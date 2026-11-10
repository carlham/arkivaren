import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import func, select

from app.models import Employer, JobAd, SyncState, active_job_ads
from app.nav.client import NavClient
from app.nav.sync import STATE_NAME, parse_args, sync

FIXTURES = Path(__file__).parent / "fixtures" / "nav"
SINCE = datetime(2026, 11, 3, tzinfo=timezone.utc)

# The four entries on feed_page_1.json.
NEW_AD = "e3187905-124a-46c8-ac20-3d94d746f363"
CHANGED_AD = "d3183152-db7c-47dd-b199-cec4915c62da"
UNCHANGED_AD = "27cb7370-5d61-4dcf-a456-49df94fc49a4"
INACTIVE_AD = "6b0c5b4f-301d-4852-b515-93b385230bf9"

PAGE_1 = "/api/v1/feed/e67e3b0c-6d45-4186-8409-0e5eec45ad9c"
PAGE_2 = "/api/v1/feed/bdee2dc9-8871-4d69-867e-f9cdfbabd93c"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_client(requests: list) -> NavClient:
    """A client wired to the fixtures. Every request it makes is added to `requests`."""
    pages = {
        "/api/v1/feed": "feed_page_1.json",
        PAGE_1: "feed_page_1.json",
        PAGE_2: "feed_page_2.json",
    }
    details = {
        f"/api/v1/feedentry/{NEW_AD}": "ad_new.json",
        f"/api/v1/feedentry/{CHANGED_AD}": "ad_changed.json",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        name = pages.get(request.url.path) or details.get(request.url.path)
        return httpx.Response(200, json=load_fixture(name)) if name else httpx.Response(404)

    return NavClient("https://feed.example.com", "token", "agent", 0, httpx.MockTransport(handler))


def detail_calls(requests: list) -> list[str]:
    return [r.url.path for r in requests if "/feedentry/" in r.url.path]


def stored_ad(uuid: str, modified: str, **fields) -> JobAd:
    return JobAd(
        uuid=uuid,
        status=fields.pop("status", "active"),
        title=fields.pop("title", "Old title"),
        source_modified_at=datetime.fromisoformat(modified),
        **fields,
    )


def add_known_ads(db) -> None:
    """The unchanged ad is stored with the same sistEndret as the feed. The changed one is older."""
    db.add_all([
        stored_ad(UNCHANGED_AD, "2026-11-10T08:36:13.287245+01:00"),
        stored_ad(CHANGED_AD, "2026-11-01T10:00:00+01:00"),
    ])
    db.flush()


def count(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_sync_adds_new_updates_changed_and_skips_the_rest(db):
    add_known_ads(db)
    requests = []

    stats = sync(db, make_client(requests), SINCE)

    assert detail_calls(requests) == [f"/api/v1/feedentry/{NEW_AD}", f"/api/v1/feedentry/{CHANGED_AD}"]
    assert (stats["new"], stats["changed"], stats["unchanged"], stats["inactive"]) == (1, 1, 1, 0)
    assert db.scalar(select(JobAd.title).where(JobAd.uuid == CHANGED_AD)) != "Old title"
    # An inactive ad we never stored stays out of the database.
    assert db.scalar(select(JobAd).where(JobAd.uuid == INACTIVE_AD)) is None


def test_syncing_the_same_feed_twice_creates_no_duplicates(db):
    add_known_ads(db)
    sync(db, make_client([]), SINCE)
    ads, employers = count(db, JobAd), count(db, Employer)

    db.delete(db.get(SyncState, STATE_NAME))  # start from the first page again
    db.flush()
    requests = []
    sync(db, make_client(requests), SINCE)

    assert (count(db, JobAd), count(db, Employer)) == (ads, employers)
    assert detail_calls(requests) == []


def test_inactive_entry_hides_the_ad_and_removes_its_text(db):
    add_known_ads(db)
    db.add(stored_ad(INACTIVE_AD, "2026-11-01T10:00:00+01:00", description="Secret text"))
    db.flush()

    stats = sync(db, make_client([]), SINCE)

    ad = db.scalar(select(JobAd).where(JobAd.uuid == INACTIVE_AD))
    assert stats["inactive"] == 1
    assert (ad.status, ad.description, ad.title) == ("inactive", None, "Old title")
    assert INACTIVE_AD not in [a.uuid for a in db.scalars(active_job_ads())]
    assert NEW_AD in [a.uuid for a in db.scalars(active_job_ads())]


def test_first_sync_starts_at_since_and_later_syncs_resume_from_last_page(db):
    add_known_ads(db)
    first = []
    sync(db, make_client(first), SINCE)
    second = []
    sync(db, make_client(second), SINCE)

    assert first[0].url.path == "/api/v1/feed"
    assert first[0].headers["If-Modified-Since"] == "Tue, 03 Nov 2026 00:00:00 GMT"
    assert db.get(SyncState, STATE_NAME).last_page_url == PAGE_2
    assert second[0].url.path == PAGE_2
    assert "If-Modified-Since" not in second[0].headers


def test_sync_stops_after_max_pages_and_continues_on_the_next_run(db):
    add_known_ads(db)
    requests = []
    sync(db, make_client(requests), SINCE, max_pages=1)

    assert db.get(SyncState, STATE_NAME).last_page_url == PAGE_1
    assert PAGE_2 not in [r.url.path for r in requests]

    sync(db, make_client(requests), SINCE)

    assert db.get(SyncState, STATE_NAME).last_page_url == PAGE_2


def test_employer_is_stored_once_per_orgnr(db):
    add_known_ads(db)
    sync(db, make_client([]), SINCE)

    employer = db.scalar(select(Employer).where(Employer.orgnr == "973635611"))
    assert employer.name == "ABB AS"
    assert db.scalar(select(JobAd.employer_id).where(JobAd.uuid == NEW_AD)) == employer.id


def test_command_line_defaults_to_seven_days_and_all_pages():
    args = parse_args([])

    assert (args.since_days, args.max_pages) == (7, None)


def test_command_line_reads_since_days_and_max_pages():
    args = parse_args(["--since-days", "2", "--max-pages", "1"])

    assert (args.since_days, args.max_pages) == (2, 1)
