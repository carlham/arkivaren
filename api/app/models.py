from datetime import date, datetime

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Document(Base):
    """Et møtedokument, i det felles formatet beskrevet i CLAUDE.md."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    kommune: Mapped[str] = mapped_column(String)
    utvalg: Mapped[str] = mapped_column(String)
    moetedato: Mapped[date] = mapped_column(Date)
    dokumenttype: Mapped[str] = mapped_column(String)
    tittel: Mapped[str] = mapped_column(String)
    saksnummer: Mapped[str | None] = mapped_column(String, nullable=True)
    kilde_url: Mapped[str] = mapped_column(String)
    local_path: Mapped[str] = mapped_column(String)
    fetched_at: Mapped[datetime] = mapped_column(DateTime)
