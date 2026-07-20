import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime, timezone
import time

from agents.gatekeeper.classifiers import GatekeeperClassifier, GatekeeperSettings
from agents.gatekeeper.audit.dead_letter_repository import GatekeeperDeadLetterRepository
from agents.gatekeeper.audit.decision_repository import GatekeeperDecisionRepository
from agents.gatekeeper.observability import configure_langsmith, traceable
from agents.gatekeeper.schemas import RawTenderStagingRecord, GatekeeperStatus
from agents.gatekeeper.routing import ProductionTenderPublisher
from db.client import get_client

logger = logging.getLogger(__name__)

class GatekeeperPipeline:
    def __init__(
        self,
        classifier: GatekeeperClassifier,
        source_table: str,
        audit_table: str,
        production_table: Optional[str] = None,
        dead_letter_table: str = "gatekeeper_dead_letter",
        enable_dead_letter: bool = True,
        max_workers: int = 4,
        classify_max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
    ):
        """
        Initialize the Gatekeeper Pipeline.
        
        Args:
            classifier: An instance of GatekeeperClassifier.
            source_table: The table to fetch raw records from (e.g., 'raw_test_db' or 'raw_tender_staging').
            audit_table: The table to save all decisions to (e.g., 'clean_test_db' or 'gatekeeper_decisions').
            production_table: The table to save APPROVED records to (e.g., None for tests, 'production_tender' for prod).
        """
        self.classifier = classifier
        self.source_table = source_table
        self.audit_table = audit_table
        self.production_table = production_table
        self.dead_letter_table = dead_letter_table
        self.enable_dead_letter = enable_dead_letter
        self.max_workers = max(1, max_workers)
        self.classify_max_retries = max(1, classify_max_retries)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        configure_langsmith(self.classifier.settings)
        
        self.audit_repository = GatekeeperDecisionRepository(table_name=audit_table)
        self.dead_letter_repository = (
            GatekeeperDeadLetterRepository(table_name=dead_letter_table)
            if enable_dead_letter
            else None
        )
        self.production_publisher = (
            ProductionTenderPublisher(table_name=production_table)
            if production_table
            else None
        )
        self.client = get_client()

    def get_processed_keys(self) -> set[tuple[str, str]]:
        """Fetch all processed (unique_key, policy_version) tuples from the audit table."""
        response = self.client.table(self.audit_table).select("unique_key,policy_version").execute()
        if not response.data:
            return set()
        return {
            (row.get("unique_key"), row.get("policy_version"))
            for row in response.data
            if row.get("unique_key") and row.get("policy_version")
        }

    def fetch_raw_records(self, limit: Optional[int] = None, offset: int = 0) -> List[dict]:
        """Fetch raw records from the source table."""
        query = self.client.table(self.source_table).select("*").order("created_at", desc=True)
        if limit is not None:
            query = query.range(offset, offset + limit - 1)
            
        response = query.execute()
        if not response.data:
            return []
        return response.data

    @staticmethod
    def _build_record(raw_data: dict[str, Any], unique_key: str) -> RawTenderStagingRecord:
        id_val = raw_data.get("id")
        return RawTenderStagingRecord(
            id=UUID(str(id_val)) if id_val else UUID(int=0),
            unique_key=unique_key,
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

    def _classify_with_retry(self, record: RawTenderStagingRecord):
        last_error = None
        for attempt in range(1, self.classify_max_retries + 1):
            try:
                return self.classifier.classify(record)
            except Exception as exc:
                last_error = exc
                if attempt >= self.classify_max_retries:
                    break
                sleep_for = self.retry_backoff_seconds * (2 ** (attempt - 1))
                logger.warning(
                    "Classification failed for %s (attempt %d/%d): %s. Retrying in %.1fs",
                    record.unique_key,
                    attempt,
                    self.classify_max_retries,
                    exc,
                    sleep_for,
                )
                if sleep_for > 0:
                    time.sleep(sleep_for)

        raise last_error

    def _route_to_dead_letter(
        self,
        *,
        unique_key: str,
        raw_data: dict[str, Any],
        stage: str,
        error_type: str,
        error_message: str,
        retry_count: int,
    ) -> None:
        if not self.dead_letter_repository:
            return
        payload = {
            "unique_key": unique_key,
            "policy_version": self.classifier.settings.policy_version,
            "stage": stage,
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": retry_count,
            "source_table": self.source_table,
            "raw_payload": raw_data,
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
        }
        self.dead_letter_repository.save(payload)

    @traceable(name="gatekeeper.pipeline.run", run_type="chain")
    def run(self, limit: Optional[int] = None, continue_on_error: bool = True) -> Dict[str, Any]:
        """
        Run the gatekeeper pipeline.
        
        Args:
            limit: Maximum number of raw records to fetch.
            continue_on_error: If True, log errors and continue. If False, raise exceptions immediately.
            
        Returns:
            A dictionary containing summary statistics of the run.
        """
        logger.info(f"Starting GatekeeperPipeline run. Source: {self.source_table}, Audit: {self.audit_table}, Prod: {self.production_table}")
        
        # Step 1: Pre-Filtering (Skip already-audited records)
        processed_keys = self.get_processed_keys()

        # Fetch enough rows so that `limit` applies to unprocessed rows, not raw fetched rows.
        if limit is None:
            raw_records = self.fetch_raw_records(limit=None)
        else:
            raw_records = []
            page_size = max(limit, 50)
            offset = 0
            while len(raw_records) < limit:
                page = self.fetch_raw_records(limit=page_size, offset=offset)
                if not page:
                    break
                raw_records.extend(page)
                offset += page_size

        if not raw_records:
            logger.info(f"No records found in {self.source_table}.")
            return {"total_fetched": 0, "processed": 0, "skipped": 0, "errors": 0, "decisions": []}

        # Pre-filter down to unprocessed rows and then enforce limit.
        unprocessed_records = []
        skipped_keys = []
        for r in raw_records:
            key = r.get("unique_key")
            key_tuple = (key, self.classifier.settings.policy_version)
            if key and key_tuple in processed_keys:
                skipped_keys.append(key)
                continue
            unprocessed_records.append(r)
            if limit is not None and len(unprocessed_records) >= limit:
                break
            
        skipped_count = len(skipped_keys)
        
        logger.info(
            f"Found {len(processed_keys)} existing decisions. "
            f"Processing {len(unprocessed_records)} new records. "
            f"Skipping {skipped_count} already-processed records."
        )
        
        # Step 2: Processing & Routing
        decisions = []
        errors = []
        saved_audit_count = 0
        saved_prod_count = 0
        save_errors = []
        approved_keys = []
        published_keys = []
        dlq_count = 0
        dlq_errors = []

        prepared_records = []
        for i, raw_data in enumerate(unprocessed_records, 1):
            unique_key = raw_data.get("unique_key", f"raw-{i}")
            try:
                prepared_records.append((i, unique_key, raw_data, self._build_record(raw_data, unique_key)))
            except Exception as e:
                if not continue_on_error:
                    raise
                errors.append({
                    "index": i,
                    "unique_key": unique_key,
                    "error": str(e),
                    "error_type": type(e).__name__,
                })
                logger.error(f"  [{i:3d}/{len(unprocessed_records)}] {unique_key:30s} -> ERROR: {type(e).__name__}: {e}")

        classification_results = []
        if self.max_workers == 1 or len(prepared_records) <= 1:
            for i, unique_key, raw_data, record in prepared_records:
                try:
                    classification_results.append((i, unique_key, raw_data, record, self._classify_with_retry(record)))
                except Exception as e:
                    classification_results.append((i, unique_key, raw_data, record, e))
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._classify_with_retry, record): (i, unique_key, raw_data, record)
                    for i, unique_key, raw_data, record in prepared_records
                }
                for future in as_completed(futures):
                    i, unique_key, raw_data, record = futures[future]
                    try:
                        decision = future.result()
                        classification_results.append((i, unique_key, raw_data, record, decision))
                    except Exception as e:
                        classification_results.append((i, unique_key, raw_data, record, e))

        classification_results.sort(key=lambda row: row[0])

        for i, unique_key, raw_data, record, outcome in classification_results:
            if isinstance(outcome, Exception):
                errors.append({
                    "index": i,
                    "unique_key": unique_key,
                    "error": str(outcome),
                    "error_type": type(outcome).__name__,
                })
                logger.error(f"  [{i:3d}/{len(unprocessed_records)}] {unique_key:30s} -> ERROR: {type(outcome).__name__}: {outcome}")
                try:
                    self._route_to_dead_letter(
                        unique_key=unique_key,
                        raw_data=raw_data,
                        stage="classification_exception",
                        error_type=type(outcome).__name__,
                        error_message=str(outcome),
                        retry_count=self.classify_max_retries,
                    )
                    dlq_count += 1
                except Exception as dlq_err:
                    dlq_errors.append({"unique_key": unique_key, "error": str(dlq_err)})
                    logger.error(f"  X Failed to route {unique_key} to dead letter table: {dlq_err}")
                continue

            decision = outcome
            decisions.append(decision)
            if decision.status == GatekeeperStatus.FAILED:
                try:
                    self._route_to_dead_letter(
                        unique_key=unique_key,
                        raw_data=raw_data,
                        stage="classification_failed_decision",
                        error_type="GatekeeperFailedDecision",
                        error_message=decision.decision_reason,
                        retry_count=self.classify_max_retries,
                    )
                    dlq_count += 1
                except Exception as dlq_err:
                    dlq_errors.append({"unique_key": unique_key, "error": str(dlq_err)})
                    logger.error(f"  X Failed to route {unique_key} to dead letter table: {dlq_err}")
            if decision.status == GatekeeperStatus.APPROVED:
                approved_keys.append(unique_key)

            logger.info(
                f"  [{i:3d}/{len(unprocessed_records)}] {record.unique_key:30s} -> "
                f"{decision.status.value:15s} (confidence: {decision.confidence_score:.2f})"
            )

            # 3. Save to Audit Table
            saved_audit_row = None
            try:
                saved_audit_row = self.audit_repository.save(decision)
                saved_audit_count += 1
            except Exception as save_err:
                if not continue_on_error:
                    raise
                save_errors.append({"unique_key": unique_key, "error": str(save_err)})
                logger.error(f"  X Failed to save audit decision for {unique_key}: {save_err}")

            # 4. Conditionally Route to Production
            if self.production_table and decision.status == GatekeeperStatus.APPROVED:
                try:
                    gatekeeper_decision_id = (
                        saved_audit_row.get("id")
                        if isinstance(saved_audit_row, dict)
                        else None
                    )
                    self.production_publisher.publish(
                        record=record,
                        decision=decision,
                        gatekeeper_decision_id=gatekeeper_decision_id,
                    )
                    saved_prod_count += 1
                    published_keys.append(unique_key)
                    logger.info(f"  V Saved APPROVED tender to {self.production_table} for {unique_key}")
                except Exception as prod_err:
                    if not continue_on_error:
                        raise
                    save_errors.append({"unique_key": unique_key, "error": f"Prod insert failed: {prod_err}"})
                    logger.error(f"  X Failed to save prod tender for {unique_key}: {prod_err}")

        summary = {
            "total_fetched": len(raw_records),
            "skipped": skipped_count,
            "skipped_keys": skipped_keys,
            "processed": len(decisions),
            "classification_errors": len(errors),
            "classification_error_details": errors,
            "approved_count": len(approved_keys),
            "approved_keys": approved_keys,
            "saved_audit": saved_audit_count,
            "saved_prod": saved_prod_count,
            "published_keys": published_keys,
            "save_errors": len(save_errors),
            "save_error_details": save_errors,
            "dlq_count": dlq_count,
            "dlq_errors": dlq_errors,
            "decisions": decisions
        }
        return summary
