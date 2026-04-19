import os
import logging
from typing import Optional
from datetime import datetime, timezone

import asyncpg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL – run once on startup to ensure tables exist
# ---------------------------------------------------------------------------
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id     TEXT        PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata    JSONB       NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    id              BIGSERIAL   PRIMARY KEY,
    user_id         TEXT        NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    text            TEXT        NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding_id    TEXT
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_messages_user_id          ON messages (user_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_timestamp   ON messages (user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_embedding_id     ON messages (embedding_id) WHERE embedding_id IS NOT NULL;
"""


class PostgresService:
    """
    Async PostgreSQL service backed by an asyncpg connection pool.

    Lifecycle
    ---------
    service = PostgresService()
    await service.connect()          # call once at startup
    ...
    await service.close()            # call once at shutdown

    Or use it as an async context manager:
        async with PostgresService() as svc:
            await svc.store_message(...)
    """

    def __init__(
        self,
        *,
        min_pool_size: int = 2,
        max_pool_size: int = 10,
        command_timeout: float = 30.0,
    ) -> None:
        self._pool: Optional[asyncpg.Pool] = None
        self._min_pool_size = min_pool_size
        self._max_pool_size = max_pool_size
        self._command_timeout = command_timeout

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Create the connection pool and ensure the schema exists."""
        dsn = self._build_dsn()
        logger.info("Connecting to PostgreSQL …")
        self._pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=self._min_pool_size,
            max_size=self._max_pool_size,
            command_timeout=self._command_timeout,
        )
        await self._create_tables()
        logger.info("PostgreSQL connection pool ready.")

    async def close(self) -> None:
        """Gracefully close all pool connections."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection pool closed.")

    # Async context-manager support
    async def __aenter__(self) -> "PostgresService":
        await self.connect()
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def store_message(
        self,
        user_id: str,
        text: str,
        embedding_id: Optional[str] = None,
    ) -> int:
        """
        Persist a message for *user_id*.

        Creates the user row automatically if it does not exist yet.
        Returns the auto-generated message id.
        """
        self._ensure_connected()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                # Upsert user so we never violate the FK constraint
                await conn.execute(
                    """
                    INSERT INTO users (user_id)
                    VALUES ($1)
                    ON CONFLICT (user_id) DO NOTHING
                    """,
                    user_id,
                )

                message_id: int = await conn.fetchval(
                    """
                    INSERT INTO messages (user_id, text, embedding_id)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    user_id,
                    text,
                    embedding_id,
                )

        logger.debug("Stored message id=%s for user=%s", message_id, user_id)
        return message_id

    async def get_user_messages(
        self,
        user_id: str,
        limit: int = 100,
    ) -> list[dict]:
        """
        Return the *limit* most-recent messages for *user_id*,
        ordered chronologically (oldest → newest).
        """
        self._ensure_connected()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, text, timestamp, embedding_id
                FROM (
                    SELECT id, user_id, text, timestamp, embedding_id
                    FROM   messages
                    WHERE  user_id = $1
                    ORDER  BY timestamp DESC
                    LIMIT  $2
                ) sub
                ORDER BY timestamp ASC
                """,
                user_id,
                limit,
            )
        return [_row_to_dict(r) for r in rows]

    async def get_all_messages(self, user_id: str) -> list[dict]:
        """
        Return every stored message for *user_id*, oldest → newest.
        Use with caution on high-volume users; prefer get_user_messages
        for day-to-day needs.
        """
        self._ensure_connected()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, user_id, text, timestamp, embedding_id
                FROM   messages
                WHERE  user_id = $1
                ORDER  BY timestamp ASC
                """,
                user_id,
            )
        return [_row_to_dict(r) for r in rows]

    async def get_user_metadata(self, user_id: str) -> Optional[dict]:
        """Return the metadata JSON for *user_id*, or None if unknown."""
        self._ensure_connected()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT user_id, created_at, metadata FROM users WHERE user_id = $1",
                user_id,
            )
        if row is None:
            return None
        return dict(row)

    async def update_user_metadata(self, user_id: str, metadata: dict) -> None:
        """
        Merge *metadata* into the existing JSONB blob for *user_id*.
        Creates the user row if it does not exist.
        """
        self._ensure_connected()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, metadata)
                VALUES ($1, $2::jsonb)
                ON CONFLICT (user_id)
                DO UPDATE SET metadata = users.metadata || EXCLUDED.metadata
                """,
                user_id,
                metadata,
            )

    async def delete_user(self, user_id: str) -> None:
        """
        Hard-delete a user and all their messages (CASCADE).
        Irreversible – use carefully.
        """
        self._ensure_connected()
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)
        logger.info("Deleted user=%s and all their messages.", user_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_dsn() -> str:
        """Build a libpq-style DSN from environment variables."""
        host     = os.getenv("POSTGRES_HOST", "localhost")
        port     = os.getenv("POSTGRES_PORT", "5432")
        user     = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        database = os.getenv("POSTGRES_DB", "postgres")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def _ensure_connected(self) -> None:
        if self._pool is None:
            raise RuntimeError(
                "PostgresService is not connected. Call `await service.connect()` first."
            )

    async def _create_tables(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_TABLES_SQL)
        logger.debug("Schema verified / created.")


# ---------------------------------------------------------------------------
# Row helper
# ---------------------------------------------------------------------------

def _row_to_dict(row: asyncpg.Record) -> dict:
    """Convert an asyncpg Record to a plain dict with serialisable values."""
    d = dict(row)
    # Ensure timestamps are UTC-aware ISO strings for easy JSON serialisation
    for key, value in d.items():
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            d[key] = value.isoformat()
    return d
