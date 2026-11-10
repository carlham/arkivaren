from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Employer(Base):
    __tablename__ = "employer"

    id: Mapped[int] = mapped_column(primary_key=True)
    orgnr: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(255))


class JobAd(Base):
    __tablename__ = "job_ad"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True)
    # 'active' or 'inactive'. Inactive ads keep their row for statistics, but lose their text.
    status: Mapped[str] = mapped_column(String(10), index=True)
    title: Mapped[str] = mapped_column(String(500))
    # Plain text with email addresses and phone numbers removed. Emptied when the ad turns inactive.
    description: Mapped[str | None] = mapped_column(Text)
    employer_id: Mapped[int | None] = mapped_column(ForeignKey("employer.id"))
    employer: Mapped[Employer | None] = relationship()
    municipal: Mapped[str | None] = mapped_column(String(100))
    county: Mapped[str | None] = mapped_column(String(100))
    extent: Mapped[str | None] = mapped_column(String(50))
    sector: Mapped[str | None] = mapped_column(String(50))
    application_url: Mapped[str | None] = mapped_column(Text)
    # NAV's applicationDue is free text. The date is only set when the text is a date.
    application_deadline_text: Mapped[str | None] = mapped_column(Text)
    application_deadline: Mapped[date | None] = mapped_column(Date)
    # NAV's occupationCategories as delivered, for the pre-filter in milestone 3.
    occupation_categories: Mapped[list | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # sistEndret from the feed. Compared on each sync to see if the ad has changed.
    source_modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SyncState(Base):
    __tablename__ = "sync_state"

    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    # The last feed page we read. The last page has no next_url, so we remember the page itself.
    last_page_url: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
