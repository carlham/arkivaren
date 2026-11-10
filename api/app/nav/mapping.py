import html
import re
from datetime import date, datetime

REMOVED = "[fjernet]"

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Norwegian phone numbers: 8 digits as 2-2-2-2 or 3-2-3, with optional +47 or 0047.
# Dots are only allowed as 22.33.44.55, so that dates like 01.12.2026 are left alone.
PHONE = re.compile(
    r"(?<!\d)(?:(?:\+|00)47[\s-]?)?"
    r"(?:\d{3}[\s-]?\d{2}[\s-]?\d{3}|\d{2}(?:[\s-]?\d{2}){3}|\d{2}(?:\.\d{2}){3})(?!\d)"
)
BLOCK_END = re.compile(r"</(?:p|li|h[1-6]|div|ul|ol)>|<br\s*/?>", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")
ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
NORWEGIAN_DATE = re.compile(r"^(\d{2})[.-](\d{2})[.-](\d{4})$")


def remove_contact_info(text: str) -> str:
    return PHONE.sub(REMOVED, EMAIL.sub(REMOVED, text))


def clean_text(raw_html: str) -> str:
    """Turn the HTML description into plain text without emails and phone numbers."""
    text = TAG.sub("", BLOCK_END.sub("\n", raw_html))
    text = remove_contact_info(html.unescape(text))
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def clean_url(url: str | None) -> str | None:
    """Drop links that are an email address (mailto:) or contain one."""
    if not url or url.lower().startswith("mailto:") or EMAIL.search(url):
        return None
    return url


def parse_deadline(text: str | None) -> date | None:
    """NAV's applicationDue is free text. Only ISO dates and dd.mm.yyyy or dd-mm-yyyy become a date."""
    if not text:
        return None
    text = text.strip()
    try:
        if match := ISO_DATE.match(text):
            year, month, day = match.groups()
        elif match := NORWEGIAN_DATE.match(text):
            day, month, year = match.groups()
        else:
            return None
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def map_ad(detail: dict) -> dict:
    """Map a feed entry with details to job_ad columns, plus `employer` (orgnr and name, or None).

    Contact persons (contactList) and the employer description are never copied. Emails and
    phone numbers are removed from the title, the description and the deadline text, and an
    application link that is an email address is dropped.
    """
    ad = detail["ad_content"]
    location = (ad.get("workLocations") or [{}])[0]
    employer = ad.get("employer") or {}
    deadline_text = ad.get("applicationDue") or None
    deadline = parse_deadline(deadline_text)
    if deadline_text and not deadline:
        # A date can look like a phone number, so only text that is not a date is cleaned.
        deadline_text = remove_contact_info(deadline_text)
    return {
        "uuid": detail["uuid"],
        "status": detail["status"].lower(),
        "title": remove_contact_info(ad["title"]),
        "description": clean_text(ad.get("description") or ""),
        "municipal": location.get("municipal") or None,
        "county": location.get("county") or None,
        "extent": ad.get("extent") or None,
        "sector": ad.get("sector") or None,
        "application_url": clean_url(ad.get("applicationUrl")),
        "application_deadline_text": deadline_text,
        "application_deadline": deadline,
        "occupation_categories": ad.get("occupationCategories"),
        "published_at": datetime.fromisoformat(ad["published"]) if ad.get("published") else None,
        "employer": {"orgnr": employer["orgnr"], "name": employer["name"]} if employer.get("orgnr") else None,
    }
