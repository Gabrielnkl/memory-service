# postgres_sqlalchemy.py

import os
import logging
from typing import Optional, List
from datetime import datetime

from dotenv import load_dotenv

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    DateTime,
    func,
    select,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DATABASE CONFIG
# ---------------------------------------------------------------------------

def get_database_url() -> str:
    return (
        f"postgresql+asyncpg://"
        f"{os.getenv('POSTGRES_USER', 'postgres')}:"
        f"{os.getenv('POSTGRES_PASSWORD', '')}@"
        f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB', 'postgres')}"
    )


# ---------------------------------------------------------------------------
# BASE MODEL
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # ⚠️ FIX: rename attribute, keep DB column as "metadata"
    user_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
    )

    messages: Mapped[List["Message"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE")
    )

    text: Mapped[str] = mapped_column(Text)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    embedding_id: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="messages")


# ---------------------------------------------------------------------------
# INDEXES
# ---------------------------------------------------------------------------

Index("idx_messages_user_id", Message.user_id)
Index("idx_messages_user_timestamp", Message.user_id, Message.timestamp.desc())
Index("idx_messages_embedding_id", Message.embedding_id)


# ---------------------------------------------------------------------------
# SERVICE
# ---------------------------------------------------------------------------

class PostgresService:
    def __init__(self):
        self.engine = create_async_engine(
            get_database_url(),
            echo=False,
            pool_size=10,
            max_overflow=20,
        )

        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    # --------------------------------------------------------------
    # Setup
    # --------------------------------------------------------------

    async def connect(self):
        """Create tables (like your DDL)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database connected and tables created.")

    async def close(self):
        await self.engine.dispose()

    # --------------------------------------------------------------
    # Core Methods
    # --------------------------------------------------------------

    async def store_message(
        self,
        user_id: str,
        text: str,
        embedding_id: Optional[str] = None,
    ) -> int:
        async with self.SessionLocal() as session:
            async with session.begin():

                # Get or create user
                user = await session.get(User, user_id)
                if not user:
                    user = User(user_id=user_id)
                    session.add(user)

                message = Message(
                    user_id=user_id,
                    text=text,
                    embedding_id=embedding_id,
                )

                session.add(message)

            await session.commit()
            await session.refresh(message)

            logger.debug("Stored message id=%s for user=%s", message.id, user_id)

            return message.id

    async def get_user_messages(
        self,
        user_id: str,
        limit: int = 100,
    ) -> list[dict]:
        async with self.SessionLocal() as session:

            stmt = (
                select(Message)
                .where(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(limit)
            )

            result = await session.execute(stmt)
            messages = list(result.scalars())

            # Return chronological order (oldest → newest)
            messages.reverse()

            return [self._to_dict(m) for m in messages]

    async def get_all_messages(self, user_id: str) -> list[dict]:
        async with self.SessionLocal() as session:

            stmt = (
                select(Message)
                .where(Message.user_id == user_id)
                .order_by(Message.timestamp.asc())
            )

            result = await session.execute(stmt)
            messages = list(result.scalars())

            return [self._to_dict(m) for m in messages]

    async def get_user_metadata(self, user_id: str) -> Optional[dict]:
        async with self.SessionLocal() as session:

            user = await session.get(User, user_id)

            if not user:
                return None

            return {
                "user_id": user.user_id,
                "created_at": user.created_at.isoformat(),
                "metadata": user.user_metadata,  # keep API consistent
            }

    async def update_user_metadata(self, user_id: str, metadata: dict):
        async with self.SessionLocal() as session:
            async with session.begin():

                user = await session.get(User, user_id)

                if not user:
                    user = User(
                        user_id=user_id,
                        user_metadata=metadata,
                    )
                    session.add(user)
                else:
                    user.user_metadata = {
                        **(user.user_metadata or {}),
                        **metadata,
                    }

    async def delete_user(self, user_id: str):
        async with self.SessionLocal() as session:
            async with session.begin():

                user = await session.get(User, user_id)

                if user:
                    await session.delete(user)

        logger.info("Deleted user=%s and all messages.", user_id)

    # --------------------------------------------------------------
    # Helper
    # --------------------------------------------------------------

    def _to_dict(self, message: Message) -> dict:
        return {
            "id": message.id,
            "user_id": message.user_id,
            "text": message.text,
            "timestamp": message.timestamp.isoformat(),
            "embedding_id": message.embedding_id,
        }
