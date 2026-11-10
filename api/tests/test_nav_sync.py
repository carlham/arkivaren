import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from sqlalchemy import delete, func, select

from app.models import Employer, JobAd, SyncState, active_job_ads
from app.nav.client import NavClient
from app.nav.mapping import map_ad
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


@pytest.fixture(autouse=True)
def start_without_saved_position_or_fixture_ads(db):
    """The dev database may hold a real sync. Hide it from each test.

    The delete happens inside the test's transaction, so it is rolled back afterwards.
    """
    db.execute(delete(SyncState))
    db.execute(delete(JobAd).where(JobAd.uuid.in_([NEW_AD, CHANGED_AD, UNCHANGED_AD, INACTIVE_AD])))
    db.flush()


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_client(requests: list, answers: dict | None = None) -> NavClient:
    """A client wired to the fixtures. Every request it makes is added to `requests`.

    `answers` replaces the answer for a path, with a ready httpx.Response.
    """
    answers = answers or {}
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
        if request.url.path in answers:
            return answers[request.url.path]
        name = pages.get(request.url.path) or details.get(request.url.path)
        return httpx.Response(200, json=load_fixture(name)) if name else httpx.Response(404)

    return NavClient(
        "https://feed.example.com", "token", "agent", pause_seconds=0, retry_pause_seconds=0,
        transport=httpx.MockTransport(handler),
    )


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
    changed = db.scalar(select(JobAd).where(JobAd.uuid == CHANGED_AD))
    expected = map_ad(load_fixture("ad_changed.json"))
    assert changed.title == expected["title"] != "Old title"
    assert changed.description == expected["description"]
    assert changed.source_modified_at == datetime.fromisoformat("2026-11-10T10:30:13.989601+01:00")
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


CHANGED_PATH = f"/api/v1/feedentry/{CHANGED_AD}"
NEW_PATH = f"/api/v1/feedentry/{NEW_AD}"
# What NAV answers for an ad that has become inactive: no ad_content.
INACTIVE_DETAIL = {"uuid": CHANGED_AD, "status": "INACTIVE", "sistEndret": "2026-11-10T10:31:00+01:00"}


def add_known_ads_with_text(db) -> None:
    add_known_ads(db)
    db.scalar(select(JobAd).where(JobAd.uuid == CHANGED_AD)).description = "Old text"
    db.flush()


def test_ad_that_turned_inactive_before_its_details_were_read_is_hidden(db):
    add_known_ads_with_text(db)
    client = make_client([], {CHANGED_PATH: httpx.Response(200, json=INACTIVE_DETAIL)})

    stats = sync(db, client, SINCE)

    ad = db.scalar(select(JobAd).where(JobAd.uuid == CHANGED_AD))
    assert (ad.status, ad.description) == ("inactive", None)
    assert (stats["inactive"], stats["new"]) == (1, 1)
    assert CHANGED_AD not in [a.uuid for a in db.scalars(active_job_ads())]


def test_ad_that_is_gone_at_nav_is_hidden(db):
    add_known_ads_with_text(db)
    client = make_client([], {CHANGED_PATH: httpx.Response(404)})

    stats = sync(db, client, SINCE)

    ad = db.scalar(select(JobAd).where(JobAd.uuid == CHANGED_AD))
    assert (ad.status, ad.description) == ("inactive", None)
    assert stats["inactive"] == 1


def test_unknown_ad_that_is_gone_at_nav_is_not_stored(db):
    add_known_ads(db)
    client = make_client([], {NEW_PATH: httpx.Response(404)})

    stats = sync(db, client, SINCE)

    assert db.scalar(select(JobAd).where(JobAd.uuid == NEW_AD)) is None
    assert (stats["new"], stats["changed"]) == (0, 1)


def test_inactive_ad_that_is_published_again_becomes_active_with_text(db):
    add_known_ads(db)
    ad = db.scalar(select(JobAd).where(JobAd.uuid == CHANGED_AD))
    ad.status, ad.description = "inactive", None
    db.flush()

    sync(db, make_client([]), SINCE)

    assert ad.status == "active"
    assert ad.description == map_ad(load_fixture("ad_changed.json"))["description"]
    assert CHANGED_AD in [a.uuid for a in db.scalars(active_job_ads())]


def test_server_error_stops_the_sync_and_keeps_what_was_saved(db):
    add_known_ads(db)
    requests = []
    client = make_client(requests, {CHANGED_PATH: httpx.Response(503)})

    with pytest.raises(httpx.HTTPStatusError):
        sync(db, client, SINCE)

    assert CHANGED_PATH in [r.url.path for r in requests]
    assert len([r for r in requests if r.url.path == CHANGED_PATH]) == 4  # four attempts
    assert db.scalar(select(JobAd).where(JobAd.uuid == NEW_AD)) is not None  # saved before the error
    assert db.get(SyncState, STATE_NAME) is None or db.get(SyncState, STATE_NAME).last_page_url is None


def test_nothing_changed_since_the_first_request_gives_an_empty_sync(db):
    requests = []
    client = make_client(requests, {"/api/v1/feed": httpx.Response(304)})

    stats = sync(db, client, SINCE)

    assert stats["pages"] == 0
    assert len(requests) == 1


def test_log_line_per_run_has_the_counts(db, caplog):
    add_known_ads(db)

    with caplog.at_level(logging.INFO, logger="app.nav.sync"):
        sync(db, make_client([]), SINCE)

    assert "NAV sync done: 2 pages, 1 new, 1 changed, 0 inactive, 1 unchanged" in caplog.text
