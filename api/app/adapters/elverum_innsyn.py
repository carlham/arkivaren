"""Klient og parsing for Elverum kommunes offentlige innsyn-API.

Se docs/decisions.md for:
- hvorfor dette API-et (/api/presentation/v2/nye-innsyn/...) er lov å bruke
  selv om robots.txt blokkerer de gamle /innsyn-sidene,
- betingelsene vi har satt oss selv (rate-limit, User-Agent, dedup, osv.), og
- det verifiserte JSON-skjemaet denne modulen bygger på.

Alle ID-er (møte-ID, sak-ID, fil-URL, utvalg-ID) kommer fra API-svarene selv.
Ingenting konstrueres eller gjettes lokalt.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime

import httpx

BASE_URL = "https://www.elverum.kommune.no"
API_PATH = "/api/presentation/v2/nye-innsyn"
SESSION_PAGE_PATH = "/vare-tjenester/politikk-planer-og-organisasjon/politikk/politisk-moteplan/"

DATASOURCE_CURRENT = "585964d3-63d8-44c9-9f12-de294f9152c7"  # "Arkiv fra april 2024"

_FILE_KEY_TO_DOKUMENTTYPE = {
    "MEETING_FILES_SUMMON": "innkalling",
    "MEETING_FILES_PROTOCOL": "protokoll",
}


@dataclass
class Utvalg:
    id: str
    name: str


@dataclass
class MeetingRef:
    id: str
    utvalg: str
    moetedato: date
    sted: str


@dataclass
class MeetingDocument:
    """Et møtedokument i CLAUDE.md sitt felles format, pluss URL-en vi laster PDF-en fra."""

    external_id: str
    kommune: str
    utvalg: str
    moetedato: date
    dokumenttype: str
    tittel: str
    saksnummer: str | None
    kilde_url: str
    file_url: str


class ElverumClient:
    """Tynn, høflig klient mot Elverum kommunes offentlige innsyn-API.

    Rate-limiter venter minst ``min_request_interval_seconds`` mellom
    *alle* kall (både JSON-oppslag og fil-nedlasting), slik at vi aldri
    overstiger grensen uavhengig av hvilken metode som brukes.
    """

    def __init__(
        self,
        user_agent: str,
        min_request_interval_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ):
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={"User-Agent": user_agent},
            timeout=30.0,
            transport=transport,
        )
        self._min_interval = min_request_interval_seconds
        self._last_request_at: float | None = None
        self._session_established = False

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ElverumClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _wait_for_rate_limit(self) -> None:
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            remaining = self._min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def _ensure_session(self) -> None:
        """API-et avviser (og kobler fra) kall uten en sesjon-cookie fra et
        vanlig sidebesøk — nettleseren har alltid lastet HTML-siden først.
        Besøker møteplan-siden én gang per klient for å få samme cookie
        (se docs/decisions.md)."""
        if self._session_established:
            return
        self._wait_for_rate_limit()
        response = self._client.get(SESSION_PAGE_PATH)
        response.raise_for_status()
        self._session_established = True

    def _post(self, path: str, key_values: list[tuple[str, str]]) -> dict:
        """``path`` må starte med "/" og inkludere ev. ekstra skråstreker vi
        har verifisert at API-et faktisk bruker (se docs/decisions.md)."""
        self._ensure_session()
        self._wait_for_rate_limit()
        body = {"type": 1, "keyValues": [{"key": k, "value": v} for k, v in key_values]}
        response = self._client.post(f"{API_PATH}{path}", json=body)
        response.raise_for_status()
        return response.json()

    def get_file(self, file_url: str) -> bytes:
        self._ensure_session()
        self._wait_for_rate_limit()
        response = self._client.get(file_url)
        response.raise_for_status()
        return response.content


def _parse_dato(value: str) -> date:
    return datetime.strptime(value, "%d.%m.%Y").date()


def _kilde_url(meeting_id: str) -> str:
    return (
        "https://www.elverum.kommune.no/vare-tjenester/politikk-planer-og-organisasjon/"
        f"politikk/politisk-moteplan/#/details/{meeting_id}"
    )


def _find_child(node: dict, key: str) -> dict | None:
    return next((child for child in node.get("b", []) if child.get("key") == key), None)


def _case_property(case: dict, title: str) -> str | None:
    property_list = next((c for c in case.get("b", []) if c.get("type") == "PropertyList"), None)
    if property_list is None:
        return None
    prop = next((p for p in property_list.get("b", []) if p.get("title") == title), None)
    return prop["text"] if prop else None


def list_utvalg(client: ElverumClient, datasource: str = DATASOURCE_CURRENT) -> list[Utvalg]:
    """Henter hele utvalgslisten dynamisk fra API-ets filter-metadata.

    Vi gjetter eller hardkoder aldri UtvalgID — den henger på en skjult
    hash-signatur (``!<hash>``) vi ikke kan konstruere selv.
    """
    data = client._post(
        "/overview",
        [
            ("Datasource", datasource),
            ("Dato", "1900-01-01"),
            ("Dato", date.today().isoformat()),
            ("Dato", "Other"),
            ("page", "1"),
            ("pageSize", "1"),
        ],
    )
    filters = data["content"]["searchOptions"]["searchFilters"]
    utvalg_filter = next(f for f in filters if f["identifier"] == "UtvalgID")
    return [Utvalg(id=f["identifier"], name=f["name"]) for f in utvalg_filter["fields"]]


def find_utvalg_id(client: ElverumClient, name: str, datasource: str = DATASOURCE_CURRENT) -> str:
    for utvalg in list_utvalg(client, datasource):
        if utvalg.name.strip().lower() == name.strip().lower():
            return utvalg.id
    raise ValueError(f"Fant ikke utvalget «{name}» hos Elverum kommune")


def list_meetings(
    client: ElverumClient,
    utvalg_id: str,
    from_date: date,
    to_date: date,
    datasource: str = DATASOURCE_CURRENT,
) -> list[MeetingRef]:
    """Henter alle møter for ett utvalg i en periode, med paginering.

    API-et har vist seg å ikke respektere en liten ``pageSize`` (det
    returnerer likevel 10 treff), så vi ber om en stor side og looper på
    ``page`` basert på hvor mange elementer *responsen* faktisk ga.
    """
    meetings: list[MeetingRef] = []
    page = 1
    while True:
        data = client._post(
            "/overview",
            [
                ("Datasource", datasource),
                ("UtvalgID", utvalg_id),
                ("Dato", from_date.isoformat()),
                ("Dato", to_date.isoformat()),
                ("Dato", "Other"),
                ("page", str(page)),
                ("pageSize", "100"),
            ],
        )
        search_items = data["content"]["searchItems"]
        items = search_items["items"]
        for item in items:
            props = item["properties"]
            meetings.append(
                MeetingRef(
                    id=item["identifier"],
                    utvalg=item["title"],
                    moetedato=_parse_dato(props["dato"]),
                    sted=props.get("sted", ""),
                )
            )
        if len(items) < search_items["pageSize"]:
            break
        page += 1
    return meetings


def get_case_documents(client: ElverumClient, case_id: str) -> list[dict]:
    """Saksframlegg-dokumenter for én sak. Returnerer rå fil-noder (identifier/title/url)."""
    data = client._post(f"/mote/saksfremlegg/{case_id}", [])
    files_node = _find_child(data["content"], "MEETING_CASE_FILES")
    if files_node is None:
        return []
    return [f for f in files_node.get("b", []) if f.get("url")]


def get_meeting_documents(client: ElverumClient, meeting: MeetingRef) -> list[MeetingDocument]:
    """Alle dokumenter for ett møte: møtedokumenter (innkalling/protokoll/møtebok)
    og saksframlegg for saker som har dokumenter."""
    data = client._post(f"//mote/{meeting.id}", [])
    content = data["content"]
    kilde_url = _kilde_url(meeting.id)
    documents: list[MeetingDocument] = []

    files_node = _find_child(content, "MEETING_FILES")
    for file_entry in (files_node.get("b", []) if files_node else []):
        url = file_entry.get("url")
        if not url:
            continue  # "ikke publisert enda"
        dokumenttype = _FILE_KEY_TO_DOKUMENTTYPE.get(file_entry.get("key"), "møtebok")
        documents.append(
            MeetingDocument(
                external_id=file_entry["identifier"],
                kommune="Elverum",
                utvalg=meeting.utvalg,
                moetedato=meeting.moetedato,
                dokumenttype=dokumenttype,
                tittel=file_entry["title"],
                saksnummer=None,
                kilde_url=kilde_url,
                file_url=url,
            )
        )

    cases_node = _find_child(content, "MEETING_CASES")
    for case in (cases_node.get("b", []) if cases_node else []):
        antall_dokumenter_text = _case_property(case, "Antall dokumenter")
        if not antall_dokumenter_text or int(antall_dokumenter_text) < 1:
            continue
        saksnummer = _case_property(case, "Saksnummer")
        for case_file in get_case_documents(client, case["identifier"]):
            documents.append(
                MeetingDocument(
                    external_id=case_file["identifier"],
                    kommune="Elverum",
                    utvalg=meeting.utvalg,
                    moetedato=meeting.moetedato,
                    dokumenttype="saksframlegg",
                    tittel=case_file["title"],
                    saksnummer=saksnummer,
                    kilde_url=kilde_url,
                    file_url=case_file["url"],
                )
            )

    return documents
