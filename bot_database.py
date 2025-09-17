"""Database module for storing bot message records."""

from datetime import datetime, timezone

import aiosqlite


class BotMessageDatabase:
    """SQLite database for storing bot message detection records."""

    def __init__(self, db_path: str = "bot_messages.db") -> None:
        self.db_path = db_path

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
                    was_deleted BOOLEAN NOT NULL DEFAULT TRUE
                )
            """)
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
    ) -> None:
        """Record a detected bot message in the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO bot_messages
                (message_id, chat_id, user_id, username, text_content,
                 spam_probability, detection_timestamp, was_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                chat_id,
                user_id,
                username,
                text_content,
                spam_probability,
                datetime.now(tz=timezone.utc),
                was_deleted,
            ))
            await db.commit()

    async def get_recent_detections(self, limit: int = 10) -> list[dict]:
        """Get recent bot message detections."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM bot_messages
                ORDER BY detection_timestamp DESC
                LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_stats(self) -> dict:
        """Get statistics about detected bot messages."""
        async with aiosqlite.connect(self.db_path) as db, db.execute("""
                SELECT
                    COUNT(*) as total_detections,
                    COUNT(CASE WHEN was_deleted = 1 THEN 1 END) as deleted_messages,
                    AVG(spam_probability) as avg_spam_probability,
                    MAX(spam_probability) as max_spam_probability
                FROM bot_messages
            """) as cursor:
            row = await cursor.fetchone()
            return {
                "total_detections": row[0] if row else 0,
                "deleted_messages": row[1] if row else 0,
                "avg_spam_probability": row[2] if row and row[2] else 0.0,
                "max_spam_probability": row[3] if row and row[3] else 0.0,
            }
