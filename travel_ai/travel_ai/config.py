from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    env_path: Path
    amap_key: Optional[str]
    database_path: Path


def load_settings() -> Settings:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path, override=False)

    # Local SQLite DB under `travel_ai/data/`
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    database_path = data_dir / "travel_ai.sqlite3"

    import os

    amap_key = os.getenv("AMAP_KEY") or None

    return Settings(
        env_path=env_path,
        amap_key=amap_key,
        database_path=database_path,
    )

