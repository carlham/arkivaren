import html
import re
from datetime import date, datetime

REMOVED = "[fjernet]"

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Norwegian phone numbers: 8 digits as 2-2-2-2 or 3-2-3, with optional +47 or 0047.
PHONE = re.compile(r"(?<!\d)(?:(?:\+|00)47[\s-]?)?(?:\d{3}[\s-]?\d{2}[\s-]?\d{3}|\d{2}(?:[\s-]?\d{2}){3})(?!\d)")
BLOCK_END = re.compile(r"</(?:p|li|h[1-6]|div|ul|ol)>|<br\s*/?>", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")
ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
NORWEGIAN_DATE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")


def clean_text(raw_html: str) -> str:
    """Turn the HTML description into plain text without emails and phone numbers."""
    text = TAG.sub("", BLOCK_END.sub("\n", raw_html))
    text = html.unescape(text)
    text = PHONE.sub(REMOVED, EMAIL.sub(REMOVED, text))
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def parse_deadline(text: str | None) -> date | None:
    """NAV's applicationDue is free text. Only ISO dates and dd.mm.yyyy become a date."""
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

    Contact persons (contactList) and the employer description are never copied.
    """
    ad = detail["ad_content"]
    location = (ad.get("workLocations") or [{}])[0]
    employer = ad.get("employer") or {}
    deadline_text = ad.get("applicationDue") or None
    return {
        "uuid": detail["uuid"],
        "status": detail["status"].lower(),
        "title": ad["title"],
        "description": clean_text(ad.get("description") or ""),
        "municipal": location.get("municipal") or None,
        "county": location.get("county") or None,
        "extent": ad.get("extent") or None,
        "sector": ad.get("sector") or None,
        "application_url": ad.get("applicationUrl") or None,
        "application_deadline_text": deadline_text,
        "application_deadline": parse_deadline(deadline_text),
        "occupation_categories": ad.get("occupationCategories"),
        "published_at": datetime.fromisoformat(ad["published"]) if ad.get("published") else None,
        "source_modified_at": datetime.fromisoformat(detail["sistEndret"]),
        "employer": {"orgnr": employer["orgnr"], "name": employer["name"]} if employer.get("orgnr") else None,
    }
