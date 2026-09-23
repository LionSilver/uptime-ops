import logging

import httpx

from uptime_ops.models import Target

log = logging.getLogger(__name__)


async def notify_discord(webhook_url: str, target: Target, message: str) -> None:
    if not webhook_url:
        log.warning("Discord webhook not configured; skipping alert for %s", target.url)
        return
    payload = {
        "content": message,
        "embeds": [
            {
                "title": f"{target.last_status.upper()}: {target.name}",
                "description": message,
                "color": 15158332 if target.last_status == "down" else 3066993,
                "fields": [
                    {"name": "URL", "value": target.url, "inline": False},
                    {
                        "name": "Failures",
                        "value": str(target.consecutive_failures),
                        "inline": True,
                    },
                    {
                        "name": "Last HTTP",
                        "value": str(target.last_status_code or "n/a"),
                        "inline": True,
                    },
                ],
            }
        ],
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()
