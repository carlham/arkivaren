import json
from datetime import date
from pathlib import Path

import pytest

from app.nav.mapping import clean_text, map_ad, parse_deadline

FIXTURES = Path(__file__).parent / "fixtures" / "nav"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_map_ad_picks_the_columns_we_store():
    fields = map_ad(load_fixture("ad_new.json"))

    assert fields["uuid"] == "e3187905-124a-46c8-ac20-3d94d746f363"
    assert fields["status"] == "active"
    assert fields["municipal"] == "SANDNES"
    assert fields["county"] == "ROGALAND"
    assert fields["extent"] == "Heltid"
    assert fields["sector"] == "Privat"
    assert fields["employer"] == {"orgnr": "973635611", "name": "ABB AS"}
    assert fields["occupation_categories"] == [{"level1": "IT", "level2": "Utvikling"}]
    assert fields["application_url"].startswith("https://")


def test_map_ad_stores_no_contact_information():
    fields = map_ad(load_fixture("ad_new.json"))

    # A name written in the description text is a known limitation (see the M2 spec), so the
    # name is not checked here. Email, phone, role and title from contactList must be gone.
    everything = json.dumps(fields, default=str)
    for contact_value in ("kari.testperson", "99 88 77 66", "Rekrutterer"):
        assert contact_value not in everything


def test_description_is_plain_text_with_contact_details_removed():
    text = map_ad(load_fixture("ad_new.json"))["description"]

    assert "<p>" not in text and "<strong>" not in text
    assert "kari.testperson@example.com" not in text
    assert "99 88 77 66" not in text
    assert "[fjernet]" in text


def test_description_removes_phone_number_with_country_code():
    text = map_ad(load_fixture("ad_changed.json"))["description"]

    assert "98765432" not in text
    assert "[fjernet]" in text


@pytest.mark.parametrize(
    "written",
    ["99 88 77 66", "99887766", "912 34 567", "+47 98765432", "0047 99 88 77 66", "99-88-77-66"],
)
def test_clean_text_removes_phone_formats(written):
    assert clean_text(f"<p>Ring {written} nå</p>") == "Ring [fjernet] nå"


def test_clean_text_keeps_numbers_that_are_not_phone_numbers():
    text = "Org.nr 973635611, ansatte siden 2015, lønn fra 650000"

    assert clean_text(text) == text


def test_clean_text_removes_email_and_splits_paragraphs():
    assert clean_text("<p>Send til a.b@firma.no</p><p>Takk&nbsp;for&nbsp;interessen</p>") == (
        "Send til [fjernet]\nTakk\xa0for\xa0interessen"
    )


@pytest.mark.parametrize(
    "written, expected",
    [
        ("2026-12-01T23:59:59+01:00", date(2026, 12, 1)),
        ("2026-12-01", date(2026, 12, 1)),
        ("01.12.2026", date(2026, 12, 1)),
        ("Snarest", None),
        ("We are evaluating candidates continuously!", None),
        ("31.02.2026", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_deadline(written, expected):
    assert parse_deadline(written) == expected


def test_map_ad_keeps_original_deadline_text_even_when_it_is_not_a_date():
    fields = map_ad(load_fixture("ad_new.json"))

    assert fields["application_deadline_text"] == "We are evaluating candidates continuously!"
    assert fields["application_deadline"] is None
