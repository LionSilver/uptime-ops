from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class CheckOutcome:
    up: bool
    status_code: int | None
    latency_ms: float
    error: str | None


async def check_url(
    url: str,
    timeout: float = 5.0,
    client: httpx.AsyncClient | None = None,
) -> CheckOutcome:
    """GET the URL. 2xx/3xx count as up. Timeouts and 4xx/5xx count as down."""
    import time

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(follow_redirects=True, timeout=timeout)
    start = time.perf_counter()
    try:
        response = await client.get(url)
        latency_ms = (time.perf_counter() - start) * 1000
        return CheckOutcome(
            up=response.status_code < 400,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
            error=None if response.status_code < 400 else f"HTTP {response.status_code}",
        )
    except Exception as exc:  # noqa: BLE001 — we want every network failure as "down"
        latency_ms = (time.perf_counter() - start) * 1000
        return CheckOutcome(
            up=False,
            status_code=None,
            latency_ms=round(latency_ms, 2),
            error=str(exc) or exc.__class__.__name__,
        )
    finally:
        if owns_client:
            await client.aclose()
