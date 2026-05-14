from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.app.model.entity.base_entity import BaseEntity


class Vocalization(BaseEntity):
    __tablename__ = "vocalizations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    speaker: Mapped[str] = mapped_column(
        Text,
    )
    record_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    location: Mapped[str] = mapped_column(
        Text,
    )
    vocalization: Mapped[str] = mapped_column(
        Text,
    )
    audio_file: Mapped[str] = mapped_column(
        Text,
    )
    audio_number: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    segment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    validated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
