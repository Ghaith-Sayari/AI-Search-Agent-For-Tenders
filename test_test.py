# tests/test_gatekeeper_end_to_end.py

import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID
import time

import pytest
from agents.gatekeeper.classifiers import GatekeeperClassifier, GatekeeperSettings
from agents.gatekeeper.audit import GatekeeperDecisionRepository
from agents.gatekeeper.schemas import (
    GatekeeperDecision,
    GatekeeperStatus,
    RawTenderStagingRecord,
)
from db.client import get_client


logger = logging.getLogger(__name__)


def fetch_raw_test_records(limit: int | None = None) -> List[dict]:
    """
    Fetch raw tender records from Supabase `raw_test_db` table.
    
    Args:
        limit: Maximum number of records to fetch. None = all records.
    
    Returns:
        List of raw tender records as dictionaries.
    """
    client = get_client()
    query = client.table("raw_test_db").select("*")
    
    if limit:
        query = query.limit(limit)
    
    response = query.execute()
    
    if not response.data:
        logger.warning("No records found in raw_test_db")
        return []
    
    logger.info(f"Fetched {len(response.data)} records from raw_test_db")
    return response.data


def save_gatekeeper_decision(
    decision: GatekeeperDecision,
    repository: GatekeeperDecisionRepository,
) -> dict:
    """
    Save a Gatekeeper decision to the clean_test_db table via the audit repository.
    
    Args:
        decision: The GatekeeperDecision to save.
        repository: The GatekeeperDecisionRepository instance.
    
    Returns:
        The saved row from Supabase.
    """
    return repository.save(decision)


