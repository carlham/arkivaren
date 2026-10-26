import json
from datetime import date

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401 - registrerer Document på Base.metadata
from app.adapters.elverum_innsyn import (
    SESSION_PAGE_PATH,
    ElverumClient,
    get_meeting_documents,
    list_meetings,
    list_utvalg,
)
from app.db import Base
from app.ingest import elverum as elverum_ingest

API = "/api/presentation/v2/nye-innsyn"

UTVALG_LIST_RESPONSE = {
    "content": {
        "searchItems": {"pageNumber": 1, "pageSize": 1, "items": []},
        "searchOptions": {
            "searchFilters": [
                {
                    "identifier": "UtvalgID",
                    "fields": [
                        {"identifier": "u-tenant-2!gneNKC", "name": "Kommunestyret"},
                        {"identifier": "u-tenant-9!uAcxav", "name": "Arbeidsmiljøutvalget"},
                    ],
                }
            ]
        },
    }
}


def _meeting_item(identifier: str, dato: str) -> dict:
    return {
        "identifier": identifier,
        "title": "Kommunestyret",
        "type": "Mote",
        "properties": {"dato": dato, "sted": "Kommunestyresalen"},
    }


MEETING_PAGE_1 = {
    "content": {
        "searchItems": {
            "pageNumber": 1,
            "pageSize": 2,
            "items": [
                _meeting_item("m-tenant-1!aaa", "28.01.2026"),
                _meeting_item("m-tenant-2!bbb", "04.03.2026"),
            ],
        }
    }
}
MEETING_PAGE_2 = {
    "content": {
        "searchItems": {
            "pageNumber": 2,
            "pageSize": 2,
            "items": [_meeting_item("m-tenant-3!ccc", "25.03.2026")],
        }
    }
}

MEETING_DETAIL_RESPONSE = {
    "content": {
        "title": "Møte i Kommunestyret",
        "identifier": "m-tenant-1!aaa",
        "b": [
            {"key": "UtvalgLenke", "type": "Metadata", "title": "utvalgslenke"},
            {
                "key": "MEETING_FILES",
                "type": "FileListButton",
                "title": "Møtedokumenter",
                "b": [
                    {
                        "key": "MEETING_FILES_SUMMON",
                        "type": "Text",
                        "title": "Møteinnkalling (pdf, 80KB)",
                        "identifier": "v-file-innkalling",
                        "url": f"{API}/filer/v-file-innkalling?pid=1",
                    },
                    {
                        "key": "MEETING_FILES_PROTOCOL",
                        "type": "Text",
                        "title": "Møteprotokoll (pdf, 169KB)",
                        "identifier": "v-file-protokoll",
                        "url": f"{API}/filer/v-file-protokoll?pid=1",
                    },
                    {"type": "Text", "title": "Møtebok (ikke publisert enda)"},
                ],
            },
            {
                "key": "MEETING_CASES",
                "type": "DocumentList",
                "title": "Saksliste",
                "b": [
                    {
                        "identifier": "d-case-1",
                        "title": "Godkjenning av innkalling/saksliste",
                        "type": "AsyncDocument",
                        "b": [
                            {
                                "type": "PropertyList",
                                "b": [
                                    {"title": "Saksnummer", "text": "001/26", "type": "Property"},
                                    {"title": "Antall dokumenter", "text": "1", "type": "Property"},
                                ],
                            }
                        ],
                    },
                    {
                        "identifier": "d-case-2",
                        "title": "Sak uten dokumenter",
                        "type": "AsyncDocument",
                        "b": [
                            {
                                "type": "PropertyList",
                                "b": [
                                    {"title": "Saksnummer", "text": "002/26", "type": "Property"},
                                    {"title": "Antall dokumenter", "text": "0", "type": "Property"},
                                ],
                            }
                        ],
                    },
                ],
            },
        ],
    }
}

SAKSFREMLEGG_RESPONSE = {
    "content": {
        "title": "Godkjenning av innkalling/saksliste",
        "identifier": "d-case-1",
        "b": [
            {
                "key": "MEETING_CASE_FILES",
                "type": "FileList",
                "title": "Saksframlegg",
                "b": [
                    {
                        "identifier": "v-file-saksframlegg",
                        "title": "Godkjenning av innkalling/saksliste (pdf, 56KB)",
                        "url": f"{API}/filer/v-file-saksframlegg?pid=1",
                        "type": "Text",
                    }
                ],
            }
        ],
        "props": {"saksnummer": "001/26", "antall dokumenter": "1", "sakstype": "Politisk sak"},
    }
}


