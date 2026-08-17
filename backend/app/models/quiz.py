import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import now_local
from app.database import Base


class Question(Base):
    """技术答题题目；type 为 choice（选择题）或 fill（填空题）。"""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    no: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # choice / fill
    title: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[str] = mapped_column(String(2000), default="[]", nullable=False)  # JSON 列表（choice）
    accept: Mapped[str] = mapped_column(String(500), default="[]", nullable=False)  # JSON 列表（fill 可接受答案）
    answer: Mapped[str] = mapped_column(String(500), nullable=False)  # choice: A/B/C/D；fill: 文本
    code: Mapped[str | None] = mapped_column(Text, nullable=True)  # fill：含 ____ 的代码
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
