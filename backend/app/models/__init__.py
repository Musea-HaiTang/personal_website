"""SQLAlchemy 模型包（各模块的表在对应 ticket 中添加）。"""

from app.models.nav import NavCategory, NavLink

__all__ = ["NavCategory", "NavLink"]
