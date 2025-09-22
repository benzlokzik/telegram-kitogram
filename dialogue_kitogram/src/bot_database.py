"""Database module for storing bot message records."""

from datetime import UTC, datetime

import aiosqlite

from .config import get_db_path


class BotMessageDatabase:
    """SQLite database for storing bot message detection records."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or get_db_path()

    async def init_database(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER,
                    username TEXT,
                    text_content TEXT,
                    spam_probability REAL NOT NULL,
                    detection_timestamp DATETIME NOT NULL,
                    was_deleted BOOLEAN NOT NULL DEFAULT TRUE,
                    was_manual BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS allowed_chats (
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT,
                    added_by_admin_id INTEGER,
                    added_at DATETIME NOT NULL
                )
            """)
            await db.commit()

            # Ensure migration: add was_manual column if missing in existing DBs
            async with db.execute("PRAGMA table_info(bot_messages)") as cursor:
                columns = await cursor.fetchall()
                column_names = {row[1] for row in columns}
            if "was_manual" not in column_names:
                await db.execute(
                    "ALTER TABLE bot_messages ADD COLUMN was_manual BOOLEAN NOT NULL DEFAULT 0",
                )
                await db.commit()

    async def record_bot_message(
        self,
        *,
        message_id: int,
        chat_id: int,
        user_id: int | None,
        username: str | None,
        text_content: str,
        spam_probability: float,
        was_deleted: bool = True,
        was_manual: bool = False,
    ) -> None:
        """Record a detected bot message in the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO bot_messages
                (message_id, chat_id, user_id, username, text_content,
                 spam_probability, detection_timestamp, was_deleted, was_manual)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    message_id,
                    chat_id,
                    user_id,
                    username,
                    text_content,
                    spam_probability,
                    datetime.now(tz=UTC),
                    was_deleted,
                    1 if was_manual else 0,
                ),
            )
            await db.commit()

    async def get_recent_detections(self, limit: int = 10) -> list[dict]:
        """Get recent bot message detections."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM bot_messages
                ORDER BY detection_timestamp DESC
                LIMIT ?
            """,
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_stats(self) -> dict:
        """Get statistics about detected bot messages."""
        async with (
            aiosqlite.connect(self.db_path) as db,
            db.execute("""
                SELECT
                    COUNT(*) as total_detections,
                    COUNT(CASE WHEN was_deleted = 1 THEN 1 END) as deleted_messages,
                    AVG(spam_probability) as avg_spam_probability,
                    MAX(spam_probability) as max_spam_probability
                FROM bot_messages
                WHERE was_manual = 0
            """) as cursor,
        ):
            row = await cursor.fetchone()
            return {
                "total_detections": row[0] if row else 0,
                "deleted_messages": row[1] if row else 0,
                "avg_spam_probability": row[2] if row and row[2] else 0.0,
                "max_spam_probability": row[3] if row and row[3] else 0.0,
            }

    async def add_allowed_chat(
        self,
        *,
        chat_id: int,
        title: str | None,
        added_by_admin_id: int,
    ) -> None:
        """Add or update an allowed chat entry."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO allowed_chats (chat_id, title, added_by_admin_id, added_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    title=excluded.title,
                    added_by_admin_id=excluded.added_by_admin_id,
                    added_at=excluded.added_at
                """,
                (chat_id, title, added_by_admin_id, datetime.now(tz=UTC)),
            )
            await db.commit()

    async def remove_allowed_chat(self, chat_id: int) -> bool:
        """Remove an allowed chat. Returns True if a row was deleted."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM allowed_chats WHERE chat_id = ?",
                (chat_id,),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def is_chat_allowed(self, chat_id: int) -> bool:
        """Check if a chat is in the allowed list."""
        async with (
            aiosqlite.connect(self.db_path) as db,
            db.execute(
                "SELECT 1 FROM allowed_chats WHERE chat_id = ? LIMIT 1",
                (chat_id,),
            ) as cursor,
        ):
            row = await cursor.fetchone()
            return row is not None

    async def list_allowed_chats(self) -> list[dict]:
        """List all allowed chats."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT chat_id, title, added_by_admin_id, added_at
                FROM allowed_chats
                ORDER BY added_at DESC
                """,
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
