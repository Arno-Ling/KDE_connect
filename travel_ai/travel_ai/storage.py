from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Sequence

from .models import PlaceCandidate, PreferenceProfile


@dataclass
class SqliteStore:
    db_path: Path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS preferences (
                  user_id TEXT PRIMARY KEY,
                  json TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS place_cache (
                  place_id TEXT PRIMARY KEY,
                  json TEXT NOT NULL,
                  source TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS visits (
                  user_id TEXT NOT NULL,
                  place_id TEXT NOT NULL,
                  visited_at TEXT NOT NULL,
                  PRIMARY KEY (user_id, place_id)
                )
                """
            )

    def upsert_preferences(self, profile: PreferenceProfile) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload = profile.model_dump_json()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO preferences(user_id, json, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                  json=excluded.json,
                  updated_at=excluded.updated_at
                """,
                (profile.user_id, payload, now),
            )

    def get_preferences(self, user_id: str) -> PreferenceProfile:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT json FROM preferences WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return PreferenceProfile(user_id=user_id)
        return PreferenceProfile.model_validate_json(row["json"])

    def mark_visited(self, user_id: str, place_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO visits(user_id, place_id, visited_at)
                VALUES(?, ?, ?)
                ON CONFLICT(user_id, place_id) DO UPDATE SET
                  visited_at=excluded.visited_at
                """,
                (user_id, place_id, now),
            )

    def is_visited(self, user_id: str, place_id: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM visits WHERE user_id = ? AND place_id = ?",
                (user_id, place_id),
            ).fetchone()
        return row is not None

    def cache_places(self, places: Sequence[PlaceCandidate]) -> None:
        if not places:
            return
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO place_cache(place_id, json, source, updated_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(place_id) DO UPDATE SET
                  json=excluded.json,
                  source=excluded.source,
                  updated_at=excluded.updated_at
                """,
                [
                    (p.place_id, json.dumps(p.model_dump()), p.source, now)
                    for p in places
                ],
            )

    def get_cached_place(self, place_id: str) -> Optional[PlaceCandidate]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT json FROM place_cache WHERE place_id = ?",
                (place_id,),
            ).fetchone()
        if not row:
            return None
        return PlaceCandidate.model_validate(json.loads(row["json"]))

