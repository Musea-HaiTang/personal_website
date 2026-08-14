import datetime

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import now_local
from app.database import Base


class DiaryEntry(Base):
    """日记元数据；正文以 YYYY-MM-DD.md 文件保存，预留 user_id。"""

    __tablename__ = "diary_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    tags: Mapped[str] = mapped_column(String(500), default="", nullable=False)  # 逗号分隔
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
