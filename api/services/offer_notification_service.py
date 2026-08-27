"""Offer email notification queue processor."""

from __future__ import annotations

import hashlib
import logging
import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any

from db.client import get_client

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, str(default))).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso() -> str:
    return _utc_now().isoformat()


class OfferNotificationService:
    """Processes queued offer-notification events and sends digest emails."""

    EVENT_KEY = "valid_offers_score_gt_70"

    def __init__(self) -> None:
        self._client = None
        self.enabled = _env_bool("OFFER_EMAIL_NOTIFICATIONS_ENABLED", False)
        self.smtp_host = str(os.getenv("OFFER_EMAIL_SMTP_HOST") or "").strip()
        self.smtp_port = int(os.getenv("OFFER_EMAIL_SMTP_PORT", "587"))
        self.smtp_user = str(os.getenv("OFFER_EMAIL_SMTP_USER") or "").strip()
        self.smtp_password = str(os.getenv("OFFER_EMAIL_SMTP_PASSWORD") or "").strip()
        self.smtp_starttls = _env_bool("OFFER_EMAIL_SMTP_STARTTLS", True)
        self.from_email = str(os.getenv("OFFER_EMAIL_FROM") or "").strip()
        self.to_emails = [
            email.strip()
            for email in str(os.getenv("OFFER_EMAIL_TO") or "").split(",")
            if email.strip()
        ]
        self.cooldown_minutes = max(0, int(os.getenv("OFFER_EMAIL_COOLDOWN_MINUTES", "30")))
        self.max_retries = max(1, int(os.getenv("OFFER_EMAIL_MAX_RETRIES", "3")))

    @property
    def client(self):  # type: ignore[no-untyped-def]
        if self._client is None:
            self._client = get_client()
        return self._client

    def is_enabled(self) -> bool:
        if not self.enabled:
            return False
        required = [
            self.smtp_host,
            self.from_email,
            ",".join(self.to_emails),
        ]
        return all(bool(v) for v in required)

    def process_pending_notifications(self, batch_size: int = 50) -> dict[str, Any]:
        if not self.is_enabled():
            return {"status": "disabled"}

        pending = (
            self.client.table("offer_notification_queue")
            .select("*")
            .eq("event_key", self.EVENT_KEY)
            .eq("status", "pending")
            .order("created_at")
            .limit(max(1, min(batch_size, 200)))
            .execute()
            .data
            or []
        )
        if not pending:
            return {"status": "idle", "queued": 0}

        ids = [str(row["id"]) for row in pending if row.get("id")]
        if not ids:
            return {"status": "idle", "queued": 0}

        now_iso = _utc_iso()
        _ = (
            self.client.table("offer_notification_queue")
            .update({"status": "processing", "processing_started_at": now_iso})
            .in_("id", ids)
            .execute()
        )

        offers = self._fetch_eligible_offers()
        snapshot_hash = self._snapshot_hash(offers)
        state = self._get_state()

        send_allowed, skip_reason = self._should_send(offers=offers, snapshot_hash=snapshot_hash, state=state)
        if not send_allowed:
            self._mark_sent(ids, provider_response=f"skipped:{skip_reason}")
            return {"status": "skipped", "queued": len(ids), "reason": skip_reason}

        try:
            provider_resp = self._send_email(offers)
            self._upsert_state(
                {
                    "event_key": self.EVENT_KEY,
                    "last_snapshot_hash": snapshot_hash,
                    "last_sent_count": len(offers),
                    "last_sent_at": now_iso,
                    "updated_at": now_iso,
                }
            )
            self._mark_sent(ids, provider_response=provider_resp)
            return {"status": "sent", "queued": len(ids), "eligible_count": len(offers)}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Offer notification email send failed: %s", exc)
            self._mark_failed_with_retries(pending, str(exc))
            return {"status": "failed", "queued": len(ids), "error": str(exc)}

    def _fetch_eligible_offers(self) -> list[dict[str, Any]]:
        today = _utc_now().date().isoformat()
        rows = (
            self.client.table("analyzed_tender")
            .select("id,title,total_score,deadline,url,source,processed_at")
            .gte("deadline", today)
            .gt("total_score", 70)
            .order("total_score", desc=True)
            .order("processed_at", desc=True)
            .execute()
            .data
            or []
        )
        return [r for r in rows if r.get("id")]

    def _snapshot_hash(self, offers: list[dict[str, Any]]) -> str:
        normalized = [
            {
                "id": str(r.get("id") or ""),
                "title": str(r.get("title") or ""),
                "total_score": float(r.get("total_score") or 0.0),
                "deadline": str(r.get("deadline") or ""),
            }
            for r in offers
        ]
        payload = repr(normalized).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _get_state(self) -> dict[str, Any]:
        rows = (
            self.client.table("offer_notification_state")
            .select("*")
            .eq("event_key", self.EVENT_KEY)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else {}

    def _should_send(
        self,
        *,
        offers: list[dict[str, Any]],
        snapshot_hash: str,
        state: dict[str, Any],
    ) -> tuple[bool, str]:
        if not offers:
            return False, "no_eligible_offers"

        last_hash = str(state.get("last_snapshot_hash") or "")
        if last_hash and last_hash == snapshot_hash:
            return False, "snapshot_unchanged"

        last_sent_raw = state.get("last_sent_at")
        if not last_sent_raw or self.cooldown_minutes <= 0:
            return True, ""

        try:
            last_sent = datetime.fromisoformat(str(last_sent_raw).replace("Z", "+00:00"))
            if last_sent.tzinfo is None:
                last_sent = last_sent.replace(tzinfo=timezone.utc)
        except Exception:  # noqa: BLE001
            return True, ""

        if _utc_now() < last_sent + timedelta(minutes=self.cooldown_minutes):
            return False, "cooldown_active"
        return True, ""

    def _build_email(self, offers: list[dict[str, Any]]) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = f"Valid offers alert: {len(offers)} offer(s) with score > 70"
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails)

        lines = [
            "The following offers are currently valid and have score > 70:",
            "",
        ]
        for row in offers:
            title = str(row.get("title") or "Untitled offer")
            score = float(row.get("total_score") or 0.0)
            deadline = str(row.get("deadline") or "N/A")
            lines.append(f"- {title} (score: {score:.2f}, deadline: {deadline})")

        lines.extend(
            [
                "",
                f"Generated at: {_utc_iso()}",
            ]
        )
        msg.set_content("\n".join(lines))
        return msg

    def _send_email(self, offers: list[dict[str, Any]]) -> str:
        msg = self._build_email(offers)
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
            if self.smtp_starttls:
                server.starttls()
            if self.smtp_user:
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
        return f"smtp:{self.smtp_host}:{self.smtp_port}"

    def _mark_sent(self, ids: list[str], *, provider_response: str) -> None:
        now_iso = _utc_iso()
        _ = (
            self.client.table("offer_notification_queue")
            .update(
                {
                    "status": "sent",
                    "processed_at": now_iso,
                    "provider_response": provider_response,
                    "last_error": None,
                }
            )
            .in_("id", ids)
            .execute()
        )

    def _mark_failed_with_retries(self, rows: list[dict[str, Any]], error_message: str) -> None:
        now_iso = _utc_iso()
        for row in rows:
            row_id = row.get("id")
            if not row_id:
                continue
            attempts = int(row.get("attempts") or 0) + 1
            exhausted = attempts >= self.max_retries
            payload = {
                "attempts": attempts,
                "status": "failed" if exhausted else "pending",
                "last_error": error_message[:3000],
                "processed_at": now_iso if exhausted else None,
                "processing_started_at": None if not exhausted else row.get("processing_started_at"),
            }
            _ = (
                self.client.table("offer_notification_queue")
                .update(payload)
                .eq("id", str(row_id))
                .execute()
            )

    def _upsert_state(self, payload: dict[str, Any]) -> None:
        _ = (
            self.client.table("offer_notification_state")
            .upsert(payload, on_conflict="event_key")
            .execute()
        )
