from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Employer, JobAd


def make_job_ad(uuid: str, **fields) -> JobAd:
    return JobAd(
        uuid=uuid,
        status="active",
        title="Developer",
        source_modified_at=datetime(2026, 11, 10, tzinfo=timezone.utc),
        **fields,
    )


def test_job_ad_keeps_employer_and_occupation_categories(db):
    # An orgnr that cannot exist in the real data, which may be in the dev database.
    employer = Employer(orgnr="000000000", name="Test AS")
    categories = [{"level1": "IT", "level2": "Utvikling"}]
    db.add(make_job_ad("a", employer=employer, occupation_categories=categories))
    db.flush()

    saved = db.query(JobAd).filter_by(uuid="a").one()

    assert saved.employer.name == "Test AS"
    assert saved.occupation_categories == categories


def test_job_ad_uuid_is_unique(db):
    db.add(make_job_ad("a"))
    db.flush()
    db.add(make_job_ad("a"))

    with pytest.raises(IntegrityError):
        db.flush()
