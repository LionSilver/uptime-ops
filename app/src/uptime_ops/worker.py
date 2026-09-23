from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from uptime_ops.alerts import notify_discord
from uptime_ops.checker import check_url
from uptime_ops.config import settings
from uptime_ops.db import SessionLocal, init_db
from uptime_ops.metrics import observe
from uptime_ops.models import Check, Target

logging.basicConfig(level=settings.log_level)
log = logging.getLogger("uptime-ops.worker")


async def process_target(db: Session, target: Target) -> Check:
    outcome = await check_url(target.url, timeout=settings.check_timeout_seconds)
    now = datetime.now(timezone.utc)
    target.last_latency_ms = outcome.latency_ms
    target.last_status_code = outcome.status_code
    target.last_checked_at = now
    observe(target.url, outcome.up, outcome.latency_ms)

    if outcome.up:
        was_down = target.last_status == "down" or target.alerted
        target.last_status = "up"
        target.consecutive_failures = 0
        if was_down and target.alerted:
            target.alerted = False
            await notify_discord(
                settings.discord_webhook_url,
                target,
                f"{target.name} recovered ({target.url})",
            )
    else:
        target.last_status = "down"
        target.consecutive_failures += 1
        if target.consecutive_failures >= settings.failure_threshold and not target.alerted:
            target.alerted = True
            await notify_discord(
                settings.discord_webhook_url,
                target,
                f"{target.name} is down after {target.consecutive_failures} failures: "
                f"{outcome.error or 'unknown error'}",
            )

    row = Check(
        target_id=target.id,
        up=outcome.up,
        status_code=outcome.status_code,
        latency_ms=outcome.latency_ms,
        error=outcome.error,
        checked_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log.info(
        "checked %s -> %s (%sms) failures=%s",
        target.url,
        target.last_status,
        outcome.latency_ms,
        target.consecutive_failures,
    )
    return row


async def run_once(db: Session) -> int:
    targets = db.query(Target).all()
    for target in targets:
        await process_target(db, target)
    return len(targets)


async def main() -> None:
    init_db()
    log.info(
        "worker started interval=%ss threshold=%s",
        settings.check_interval_seconds,
        settings.failure_threshold,
    )
    while True:
        db = SessionLocal()
        try:
            await run_once(db)
        except Exception:
            log.exception("worker loop failed")
        finally:
            db.close()
        await asyncio.sleep(settings.check_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
