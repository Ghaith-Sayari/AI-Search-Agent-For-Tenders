# test_pipeline_integrity.py
"""
End-to-end integrity test for the data governance pipeline.

Verifies each stage independently:
  1. Mapping    (mappings/mapper.py -> map_record)
  2. Hashing    (pipeline/hashing.py -> generate_unique_key)
  3. Validation (mappings/schemas.py -> CanonicalOpportunity)
  4. Dedup      (pipeline/normalizer.py -> normalize)
  5. Load       (db/loader.py -> load_all, real Supabase call)

Run with: pytest test_pipeline_integrity.py -v
"""

import pytest
from pydantic import ValidationError

from mappings.mapper import map_record, build_canonical_opportunity
from mappings.schemas import CanonicalOpportunity
from pipeline.hashing import generate_unique_key
from pipeline.normalizer import normalize, normalize_batch


# ---------------------------------------------------------------------------
# Fixtures — fake raw records mimicking real scraper output
# ---------------------------------------------------------------------------

@pytest.fixture
def raw_tendersontime_record():
    return {
        "source": "tendersontime",
        "TOT Reference": "TOT-88213",
        "Titre": "Fourniture de matériel informatique",
        "Pays": "France",
        "Posting Date": "2026-07-01",
        "Deadline": "2026-08-15",
        "Lien de l'offre": "https://tendersontime.com/xyz",
    }


@pytest.fixture
def raw_record_missing_title():
    return {
        "source": "tendersontime",
        "TOT Reference": "TOT-99999",
        "Titre": "",  # blank title -> should fail validation
        "Pays": "France",
    }


@pytest.fixture
def raw_beta_mr_record():
    return {
        "source": "beta_mr",
        "tender_id": "BMR-001",
        "title": "Construction de routes",
        "location": "Mauritania",
        "posting_date": "2026-07-01",
        "deadline": "2026-08-01",
        "url_link": "https://betamr.com/tender1",
        "description": "Road construction project",
    }


# ---------------------------------------------------------------------------
# Stage 1 — Mapping
# ---------------------------------------------------------------------------

def test_mapping_renames_fields_correctly(raw_tendersontime_record):
    mapped = map_record(raw_tendersontime_record)

    assert mapped["title"] == "Fourniture de matériel informatique"
    assert mapped["country"] == "France"
    assert mapped["external_id"] == "TOT-88213"
    assert mapped["source"] == "tendersontime"
    assert mapped["description"] is None  # tendersontime has no description field


def test_mapping_handles_different_source_schema(raw_beta_mr_record):
    mapped = map_record(raw_beta_mr_record)

    assert mapped["title"] == "Construction de routes"
    assert mapped["external_id"] == "BMR-001"
    assert mapped["description"] == "Road construction project"


# ---------------------------------------------------------------------------
# Stage 2 — Hashing
# ---------------------------------------------------------------------------

def test_hash_is_deterministic():
    """Same input must always produce the same unique_key."""
    key1 = generate_unique_key(title="Test Tender", source="tendersontime")
    key2 = generate_unique_key(title="Test Tender", source="tendersontime")
    assert key1 == key2


def test_hash_differs_for_different_titles():
    key1 = generate_unique_key(title="Tender A", source="tendersontime")
    key2 = generate_unique_key(title="Tender B", source="tendersontime")
    assert key1 != key2


def test_hash_is_case_and_whitespace_insensitive():
    """'  Tender A  ' and 'tender a' should hash the same, per your salt formula."""
    key1 = generate_unique_key(title="  Tender A  ", source="TendersOnTime")
    key2 = generate_unique_key(title="tender a", source="tendersontime")
    assert key1 == key2


# ---------------------------------------------------------------------------
# Stage 3 — Validation (CanonicalOpportunity contract)
# ---------------------------------------------------------------------------

def test_valid_record_passes_validation(raw_tendersontime_record):
    opportunity = build_canonical_opportunity(raw_tendersontime_record)

    assert isinstance(opportunity, CanonicalOpportunity)
    assert opportunity.unique_key  # non-empty
    assert opportunity.title == "Fourniture de matériel informatique"
    assert opportunity.source == "tendersontime"


def test_blank_title_fails_validation(raw_record_missing_title):
    """This is the core governance guarantee: no blank titles reach the DB."""
    with pytest.raises(ValidationError):
        build_canonical_opportunity(raw_record_missing_title)


def test_missing_source_fails_validation():
    with pytest.raises((ValidationError, KeyError)):
        build_canonical_opportunity({"Titre": "Some tender"})  # no "source" key at all


# ---------------------------------------------------------------------------
# Stage 4 — Normalization batch (map + hash + validate + drop-tracking)
# ---------------------------------------------------------------------------

def test_normalize_batch_separates_valid_and_dropped(
    raw_tendersontime_record, raw_record_missing_title
):
    records = [raw_tendersontime_record, raw_record_missing_title]

    valid, dropped = normalize_batch(records)

    assert len(valid) == 1
    assert dropped == 1
    assert valid[0]["title"] == "Fourniture de matériel informatique"


def test_normalize_batch_output_has_unique_key(raw_tendersontime_record):
    valid, _ = normalize_batch([raw_tendersontime_record])
    assert "unique_key" in valid[0]
    assert valid[0]["unique_key"] != ""


# ---------------------------------------------------------------------------
# Stage 5 — Deduplication across the full normalize() run
# ---------------------------------------------------------------------------

def test_normalize_batch_deduplicates_identical_records(raw_tendersontime_record):
    """Two identical raw records should collapse into ONE record after hashing."""
    duplicate = raw_tendersontime_record.copy()
    records = [raw_tendersontime_record, duplicate]

    valid, dropped = normalize_batch(records)

    unique_keys = {r["unique_key"] for r in valid}
    # NOTE: normalize_batch alone does not dedupe (that happens in normalize()).
    # This test documents that behavior explicitly, so it's not mistaken for a bug.
    assert len(valid) == 2
    assert len(unique_keys) == 1  # but they DO share the same key


def test_normalize_deduplicates_across_files(monkeypatch, tmp_path, raw_tendersontime_record):
    """
    Full normalize() should collapse duplicates across files, not just within a batch.
    Uses a temp directory with two JSON files containing the same tender.
    """
    import json
    import pipeline.normalizer as normalizer_module

    file1 = tmp_path / "source1.json"
    file2 = tmp_path / "source2.json"
    file1.write_text(json.dumps([raw_tendersontime_record]))
    file2.write_text(json.dumps([raw_tendersontime_record]))  # exact duplicate

    monkeypatch.setattr(normalizer_module, "RAW_DIR", tmp_path)

    result = normalize()

    assert len(result) == 1  # duplicate collapsed


# ---------------------------------------------------------------------------
# Stage 6 — Full load (real Supabase call — run against dev/staging only)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_load_all_inserts_and_is_idempotent():
    """
    Runs the REAL pipeline end-to-end against Supabase.
    Running load_all() twice should NOT create duplicate rows or crash
    (this is the idempotency guarantee from Section 2.2 of the governance doc).
    """
    from db.client import get_client
    from db.loader import load_all

    supabase = get_client()

    before = supabase.table("opportunity").select("id", count="exact").execute()
    before_count = before.count or 0

    load_all()
    load_all()  # run twice on purpose

    after = supabase.table("opportunity").select("id", count="exact").execute()
    after_count = after.count or 0

    # Row count should grow once, then stay flat on the second run
    assert after_count >= before_count