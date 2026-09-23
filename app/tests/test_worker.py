from unittest.mock import AsyncMock, patch

import pytest

from uptime_ops.checker import CheckOutcome
from uptime_ops.models import Target
from uptime_ops.worker import process_target


@pytest.mark.asyncio
async def test_three_failures_trigger_alert(db):
    target = Target(name="API", url="https://api.example.com/health")
    db.add(target)
    db.commit()
    db.refresh(target)

    down = CheckOutcome(up=False, status_code=500, latency_ms=12.0, error="HTTP 500")
    with (
        patch("uptime_ops.worker.check_url", new=AsyncMock(return_value=down)),
        patch("uptime_ops.worker.notify_discord", new=AsyncMock()) as alert,
        patch("uptime_ops.worker.settings") as settings,
    ):
        settings.failure_threshold = 3
        settings.check_timeout_seconds = 5
        settings.discord_webhook_url = "https://discord.example/webhook"
        await process_target(db, target)
        await process_target(db, target)
        assert alert.await_count == 0
        await process_target(db, target)
        assert alert.await_count == 1
        db.refresh(target)
        assert target.alerted is True
        assert target.consecutive_failures == 3
        assert target.last_status == "down"
