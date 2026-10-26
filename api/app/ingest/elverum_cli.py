"""Kommandolinje for å hente møtedokumenter fra Elverum kommune.

Eksempel:
    docker compose exec api python -m app.ingest.elverum_cli --utvalg Kommunestyret --year 2026
"""
from __future__ import annotations

import argparse
import logging

from app.db import SessionLocal
from app.ingest.elverum import run


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--utvalg", required=True, help="Navn på utvalget, f.eks. Kommunestyret")
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help=(
            "Maks antall møter å hente (standard 5 — en håndfull, siden vi ikke har fått "
            "bekreftet tillatelse fra kommunen ennå, se docs/decisions.md)"
        ),
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = run(args.utvalg, args.year, db, limit=args.limit)
    finally:
        db.close()

    print(
        f"{result.meetings_checked} møter sjekket, "
        f"{result.documents_new} nye dokumenter, "
        f"{result.documents_skipped} allerede hentet"
    )


if __name__ == "__main__":
    main()
