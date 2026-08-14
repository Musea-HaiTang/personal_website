from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import now_local
from app.database import Base


class NavCategory(Base):
    """导航分类，预留 user_id 供未来公网登录使用。"""

    __tablename__ = "nav_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    links: Mapped[list["NavLink"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="NavLink.is_pinned.desc(), NavLink.sort_order, NavLink.id",
    )


class NavLink(Base):
    """导航链接：置顶与排序字段用于控制展示顺序。"""

    __tablename__ = "nav_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("nav_categories.id"), nullable=False)
    is_pinned: Mapped[bool] = mapped_column(default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    category: Mapped[NavCategory] = relationship(back_populates="links")
