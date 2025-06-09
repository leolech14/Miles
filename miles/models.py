"""SQLAlchemy models for Miles bot database."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from miles.database import Base


class Promotion(Base):
    """Historical promotion tracking."""

    __tablename__ = "promotions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    program: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    bonus_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    hash_fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    user_notified_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Relationships
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="promotion"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("bonus_percentage > 0", name="positive_bonus"),
        CheckConstraint(
            "end_date IS NULL OR end_date > start_date", name="valid_date_range"
        ),
    )


class Source(Base):
    """Source management and quality tracking."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_successful_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    success_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=100.00)
    avg_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    total_checks: Mapped[int] = mapped_column(Integer, default=0)
    successful_checks: Mapped[int] = mapped_column(Integer, default=0)
    promotions_found: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[float] = mapped_column(Numeric(3, 2), default=5.0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    check_frequency_minutes: Mapped[int] = mapped_column(Integer, default=60)
    plugin_config: Mapped[Optional[dict]] = mapped_column(JSON)
    last_error_message: Mapped[Optional[str]] = mapped_column(Text)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    metrics: Mapped[List["SourceMetric"]] = relationship(
        "SourceMetric", back_populates="source"
    )


class User(Base):
    """User profiles and preferences."""

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    language_code: Mapped[str] = mapped_column(String(10), default="pt")

    # Preferences
    preferred_programs: Mapped[List[str]] = mapped_column(
        ARRAY(String), default=list, server_default="{}"
    )
    min_bonus_threshold: Mapped[int] = mapped_column(Integer, default=80)
    max_notifications_per_day: Mapped[int] = mapped_column(Integer, default=10)
    notification_hours: Mapped[List[int]] = mapped_column(
        ARRAY(Integer), default=[8, 12, 18], server_default="{8,12,18}"
    )
    timezone: Mapped[str] = mapped_column(String(50), default="America/Sao_Paulo")

    # Settings
    ai_chat_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_preferences: Mapped[dict] = mapped_column(
        JSON,
        default={
            "instant": True,
            "daily_summary": False,
            "weekly_report": True,
        },
        server_default='{"instant": true, "daily_summary": false, "weekly_report": true}',
    )

    # Activity tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    total_commands_used: Mapped[int] = mapped_column(Integer, default=0)
    total_promotions_received: Mapped[int] = mapped_column(Integer, default=0)

    # AI preferences
    preferred_ai_model: Mapped[str] = mapped_column(String(50), default="gpt-4o-mini")
    ai_temperature: Mapped[float] = mapped_column(Numeric(2, 1), default=0.7)
    ai_max_tokens: Mapped[int] = mapped_column(Integer, default=1000)

    # Relationships
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("min_bonus_threshold >= 0", name="positive_min_bonus"),
        CheckConstraint(
            "ai_temperature BETWEEN 0.0 AND 2.0", name="valid_ai_temperature"
        ),
        CheckConstraint(
            "ai_max_tokens BETWEEN 100 AND 4000", name="valid_ai_max_tokens"
        ),
    )


class Notification(Base):
    """Notification delivery tracking."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    promotion_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Notification details
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(20), default="promotion")

    # Delivery tracking
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    delivered: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    delivery_error: Mapped[Optional[str]] = mapped_column(Text)

    # User interaction
    viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    action_taken: Mapped[Optional[str]] = mapped_column(String(20))

    # Metadata
    channel: Mapped[str] = mapped_column(String(20), default="telegram")
    priority: Mapped[int] = mapped_column(Integer, default=5)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    promotion: Mapped[Optional["Promotion"]] = relationship(
        "Promotion", back_populates="notifications"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 10", name="valid_priority"),
    )


class SourceMetric(Base):
    """Source performance metrics."""

    __tablename__ = "source_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # Performance data
    check_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    content_length: Mapped[Optional[int]] = mapped_column(Integer)
    promotions_found: Mapped[int] = mapped_column(Integer, default=0)

    # Quality indicators
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    parsing_errors: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    user_agent: Mapped[Optional[str]] = mapped_column(String(200))
    plugin_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="metrics")


class BonusPrediction(Base):
    """ML predictions and training data."""

    __tablename__ = "bonus_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    program: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Prediction details
    predicted_bonus_range: Mapped[List[int]] = mapped_column(
        ARRAY(Integer), nullable=False
    )
    prediction_confidence: Mapped[float] = mapped_column(Numeric(3, 2))
    predicted_for_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    prediction_window_days: Mapped[int] = mapped_column(Integer, default=7)

    # Model information
    model_version: Mapped[Optional[str]] = mapped_column(String(20))
    model_features: Mapped[Optional[dict]] = mapped_column(JSON)

    # Verification
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actual_bonus: Mapped[Optional[int]] = mapped_column(Integer)
    actual_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    prediction_accuracy: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "prediction_confidence BETWEEN 0 AND 1", name="valid_confidence"
        ),
        UniqueConstraint(
            "program", "predicted_for_date", name="unique_program_prediction"
        ),
    )


# Helper function to create all tables
async def create_tables() -> None:
    """Create all database tables."""
    from miles.database import db_manager

    if not db_manager.engine:
        raise RuntimeError("Database not initialized")

    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Helper function to drop all tables (for testing)
async def drop_tables() -> None:
    """Drop all database tables."""
    from miles.database import db_manager

    if not db_manager.engine:
        raise RuntimeError("Database not initialized")

    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
