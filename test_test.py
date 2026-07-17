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
from pipeline.gatekeeper_pipeline import GatekeeperPipeline


logger = logging.getLogger(__name__)


# The fetch_raw_test_records and save_gatekeeper_decision functions have been removed
# as this logic is now encapsulated within the GatekeeperPipeline class.


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
    
    pipeline = GatekeeperPipeline(
        classifier=classifier,
        source_table="raw_test_db",
        audit_table="clean_test_db",
        production_table=None
    )
    
    logger.info("\n[1] Running GatekeeperPipeline...")
    summary = pipeline.run(limit=None, continue_on_error=True)
    
    if summary["total_fetched"] == 0:
        pytest.skip("No records in raw_test_db to process")
        
    decisions = summary["decisions"]
    
    # ==================== SUMMARY ====================
    logger.info("\n[2] Processing Summary:")
    logger.info(f"  Total raw records:        {summary['total_fetched']}")
    logger.info(f"  Successfully classified: {summary['processed']}")
    logger.info(f"  Skipped (deduplicated):  {summary['skipped']}")
    logger.info(f"  Classification errors:   {summary['classification_errors']}")
    logger.info(f"  Successfully saved:      {summary['saved_audit']}/{summary['processed']}")
    logger.info(f"  Save errors:             {summary['save_errors']}")
    
    # Status distribution
    status_counts = {}
    for decision in decisions:
        status = decision.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    logger.info("\n[3] Decision Status Distribution:")
    for status, count in sorted(status_counts.items()):
        percentage = 100 * count / len(decisions) if decisions else 0
        logger.info(f"  {status:15s}: {count:4d} ({percentage:5.1f}%)")
    
    # Confidence statistics
    if decisions:
        confidences = [d.confidence_score for d in decisions]
        logger.info("\n[4] Confidence Score Statistics:")
        logger.info(f"  Average:  {sum(confidences)/len(confidences):.3f}")
        logger.info(f"  Min:      {min(confidences):.3f}")
        logger.info(f"  Max:      {max(confidences):.3f}")
    
    logger.info("\n" + "=" * 60)
    
    # ==================== ASSERTIONS ====================
    # If everything was skipped, we should adjust assertions
    if summary["skipped"] == summary["total_fetched"]:
        logger.info("All records were skipped. Assertions will reflect 0 processed.")
        assert summary["processed"] == 0
    else:
        assert summary["processed"] > 0, "At least one record should be processed"
        assert summary["saved_audit"] == summary["processed"], "All decisions should be saved to clean_test_db"
        assert summary["save_errors"] == 0, f"No save errors should occur"
        
        # Ensure we have meaningful decisions (not all FAILED)
        failed_count = status_counts.get(GatekeeperStatus.FAILED.value, 0)
        assert failed_count < summary["processed"], "Most decisions should not be FAILED"


def test_gatekeeper_handles_batch_with_error_recovery():
    """
    Robustness test: Verify that partial failures don't stop the entire batch.

    This test processes raw_test_db but continues even if individual records fail,
    ensuring batch resilience.
    """
    logger.info("\n[Robustness Test] Processing with error recovery...")

    settings = GatekeeperSettings.from_env()
    classifier = GatekeeperClassifier(settings=settings)
    
    pipeline = GatekeeperPipeline(
        classifier=classifier,
        source_table="raw_test_db",
        audit_table="clean_test_db",
        production_table=None
    )
    
    # We test that the pipeline handles errors and continues
    summary = pipeline.run(limit=2, continue_on_error=True)
    
    if summary["total_fetched"] == 0:
        pytest.skip("Not enough records to test error recovery")

    logger.info(
        f"✓ Error recovery summary: total={summary['total_fetched']}, "
        f"classified={summary['processed']}, saved={summary['saved_audit']}, "
        f"classification_errors={summary['classification_errors']}, save_errors={summary['save_errors']}"
    )
    if summary["skipped"] < summary["total_fetched"]:
        assert summary["processed"] + summary["classification_errors"] > 0, "Should attempt some records"

def test_gatekeeper_decision_audit_trail():
    """
    Verify that all decisions have proper audit metadata.
    """
    logger.info("\n[Audit Trail Test] Verifying decision metadata...")
    
    settings = GatekeeperSettings.from_env()
    classifier = GatekeeperClassifier(settings=settings)
    
    pipeline = GatekeeperPipeline(
        classifier=classifier,
        source_table="raw_test_db",
        audit_table="clean_test_db",
        production_table=None
    )
    
    summary = pipeline.run(limit=5, continue_on_error=True)
    
    if summary["total_fetched"] == 0:
        pytest.skip("Not enough records to test audit trail")
        
    for decision in summary["decisions"]:
        try:
            # Verify audit metadata
            assert decision.staging_tender_id is not None
            assert decision.unique_key is not None
            assert decision.processed_at is not None
            assert decision.policy_version == settings.policy_version
            assert decision.agent_version == settings.agent_version
            assert decision.decision_reason  # Non-empty reason
            assert 0 <= decision.confidence_score <= 1
            
            logger.info(f"âœ“ {decision.unique_key}: Audit trail verified")
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
