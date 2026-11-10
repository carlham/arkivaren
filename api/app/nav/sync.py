import argparse
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import Employer, JobAd, SyncState
from app.nav.client import FIRST_PAGE, NavClient
from app.nav.mapping import map_ad

logger = logging.getLogger(__name__)

STATE_NAME = "nav_feed"


def sync(db: Session, client: NavClient, since: datetime, max_pages: int | None = None) -> Counter:
    """Read the feed page by page and store new and changed ads.

    The first time, we start at `since`. After that we start at the last page we read.
    Returns counts of pages, new, changed, inactive and unchanged ads.
    """
    state = db.get(SyncState, STATE_NAME)
    if state is None:
        state = SyncState(name=STATE_NAME)
        db.add(state)

    stats = Counter()
    if state.last_page_url:
        page = client.get_page(state.last_page_url)
    else:
        page = client.get_page(FIRST_PAGE, since=since)

    while True:
        stats["pages"] += 1
        sync_page(db, client, page, stats)
        state.last_page_url = page["feed_url"]
        db.commit()
        if not page["next_url"] or (max_pages and stats["pages"] >= max_pages):
            break
        page = client.get_page(page["next_url"])

    logger.info(
        "NAV sync done: %d pages, %d new, %d changed, %d inactive, %d unchanged",
        stats["pages"], stats["new"], stats["changed"], stats["inactive"], stats["unchanged"],
    )
    return stats


def sync_page(db: Session, client: NavClient, page: dict, stats: Counter) -> None:
    # Every change is a new entry in the feed, so an ad can appear more than once. The last one counts.
    latest = {item["_feed_entry"]["uuid"]: item for item in page["items"]}
    existing = {
        ad.uuid: ad for ad in db.scalars(select(JobAd).where(JobAd.uuid.in_(latest)))
    }

    for uuid, item in latest.items():
        entry = item["_feed_entry"]
        ad = existing.get(uuid)
        modified = datetime.fromisoformat(entry["sistEndret"])

        if entry["status"] != "ACTIVE":
            if ad is not None and ad.status == "active":
                mark_inactive(ad, modified)
                stats["inactive"] += 1
        elif ad is not None and ad.status == "active" and ad.source_modified_at == modified:
            stats["unchanged"] += 1
        else:
            detail = client.get_ad(item["url"])
            if "ad_content" not in detail:
                # The ad turned inactive between the list and the details.
                if ad is not None and ad.status == "active":
                    mark_inactive(ad, modified)
                    stats["inactive"] += 1
            else:
                save_ad(db, ad, detail, modified)
                stats["changed" if ad is not None else "new"] += 1
        db.commit()


def mark_inactive(ad: JobAd, modified: datetime) -> None:
    # Hidden from results at once. The row stays for statistics, but the text is removed.
    ad.status = "inactive"
    ad.description = None
    ad.source_modified_at = modified


def save_ad(db: Session, ad: JobAd | None, detail: dict, modified: datetime) -> None:
    fields = map_ad(detail)
    employer = fields.pop("employer")
    fields["employer"] = get_or_create_employer(db, employer) if employer else None
    fields["source_modified_at"] = modified
    if ad is None:
        db.add(JobAd(**fields))
    else:
        for name, value in fields.items():
            setattr(ad, name, value)


def get_or_create_employer(db: Session, data: dict) -> Employer:
    employer = db.scalar(select(Employer).where(Employer.orgnr == data["orgnr"]))
    if employer is None:
        employer = Employer(orgnr=data["orgnr"], name=data["name"])
        db.add(employer)
    else:
        employer.name = data["name"]
    return employer


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync job ads from NAV's feed.")
    parser.add_argument(
        "--since-days", type=int, default=7,
        help="how far back the first sync starts (ignored once we have a saved position)",
    )
    parser.add_argument("--max-pages", type=int, help="stop after this many pages (for development)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    client = NavClient(settings.nav_feed_base_url, settings.nav_feed_token, settings.http_user_agent)
    since = datetime.now(timezone.utc) - timedelta(days=args.since_days)
    with SessionLocal() as db:
        sync(db, client, since, args.max_pages)


if __name__ == "__main__":
    main()
