from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """确保数据目录存在并初始化 SQLite。"""
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # 真正执行一次查询，确保 SQLite 数据库文件落盘
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
