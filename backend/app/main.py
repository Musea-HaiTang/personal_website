from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import dashboard, diary, flash, nav, notes, pomodoro, quiz, tasks
from app.services.indexing import index_worker


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    index_worker.start()
    yield
    index_worker.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diary.router)
app.include_router(dashboard.router)
app.include_router(flash.router)
app.include_router(nav.router)
app.include_router(notes.router)
app.include_router(pomodoro.router)
app.include_router(quiz.router)
app.include_router(tasks.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "timezone": settings.timezone,
        "auth_enabled": settings.auth_enabled,
    }
