import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from scrapers.sources.tendersontime import TendersOnTimeScraper


def main() -> int:
    scraper = TendersOnTimeScraper()

    print("=" * 70)
    print("TENDERS ON TIME - PAGE DIAGNOSTIC")
    print("=" * 70)

    try:
        asyncio.run(scraper.diagnose_page())

        status = "ok"
        error = None

    except Exception as exc:
        status = "error"
        error = f"{type(exc).__name__}: {exc}"

        print("\n[ERROR]")
        print(error)

    # ------------------------------------------------------------
    # Save diagnostic result
    # ------------------------------------------------------------

    out_dir = Path("data") / "raw_scrapes"
    out_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    out_file = (
        out_dir /
        "tendersontime_diagnostic.json"
    )

    payload = {
        "status": status,
        "error": error,
        "timestamp_utc": (
            datetime.now(timezone.utc)
            .isoformat()
        ),
    }

    out_file.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("DIAGNOSTIC TERMINÉ")
    print("=" * 70)

    print(
        f"[INFO] status={status}"
    )

    print(
        f"[INFO] diagnostic JSON={out_file}"
    )

    print(
        "[INFO] screenshot="
        "data/raw_scrapes/tendersontime_debug.png"
    )

    print(
        "[INFO] HTML="
        "data/raw_scrapes/tendersontime_debug.html"
    )

    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())