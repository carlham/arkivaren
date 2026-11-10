import email.utils
import logging
import time
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

# Pause after each request, to be kind to NAV's free service.
PAUSE_SECONDS = 0.5

# A request that fails with one of these (or a network error) is tried again, a bit later each time.
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4
RETRY_PAUSE_SECONDS = 5

FIRST_PAGE = "/api/v1/feed"


class NavClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        user_agent: str,
        pause_seconds: float = PAUSE_SECONDS,
        retry_pause_seconds: float = RETRY_PAUSE_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ):
        self.pause_seconds = pause_seconds
        self.retry_pause_seconds = retry_pause_seconds
        self.http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}", "User-Agent": user_agent},
            timeout=30,
            transport=transport,
        )

    def get_page(self, url: str = FIRST_PAGE, since: datetime | None = None) -> dict | None:
        """Read one feed page. `since` (timezone-aware) is only used on the first page.

        Returns None if NAV answers 304: nothing has changed since `since`.
        """
        headers = {}
        if since is not None:
            headers["If-Modified-Since"] = email.utils.format_datetime(since, usegmt=True)
        response = self._get(url, headers)
        if response.status_code == 304:
            return None
        response.raise_for_status()
        return response.json()

    def get_ad(self, url: str) -> dict:
        """Read the details of one feed entry, from the `url` of a feed item."""
        response = self._get(url, {})
        response.raise_for_status()
        return response.json()

    def _get(self, url: str, headers: dict) -> httpx.Response:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = self.http.get(url, headers=headers)
            except httpx.TransportError:
                if attempt == MAX_ATTEMPTS:
                    raise
            else:
                if response.status_code not in RETRY_STATUSES or attempt == MAX_ATTEMPTS:
                    break
            logger.warning("NAV request failed (attempt %d of %d): %s", attempt, MAX_ATTEMPTS, url)
            time.sleep(self.retry_pause_seconds * attempt)
        time.sleep(self.pause_seconds)
        return response
