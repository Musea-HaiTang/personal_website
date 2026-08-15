from pathlib import Path

from sqlalchemy import create_engine, inspect, text
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
    # 开发期轻量迁移：旧版 tasks 单层表（含 priority 字段）在升级后不再兼容，
    # 若检测到旧表且尚未创建新表结构，则先丢弃旧表再重建。
    with engine.connect() as conn:
        tables = set(inspect(engine).get_table_names())
        if "weekly_plans" not in tables and "tasks" in tables:
            conn.execute(text("DROP TABLE tasks"))
            conn.commit()
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
