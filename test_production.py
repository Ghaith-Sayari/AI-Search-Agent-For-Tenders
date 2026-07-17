import os
import logging
from dotenv import load_dotenv

from agents.gatekeeper.classifiers import GatekeeperClassifier, GatekeeperSettings
from pipeline.gatekeeper_pipeline import GatekeeperPipeline

logger = logging.getLogger(__name__)

def _disable_dead_local_proxy() -> None:
    """Prevent broken local proxy env vars from blocking Supabase calls."""
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        value = os.environ.get(key, "")
        if value.strip() in {"http://127.0.0.1:9", "http://localhost:9"}:
            os.environ.pop(key, None)

def test_production_pipeline_first_4_records():
    """
    Test the Gatekeeper pipeline using production table configurations,
    processing only the first 4 records to verify the end-to-end flow.
    """
    # Load environment variables (e.g. Supabase credentials and table names)
    load_dotenv()
    _disable_dead_local_proxy()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)8s] %(message)s",
    )
    
    logger.info("=" * 60)
    logger.info("PRODUCTION GATEKEEPER PIPELINE TEST (First 4 records)")
    logger.info("=" * 60)
    
    # Fetch table names from .env, with defaults as fallback
    source_table = os.environ.get("PROD_SOURCE_TABLE", "raw_tender_staging")
    audit_table = os.environ.get("PROD_AUDIT_TABLE", "gatekeeper_decisions")
    production_table = os.environ.get("PROD_TARGET_TABLE", "production_tender")
    
    logger.info(f"Configuration:")
    logger.info(f"  Source Table:     {source_table}")
    logger.info(f"  Audit Table:      {audit_table}")
    logger.info(f"  Production Table: {production_table}")
    
    # Initialize classifier
    settings = GatekeeperSettings.from_env()
    classifier = GatekeeperClassifier(settings=settings)
    
    # Initialize pipeline
    pipeline = GatekeeperPipeline(
        classifier=classifier,
        source_table=source_table,
        audit_table=audit_table,
        production_table=production_table
    )
    
    # Run the pipeline with limit=4
    logger.info("\n[1] Running GatekeeperPipeline...")
    summary = pipeline.run(limit=4, continue_on_error=False)
    
    # Summary of results
    logger.info("\n[2] Processing Summary:")
    logger.info(f"  Total raw records fetched: {summary['total_fetched']}")
    logger.info(f"  Successfully classified:   {summary['processed']}")
    logger.info(f"  Skipped (deduplicated):    {summary['skipped']}")
    logger.info(f"  Classification errors:     {summary['classification_errors']}")
    logger.info(f"  Approved decisions:        {summary.get('approved_count', 0)}")
    logger.info(f"  Saved to Audit Table:      {summary['saved_audit']}/{summary['processed']}")
    logger.info(f"  Saved to Prod Table:       {summary['saved_prod']}")
    logger.info(f"  Save errors:               {summary['save_errors']}")

    if summary.get("approved_keys"):
        logger.info("\n[3] Approved keys:")
        for key in summary["approved_keys"]:
            logger.info(f"  - {key}")

    if summary.get("published_keys"):
        logger.info("\n[4] Published keys:")
        for key in summary["published_keys"]:
            logger.info(f"  - {key}")

    if summary.get("skipped_keys"):
        logger.info("\n[5] Skipped keys (already in audit):")
        for key in summary["skipped_keys"]:
            logger.info(f"  - {key}")

    if summary.get("classification_error_details"):
        logger.info("\n[6] Classification error details:")
        for err in summary["classification_error_details"]:
            logger.info(f"  - {err}")

    if summary.get("save_error_details"):
        logger.info("\n[7] Save error details:")
        for err in summary["save_error_details"]:
            logger.info(f"  - {err}")

    if summary.get("decisions"):
        logger.info("\n[8] Decision statuses:")
        for d in summary["decisions"]:
            logger.info(
                f"  - {d.unique_key} => {d.status.value}, confidence={d.confidence_score:.2f}, deadline={d.extracted_deadline}"
            )

    # CI guardrails: fail the test if there were hidden classification/save failures.
    assert summary["classification_errors"] == 0, (
        f"Classification errors encountered: {summary.get('classification_error_details')}"
    )
    assert summary["save_errors"] == 0, f"Save errors encountered: {summary.get('save_error_details')}"

    approved_count = summary.get("approved_count", 0)
    if approved_count > 0:
        assert summary["saved_prod"] == approved_count, (
            f"Approved decisions ({approved_count}) did not all publish. "
            f"saved_prod={summary['saved_prod']}, "
            f"published_keys={summary.get('published_keys')}, "
            f"save_error_details={summary.get('save_error_details')}"
        )
    
    logger.info("\n" + "=" * 60)
    logger.info("Test complete.")

if __name__ == "__main__":
    test_production_pipeline_first_4_records()
