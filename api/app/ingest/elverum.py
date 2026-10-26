"""Henter og lagrer møtedokumenter fra Elverum kommune.

Kalles i dag av CLI-et (app.ingest.elverum_cli). Milepæl 8 kan wrappe
``run`` i et FastAPI-endepunkt (n8n -> /ingest) uten omskriving.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.elverum_innsyn import (
    ElverumClient,
    MeetingDocument,
    find_utvalg_id,
    get_meeting_documents,
    list_meetings,
)
from app.config import settings
from app.models import Document

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/elverum")


@dataclass
class IngestResult:
    meetings_checked: int
    documents_new: int
    documents_skipped: int


def _already_fetched(db: Session, external_id: str) -> bool:
    existing = db.execute(
        select(Document.id).where(Document.external_id == external_id)
    ).scalar_one_or_none()
    return existing is not None


def _save_document(db: Session, client: ElverumClient, doc: MeetingDocument) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    local_path = DATA_DIR / f"{doc.external_id.replace('/', '_')}.pdf"
    local_path.write_bytes(client.get_file(doc.file_url))

    db.add(
        Document(
            external_id=doc.external_id,
            kommune=doc.kommune,
            utvalg=doc.utvalg,
            moetedato=doc.moetedato,
            dokumenttype=doc.dokumenttype,
            tittel=doc.tittel,
            saksnummer=doc.saksnummer,
            kilde_url=doc.kilde_url,
            local_path=str(local_path),
            fetched_at=datetime.now(UTC),
        )
    )
    db.commit()


def run(
    utvalg_name: str,
    year: int,
    db: Session,
    limit: int | None = None,
    transport: httpx.BaseTransport | None = None,
) -> IngestResult:
    """Henter dokumenter for ett utvalg og ett år.

    ``limit`` begrenser antall *møter* (ikke dokumenter) vi henter detaljer
    for — brukt til å holde de første, uregulariserte kjøringene små
    (se docs/decisions.md). ``transport`` er kun til bruk i tester, for å
    unngå ekte HTTP-kall.
    """
    with ElverumClient(
        user_agent=settings.http_user_agent,
        min_request_interval_seconds=settings.min_request_interval_seconds,
        transport=transport,
    ) as client:
        utvalg_id = find_utvalg_id(client, utvalg_name)
        meetings = list_meetings(
            client,
            utvalg_id,
            from_date=date(year, 1, 1),
            to_date=date(year, 12, 31),
        )
        if limit is not None:
            meetings = meetings[:limit]

        documents_new = 0
        documents_skipped = 0
        for meeting in meetings:
            for doc in get_meeting_documents(client, meeting):
                if _already_fetched(db, doc.external_id):
                    documents_skipped += 1
                    continue
                _save_document(db, client, doc)
                documents_new += 1

        logger.info(
            "Elverum-ingest for %s %s: %s møter sjekket, %s nye dokumenter, %s allerede hentet",
            utvalg_name,
            year,
            len(meetings),
            documents_new,
            documents_skipped,
        )
        return IngestResult(
            meetings_checked=len(meetings),
            documents_new=documents_new,
            documents_skipped=documents_skipped,
        )