def make_transport(
    saksfremlegg_calls: list[str] | None = None,
    session_calls: list[str] | None = None,
) -> httpx.MockTransport:
    pages = {1: MEETING_PAGE_1, 2: MEETING_PAGE_2}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path

        if path == SESSION_PAGE_PATH:
            if session_calls is not None:
                session_calls.append(path)
            return httpx.Response(200, text="<html></html>")

        if path == f"{API}/overview":
            payload = json.loads(request.read())
            keys = {kv["key"] for kv in payload["keyValues"]}
            if "UtvalgID" in keys:
                page = next(
                    int(kv["value"]) for kv in payload["keyValues"] if kv["key"] == "page"
                )
                return httpx.Response(200, json=pages[page])
            return httpx.Response(200, json=UTVALG_LIST_RESPONSE)

        if path == f"{API}//mote/m-tenant-1!aaa":
            return httpx.Response(200, json=MEETING_DETAIL_RESPONSE)

        if path == f"{API}/mote/saksfremlegg/d-case-1":
            if saksfremlegg_calls is not None:
                saksfremlegg_calls.append(path)
            return httpx.Response(200, json=SAKSFREMLEGG_RESPONSE)

        if path.startswith(f"{API}/filer/"):
            return httpx.Response(200, content=b"%PDF-fake-content")

        raise AssertionError(f"Uventet kall i test: {path}")

    return httpx.MockTransport(handler)


@pytest.fixture
def client() -> ElverumClient:
    with ElverumClient(
        user_agent="test-agent",
        min_request_interval_seconds=0,
        transport=make_transport(),
    ) as c:
        yield c


def test_list_utvalg_leser_fra_search_filters(client: ElverumClient):
    utvalg = list_utvalg(client)
    assert {u.name for u in utvalg} == {"Kommunestyret", "Arbeidsmiljøutvalget"}
    assert any(u.id == "u-tenant-2!gneNKC" for u in utvalg)


def test_session_side_hentes_bare_en_gang_per_klient():
    session_calls: list[str] = []
    with ElverumClient(
        user_agent="test-agent",
        min_request_interval_seconds=0,
        transport=make_transport(session_calls=session_calls),
    ) as c:
        list_utvalg(c)
        list_meetings(
            c,
            utvalg_id="u-tenant-2!gneNKC",
            from_date=date(2026, 1, 1),
            to_date=date(2026, 12, 31),
        )
    assert session_calls == [SESSION_PAGE_PATH]


def test_list_meetings_paginerer_til_siste_side(client: ElverumClient):
    meetings = list_meetings(
        client,
        utvalg_id="u-tenant-2!gneNKC",
        from_date=date(2026, 1, 1),
        to_date=date(2026, 12, 31),
    )
    assert [m.id for m in meetings] == ["m-tenant-1!aaa", "m-tenant-2!bbb", "m-tenant-3!ccc"]
    assert meetings[0].moetedato == date(2026, 1, 28)


def test_get_meeting_documents_mapper_møtedokumenter_og_saksframlegg(client: ElverumClient):
    from app.adapters.elverum_innsyn import MeetingRef

    meeting = MeetingRef(
        id="m-tenant-1!aaa",
        utvalg="Kommunestyret",
        moetedato=date(2026, 1, 28),
        sted="Kommunestyresalen",
    )
    documents = get_meeting_documents(client, meeting)

    by_type = {d.dokumenttype: d for d in documents}
    assert set(by_type) == {"innkalling", "protokoll", "saksframlegg"}
    assert by_type["innkalling"].external_id == "v-file-innkalling"
    assert by_type["innkalling"].saksnummer is None
    assert by_type["saksframlegg"].saksnummer == "001/26"
    assert by_type["saksframlegg"].external_id == "v-file-saksframlegg"
    assert all(d.kilde_url.endswith("#/details/m-tenant-1!aaa") for d in documents)


def test_get_meeting_documents_henter_ikke_saksframlegg_for_saker_uten_dokumenter():
    saksfremlegg_calls: list[str] = []
    with ElverumClient(
        user_agent="test-agent",
        min_request_interval_seconds=0,
        transport=make_transport(saksfremlegg_calls),
    ) as c:
        from app.adapters.elverum_innsyn import MeetingRef

        meeting = MeetingRef(
            id="m-tenant-1!aaa",
            utvalg="Kommunestyret",
            moetedato=date(2026, 1, 28),
            sted="Kommunestyresalen",
        )
        get_meeting_documents(c, meeting)

    assert saksfremlegg_calls == [f"{API}/mote/saksfremlegg/d-case-1"]


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_run_oppretter_ingen_duplikater_ved_ny_kjøring(db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(elverum_ingest.settings, "min_request_interval_seconds", 0)
    monkeypatch.setattr(elverum_ingest.settings, "http_user_agent", "test-agent")
    monkeypatch.setattr(elverum_ingest, "DATA_DIR", tmp_path)

    first = elverum_ingest.run(
        "Kommunestyret", 2026, db_session, limit=1, transport=make_transport()
    )
    assert first.documents_new == 3
    assert first.documents_skipped == 0

    second = elverum_ingest.run(
        "Kommunestyret", 2026, db_session, limit=1, transport=make_transport()
    )
    assert second.documents_new == 0
    assert second.documents_skipped == 3
