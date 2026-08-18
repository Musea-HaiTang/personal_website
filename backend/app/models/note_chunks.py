import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import now_local
from app.database import Base


class NoteChunk(Base):
    """笔记分块与 embedding 向量；正文变更时整体重建。"""

    __tablename__ = "note_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_order: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=now_local, onupdate=now_local
    )


class NoteIndexJob(Base):
    """每篇笔记一条索引状态；批量导入由后台 worker 消费。"""

    __tablename__ = "note_index_jobs"

    note_id: Mapped[int] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=now_local, onupdate=now_local
    )
