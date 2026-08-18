import queue
import threading
import time
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.note_chunks import NoteChunk, NoteIndexJob
from app.models.notes import Note
from app.schemas.notes import IndexProgress
from app.services.chunker import chunk_markdown
from app.services.embeddings import embed_texts
from app.services.markdown_store import notes_store

PENDING = "pending"
RUNNING = "running"
RETRYING = "retrying"
DONE = "done"
FAILED = "failed"
_ACTIVE_STATUSES = (PENDING, RUNNING, RETRYING)


def rebuild_note_index(db: Session, note_id: int) -> None:
    """重建一篇笔记的分块与向量；失败自动重试，重试耗尽后标记 failed。"""
    note = db.get(Note, note_id)
    if note is None:
        return
    content = notes_store.read(Path(note.file_path))
    chunks = chunk_markdown(content)
    payloads = [
        f"{chunk.heading}\n{chunk.content}" if chunk.heading else chunk.content
        for chunk in chunks
    ]
    max_attempts = settings.embedding_retries + 1

    for attempt in range(1, max_attempts + 1):
        job = _ensure_job(db, note_id)
        job.status = RUNNING
        job.attempts = attempt
        job.error = None
        db.commit()
        try:
            vectors = embed_texts(payloads) if payloads else []
            db.execute(delete(NoteChunk).where(NoteChunk.note_id == note_id))
            for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
                db.add(
                    NoteChunk(
                        note_id=note_id,
                        chunk_order=index,
                        heading=chunk.heading or None,
                        content=chunk.content,
                        embedding=vector,
                    )
                )
            job = _ensure_job(db, note_id)
            job.status = DONE
            job.error = None
            db.commit()
            return
        except Exception as exc:
            db.rollback()
            job = _ensure_job(db, note_id)
            job.status = RETRYING if attempt < max_attempts else FAILED
            job.attempts = attempt
            job.error = str(exc)[:500]
            db.commit()
            if attempt < max_attempts:
                time.sleep(min(0.1 * attempt, 1.0))


def delete_note_index(db: Session, note_id: int) -> None:
    db.execute(delete(NoteChunk).where(NoteChunk.note_id == note_id))
    job = db.get(NoteIndexJob, note_id)
    if job is not None:
        db.delete(job)


def index_progress(db: Session) -> IndexProgress:
    total = db.scalar(select(func.count(Note.id))) or 0
    chunk_count = db.scalar(
        select(func.count(NoteChunk.id)).where(NoteChunk.embedding.is_not(None))
    ) or 0
    jobs = db.scalars(select(NoteIndexJob)).all()
    done = sum(job.status == DONE for job in jobs)
    pending = sum(job.status in _ACTIVE_STATUSES for job in jobs)
    failed = sum(job.status == FAILED for job in jobs)
    return IndexProgress(
        total=total,
        done=done,
        chunk_count=chunk_count,
        pending=pending,
        failed=failed,
        running=pending > 0,
    )


def queue_import_notes(note_ids: list[int]) -> None:
    if not note_ids:
        return
    with SessionLocal() as db:
        for note_id in note_ids:
            job = db.get(NoteIndexJob, note_id)
            if job is None:
                job = NoteIndexJob(note_id=note_id, status=PENDING)
                db.add(job)
            else:
                job.status = PENDING
                job.attempts = 0
                job.error = None
        db.commit()
    for note_id in note_ids:
        index_worker.enqueue(note_id)


class NoteIndexWorker:
    def __init__(self) -> None:
        self._queue: queue.Queue[int | None] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._run, name="note-index-worker", daemon=True)
            self._thread.start()
            try:
                with SessionLocal() as db:
                    note_ids = db.scalars(
                        select(NoteIndexJob.note_id).where(NoteIndexJob.status.in_(_ACTIVE_STATUSES))
                    ).all()
            except Exception:
                note_ids = []
        for note_id in note_ids:
            self._queue.put(note_id)

    def stop(self) -> None:
        self._queue.put(None)
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2)

    def enqueue(self, note_id: int) -> None:
        self._queue.put(note_id)
        self.start()

    def _run(self) -> None:
        while True:
            note_id = self._queue.get()
            if note_id is None:
                return
            try:
                with SessionLocal() as db:
                    rebuild_note_index(db, note_id)
            except Exception:
                # rebuild_note_index 已处理业务异常；这里只保证 worker 不因意外退出。
                pass


def _ensure_job(db: Session, note_id: int) -> NoteIndexJob:
    job = db.get(NoteIndexJob, note_id)
    if job is None:
        job = NoteIndexJob(note_id=note_id, status=PENDING)
        db.add(job)
        db.flush()
    return job


index_worker = NoteIndexWorker()
