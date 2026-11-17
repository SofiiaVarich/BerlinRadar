"""SQLite repositories for events, preferences, and notification history."""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Iterator, Sequence

from database.models import Event, UserPreferences


class Repository:
    def __init__(self, database_path: Path | str) -> None:
        self.path = str(database_path)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    async def initialize(self) -> None:
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(self._initialize)

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT,
                    title TEXT NOT NULL,
                    starts_at TEXT NOT NULL,
                    location TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    categories TEXT NOT NULL DEFAULT '[]',
                    price REAL,
                    currency TEXT NOT NULL DEFAULT 'EUR',
                    fingerprint TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    UNIQUE(source, external_id)
                );
                CREATE INDEX IF NOT EXISTS events_starts_at ON events(starts_at);
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    categories TEXT NOT NULL DEFAULT '[]',
                    free_only INTEGER NOT NULL DEFAULT 0,
                    subscribed INTEGER NOT NULL DEFAULT 0,
                    timezone TEXT NOT NULL DEFAULT 'Europe/Berlin'
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    telegram_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL,
                    sent_at TEXT NOT NULL,
                    PRIMARY KEY (telegram_id, event_id),
                    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
                );
            """)

    async def upsert_events(self, events: Sequence[Event]) -> int:
        return await asyncio.to_thread(self._upsert_events, events)

    def _upsert_events(self, events: Sequence[Event]) -> int:
        changed = 0
        insert_sql = """INSERT INTO events
            (external_id,title,starts_at,location,url,source,description,categories,price,currency,fingerprint,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(fingerprint) DO UPDATE SET
              external_id=excluded.external_id, title=excluded.title, starts_at=excluded.starts_at,
              location=excluded.location, url=excluded.url, description=excluded.description,
              categories=excluded.categories, price=excluded.price, currency=excluded.currency"""
        update_sql = """UPDATE events SET title=?, starts_at=?, location=?, url=?, description=?, categories=?,
            price=?, currency=?, fingerprint=? WHERE source=? AND external_id=?"""
        with self._connect() as db:
            for event in events:
                before = db.total_changes
                values = (event.external_id, event.title, event.starts_at.isoformat(), event.location,
                    event.url, event.source, event.description, json.dumps(event.categories), event.price,
                    event.currency, event.fingerprint, event.created_at.isoformat())
                if event.external_id:
                    db.execute(update_sql, (event.title, event.starts_at.isoformat(), event.location, event.url,
                        event.description, json.dumps(event.categories), event.price, event.currency,
                        event.fingerprint, event.source, event.external_id))
                if db.total_changes == before:
                    db.execute(insert_sql, values)
                changed += db.total_changes - before
        return changed

    async def list_events(self, start: datetime, end: datetime, limit: int = 20) -> list[Event]:
        return await asyncio.to_thread(self._list_events, start, end, limit)

    def _list_events(self, start: datetime, end: datetime, limit: int) -> list[Event]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM events WHERE starts_at >= ? AND starts_at < ? ORDER BY starts_at LIMIT ?",
                              (start.isoformat(), end.isoformat(), limit)).fetchall()
        return [self._event(row) for row in rows]

    async def prune_source(self, source: str, external_ids: set[str]) -> None:
        await asyncio.to_thread(self._prune_source, source, external_ids)

    def _prune_source(self, source: str, external_ids: set[str]) -> None:
        with self._connect() as db:
            if external_ids:
                placeholders = ",".join("?" for _ in external_ids)
                db.execute(
                    f"DELETE FROM events WHERE source = ? AND external_id NOT IN ({placeholders})",
                    (source, *sorted(external_ids)),
                )
            else:
                db.execute("DELETE FROM events WHERE source = ?", (source,))

    async def delete_expired(self, before: datetime) -> None:
        await asyncio.to_thread(self._delete_expired, before)

    def _delete_expired(self, before: datetime) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM events WHERE starts_at < ?", (before.astimezone(timezone.utc).isoformat(),))

    async def ensure_user(self, telegram_id: int) -> None:
        await asyncio.to_thread(self._ensure_user, telegram_id)

    def _ensure_user(self, telegram_id: int) -> None:
        with self._connect() as db:
            db.execute("INSERT OR IGNORE INTO users(telegram_id) VALUES (?)", (telegram_id,))

    async def get_preferences(self, telegram_id: int) -> UserPreferences:
        await self.ensure_user(telegram_id)
        return await asyncio.to_thread(self._get_preferences, telegram_id)

    def _get_preferences(self, telegram_id: int) -> UserPreferences:
        with self._connect() as db:
            row = db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        return UserPreferences(row["telegram_id"], json.loads(row["categories"]), bool(row["free_only"]),
                               bool(row["subscribed"]), row["timezone"])

    async def update_preferences(self, preferences: UserPreferences) -> None:
        await asyncio.to_thread(self._update_preferences, preferences)

    def _update_preferences(self, p: UserPreferences) -> None:
        with self._connect() as db:
            db.execute("""INSERT INTO users(telegram_id,categories,free_only,subscribed,timezone) VALUES (?,?,?,?,?)
                ON CONFLICT(telegram_id) DO UPDATE SET categories=excluded.categories, free_only=excluded.free_only,
                subscribed=excluded.subscribed, timezone=excluded.timezone""",
                (p.telegram_id, json.dumps(p.categories), int(p.free_only), int(p.subscribed), p.timezone))

    async def delete_user(self, telegram_id: int) -> None:
        await asyncio.to_thread(self._delete_user, telegram_id)

    def _delete_user(self, telegram_id: int) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM notifications WHERE telegram_id = ?", (telegram_id,))
            db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))

    async def subscribed_users(self) -> list[UserPreferences]:
        return await asyncio.to_thread(self._subscribed_users)

    def _subscribed_users(self) -> list[UserPreferences]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM users WHERE subscribed = 1").fetchall()
        return [UserPreferences(r["telegram_id"], json.loads(r["categories"]), bool(r["free_only"]), True, r["timezone"]) for r in rows]

    async def unsent(self, telegram_id: int, events: Sequence[Event]) -> list[Event]:
        ids = [e.id for e in events if e.id is not None]
        if not ids:
            return []
        return await asyncio.to_thread(self._unsent, telegram_id, events, ids)

    def _unsent(self, telegram_id: int, events: Sequence[Event], ids: list[int]) -> list[Event]:
        placeholders = ",".join("?" for _ in ids)
        with self._connect() as db:
            sent = {r[0] for r in db.execute(
                f"SELECT event_id FROM notifications WHERE telegram_id=? AND event_id IN ({placeholders})",
                (telegram_id, *ids)).fetchall()}
        return [e for e in events if e.id not in sent]

    async def mark_sent(self, telegram_id: int, event_id: int) -> None:
        await asyncio.to_thread(self._mark_sent, telegram_id, event_id)

    def _mark_sent(self, telegram_id: int, event_id: int) -> None:
        with self._connect() as db:
            db.execute("INSERT OR IGNORE INTO notifications VALUES (?,?,?)",
                       (telegram_id, event_id, datetime.now(timezone.utc).isoformat()))

    @staticmethod
    def _event(row: sqlite3.Row) -> Event:
        return Event(id=row["id"], external_id=row["external_id"], title=row["title"],
            starts_at=datetime.fromisoformat(row["starts_at"]), location=row["location"], url=row["url"],
            source=row["source"], description=row["description"], categories=json.loads(row["categories"]),
            price=row["price"], currency=row["currency"], created_at=datetime.fromisoformat(row["created_at"]))
