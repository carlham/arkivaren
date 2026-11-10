import email.utils
import time
from datetime import datetime

import httpx

# Pause after each request, to be kind to NAV's free service.
PAUSE_SECONDS = 0.5

FIRST_PAGE = "/api/v1/feed"


class NavClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        user_agent: str,
        pause_seconds: float = PAUSE_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ):
        self.pause_seconds = pause_seconds
        self.http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}", "User-Agent": user_agent},
            timeout=30,
            transport=transport,
        )

    def get_page(self, url: str = FIRST_PAGE, since: datetime | None = None) -> dict:
        """Read one feed page. `since` (timezone-aware) is only used on the first page."""
        headers = {}
        if since is not None:
            headers["If-Modified-Since"] = email.utils.format_datetime(since, usegmt=True)
        return self._get(url, headers)

    def get_ad(self, url: str) -> dict:
        """Read the details of one feed entry, from the `url` of a feed item."""
        return self._get(url, {})

    def _get(self, url: str, headers: dict) -> dict:
        response = self.http.get(url, headers=headers)
        response.raise_for_status()
        time.sleep(self.pause_seconds)
        return response.json()
