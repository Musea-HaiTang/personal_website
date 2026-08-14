from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "personal-website"
    timezone: str = "Asia/Shanghai"
    auth_enabled: bool = False
    data_dir: Path = BASE_DIR / "data"
    database_url: str | None = None

    @model_validator(mode="after")
    def _ensure_database_url(self) -> "Settings":
        if self.database_url is None:
            self.database_url = f"sqlite:///{(self.data_dir / 'app.db').as_posix()}"
        return self


settings = Settings()

# 统一本地时区（Windows 下依赖 tzdata 提供时区数据库）
LOCAL_TZ = ZoneInfo(settings.timezone)


def now_local() -> datetime:
    return datetime.now(LOCAL_TZ)
