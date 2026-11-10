import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.nav.client import NavClient

FIXTURES = Path(__file__).parent / "fixtures" / "nav"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_client(requests: list) -> NavClient:
    """A client wired to the fixtures. Every request it makes is added to `requests`."""

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v1/feed":
            return httpx.Response(200, json=load_fixture("feed_page_1.json"))
        if request.url.path.startswith("/api/v1/feedentry/"):
            return httpx.Response(200, json=load_fixture("ad_new.json"))
        return httpx.Response(404)

    return NavClient(
        base_url="https://feed.example.com",
        token="test-token",
        user_agent="test-agent",
        pause_seconds=0,
        transport=httpx.MockTransport(handler),
    )


def test_client_sends_token_and_user_agent():
    requests = []

    make_client(requests).get_page()

    assert requests[0].headers["Authorization"] == "Bearer test-token"
    assert requests[0].headers["User-Agent"] == "test-agent"


def test_client_reads_feed_page_and_ad_details():
    client = make_client([])

    page = client.get_page()
    ad = client.get_ad(page["items"][0]["url"])

    assert len(page["items"]) == 4
    assert ad["ad_content"]["title"] == page["items"][0]["title"]


def test_client_sends_if_modified_since_only_when_asked():
    requests = []
    client = make_client(requests)

    client.get_page()
    client.get_page(since=datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc))

    assert "If-Modified-Since" not in requests[0].headers
    assert requests[1].headers["If-Modified-Since"] == "Tue, 03 Nov 2026 12:00:00 GMT"


def test_client_raises_on_error_response():
    with pytest.raises(httpx.HTTPStatusError):
        make_client([]).get_ad("/api/v1/does-not-exist")
