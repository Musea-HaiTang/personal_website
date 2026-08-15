import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import now_local
from app.database import Base


class FlashNote(Base):
    """闪念：一句话灵感快记，按创建时间归档，预留 user_id。"""

    __tablename__ = "flash_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local, index=True)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
