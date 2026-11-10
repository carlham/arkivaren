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
    [
        "99 88 77 66", "99887766", "912 34 567", "+47 98765432", "0047 99 88 77 66", "99-88-77-66",
        "22.33.44.55", "+47 22.33.44.55",
    ],
)
def test_clean_text_removes_phone_formats(written):
    assert clean_text(f"<p>Ring {written} nå</p>") == "Ring [fjernet] nå"


def test_clean_text_removes_number_after_country_code_in_parentheses():
    assert clean_text("Ring (+47) 22 33 44 55.") == "Ring (+47) [fjernet]."


def test_clean_text_keeps_numbers_that_are_not_phone_numbers():
    text = "Org.nr 973635611, ansatte siden 2015, lønn fra 650000, frist 01.12.2026"

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
        ("01-12-2026", date(2026, 12, 1)),
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


def ad_with(**changes) -> dict:
    """The new-ad fixture with some fields in ad_content replaced."""
    detail = load_fixture("ad_new.json")
    detail["ad_content"].update(changes)
    return detail


@pytest.mark.parametrize(
    "link",
    ["mailto:kari.testperson@example.com", "MAILTO:kari@example.com", "https://apply.example.com/?to=kari@example.com"],
)
def test_application_link_that_is_an_email_address_is_dropped(link):
    assert map_ad(ad_with(applicationUrl=link))["application_url"] is None


def test_application_link_to_a_web_page_is_kept():
    link = "https://apply.recman.page/job_post.php?id=476166&path=nav&sub_id=87"

    assert map_ad(ad_with(applicationUrl=link))["application_url"] == link


def test_title_has_email_and_phone_removed():
    fields = map_ad(ad_with(title="Utvikler, kontakt kari@example.com eller 22 33 44 55"))

    assert fields["title"] == "Utvikler, kontakt [fjernet] eller [fjernet]"


def test_deadline_text_has_email_and_phone_removed_when_it_is_not_a_date():
    fields = map_ad(ad_with(applicationDue="Send søknad til kari@example.com, ring 22 33 44 55"))

    assert fields["application_deadline_text"] == "Send søknad til [fjernet], ring [fjernet]"
    assert fields["application_deadline"] is None


@pytest.mark.parametrize("written", ["2026-12-01T23:59:59+01:00", "01.12.2026", "01-12-2026"])
def test_deadline_text_that_is_a_date_is_stored_as_written(written):
    fields = map_ad(ad_with(applicationDue=written))

    assert fields["application_deadline_text"] == written
    assert fields["application_deadline"] == date(2026, 12, 1)