def test_gatekeeper_processes_raw_test_db_and_saves_to_clean_test_db():
    """
    End-to-end integration test:
    
    1. Fetch all records from Supabase `raw_test_db` table
    2. Process each through the Gatekeeper classifier
    3. Save decisions to Supabase `clean_test_db` table (via audit repository)
    4. Validate processing statistics
    
    This test:
    - Validates Gatekeeper classifier works with real Supabase data
    - Generates immutable audit trail for all decisions
    - Supports iterative refinement of gatekeeper policies
    - Detects data quality issues in raw_test_db
    """
    # ==================== SETUP ====================
    logger.info("=" * 60)
    logger.info("GATEKEEPER END-TO-END TEST: raw_test_db â†’ clean_test_db")
    logger.info("=" * 60)
    
    # Initialize classifier with environment settings
    settings = GatekeeperSettings.from_env()
    classifier = GatekeeperClassifier(settings=settings)
    
    # Initialize repository (saves to clean_test_db via audit_table config)
    repository = GatekeeperDecisionRepository(table_name="clean_test_db")
    
    # ==================== FETCH ====================
    logger.info("\n[1] Fetching raw test records from Supabase...")
    raw_records = fetch_raw_test_records()
    
    if not raw_records:
        pytest.skip("No records in raw_test_db to process")
    
    logger.info(f"âœ“ Loaded {len(raw_records)} raw tender records")
    
    # ==================== PROCESS ====================
    logger.info("\n[2] Processing records through Gatekeeper classifier...")
    
    decisions: List[GatekeeperDecision] = []
    errors: List[dict] = []
    
    for i, raw_data in enumerate(raw_records, 1):
        try:
            # Convert Supabase row to RawTenderStagingRecord
            record = RawTenderStagingRecord(
                id=UUID(str(raw_data["id"])),  # Generate new UUID for this processing run
                unique_key=raw_data.get("unique_key", f"raw-{i}"),
                source=raw_data.get("source", "unknown_source"),
                title=raw_data.get("title"),
                country=raw_data.get("country"),
                posting_date=raw_data.get("posting_date"),
                deadline=raw_data.get("deadline"),
                url=raw_data.get("url"),
                description=raw_data.get("description"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                external_id=raw_data.get("external_id"),
            )
            
            # Classify with Gatekeeper
            decision = classifier.classify(record)
            time.sleep(45)
            decisions.append(decision)
            
            logger.info(
                f"  [{i:3d}/{len(raw_records)}] {record.unique_key:30s} â†’ "
                f"{decision.status.value:15s} (confidence: {decision.confidence_score:.2f})"
            )
            
        except Exception as e:
            error_entry = {
                "index": i,
                "unique_key": raw_data.get("unique_key", "unknown"),
                "error": str(e),
                "error_type": type(e).__name__,
            }
            errors.append(error_entry)
            logger.error(
                f"  [{i:3d}/{len(raw_records)}] {raw_data.get('unique_key', 'unknown'):30s} "
                f"â†’ ERROR: {type(e).__name__}: {e}"
            )
    
    # ==================== SAVE ====================
    logger.info(f"\n[3] Saving {len(decisions)} decisions to Supabase clean_test_db...")
    
    saved_count = 0
    save_errors = []
    
    for decision in decisions:
        try:
            saved_row = save_gatekeeper_decision(decision, repository)
            saved_count += 1
            logger.debug(f"  âœ“ Saved decision for {decision.unique_key}")
        except Exception as e:
            save_error = {
                "unique_key": decision.unique_key,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            save_errors.append(save_error)
            logger.error(f"  âœ— Failed to save decision for {decision.unique_key}: {e}")
    
    logger.info(f"âœ“ Saved {saved_count}/{len(decisions)} decisions to clean_test_db")
    
    # ==================== SUMMARY ====================
    logger.info("\n[4] Processing Summary:")
    logger.info(f"  Total raw records:        {len(raw_records)}")
    logger.info(f"  Successfully classified: {len(decisions)} ({100*len(decisions)/len(raw_records):.1f}%)")
    logger.info(f"  Classification errors:   {len(errors)}")
    logger.info(f"  Successfully saved:      {saved_count}/{len(decisions)}")
    logger.info(f"  Save errors:             {len(save_errors)}")
    
    # Status distribution
    status_counts = {}
    for decision in decisions:
        status = decision.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    logger.info("\n[5] Decision Status Distribution:")
    for status, count in sorted(status_counts.items()):
        percentage = 100 * count / len(decisions) if decisions else 0
        logger.info(f"  {status:15s}: {count:4d} ({percentage:5.1f}%)")
    
    # Confidence statistics
    if decisions:
        confidences = [d.confidence_score for d in decisions]
        logger.info("\n[6] Confidence Score Statistics:")
        logger.info(f"  Average:  {sum(confidences)/len(confidences):.3f}")
        logger.info(f"  Min:      {min(confidences):.3f}")
        logger.info(f"  Max:      {max(confidences):.3f}")
    
    logger.info("\n" + "=" * 60)
    
    # ==================== ASSERTIONS ====================
    assert len(decisions) > 0, "At least one record should be processed"
    assert saved_count == len(decisions), "All decisions should be saved to clean_test_db"
    assert len(save_errors) == 0, f"No save errors should occur: {save_errors}"
    
    # Ensure we have meaningful decisions (not all FAILED)
    failed_count = status_counts.get(GatekeeperStatus.FAILED.value, 0)
    assert failed_count < len(decisions), "Most decisions should not be FAILED"


def test_gatekeeper_handles_batch_with_error_recovery():
    """
    Robustness test: Verify that partial failures don't stop the entire batch.

    This test processes raw_test_db but continues even if individual records fail,
    ensuring batch resilience.
    """
    logger.info("\n[Robustness Test] Processing with error recovery...")

    settings = GatekeeperSettings.from_env()
    classifier = GatekeeperClassifier(settings=settings)
    repository = GatekeeperDecisionRepository(table_name="clean_test_db")

    raw_records = fetch_raw_test_records(limit=2)  # Sample first 2

    if not raw_records:
        pytest.skip("Not enough records to test error recovery")

    classified = 0
    saved = 0
    classification_errors = 0
    save_errors = 0

    for raw_data in raw_records:
        try:
            record = RawTenderStagingRecord(
                id=UUID(str(raw_data["id"])),
                unique_key=raw_data.get("unique_key", "unknown"),
                source=raw_data.get("source", "unknown"),
                title=raw_data.get("title"),
                description=raw_data.get("description"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            decision = classifier.classify(record)
            classified += 1
        except Exception as e:
            classification_errors += 1
            logger.warning(f"Skipping record due to classification error: {e}")
            continue

        try:
            save_gatekeeper_decision(decision, repository)
            saved += 1
        except Exception as e:
            save_errors += 1
            logger.warning(f"Skipping record due to save error: {e}")
            continue

    logger.info(
        f"✓ Error recovery summary: total={len(raw_records)}, "
        f"classified={classified}, saved={saved}, "
        f"classification_errors={classification_errors}, save_errors={save_errors}"
    )
    assert classified > 0, "Should classify at least some records"

def test_gatekeeper_decision_audit_trail():
    """
    Verify that all decisions have proper audit metadata.
    """
    logger.info("\n[Audit Trail Test] Verifying decision metadata...")
    
    settings = GatekeeperSettings.from_env()
    classifier = GatekeeperClassifier(settings=settings)
    
    raw_records = fetch_raw_test_records(limit=5)
    
    if not raw_records:
        pytest.skip("Not enough records to test audit trail")
    
    for raw_data in raw_records:
        try:
            record = RawTenderStagingRecord(
                id=UUID(str(raw_data["id"])),
                unique_key=raw_data.get("unique_key", "unknown"),
                source=raw_data.get("source", "unknown"),
                title=raw_data.get("title"),
                description=raw_data.get("description"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            decision = classifier.classify(record)
            
            # Verify audit metadata
            assert decision.staging_tender_id is not None
            assert decision.unique_key == record.unique_key
            assert decision.processed_at is not None
            assert decision.policy_version == settings.policy_version
            assert decision.agent_version == settings.agent_version
            assert decision.decision_reason  # Non-empty reason
            assert 0 <= decision.confidence_score <= 1
            
            logger.info(f"âœ“ {record.unique_key}: Audit trail verified")
        except Exception as e:
            logger.error(f"âœ— Audit trail check failed: {e}")
            raise


if __name__ == "__main__":
    # Enable detailed logging for local testing
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)8s] %(message)s",
    )
    
    # Run the main test
    test_gatekeeper_processes_raw_test_db_and_saves_to_clean_test_db()
