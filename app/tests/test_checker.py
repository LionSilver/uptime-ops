import httpx
import pytest

from uptime_ops.checker import check_url


@pytest.mark.asyncio
async def test_check_url_up():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="ok")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        outcome = await check_url("https://example.com/health", client=client)
    assert outcome.up is True
    assert outcome.status_code == 200
    assert outcome.error is None


@pytest.mark.asyncio
async def test_check_url_http_error_is_down():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="nope")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        outcome = await check_url("https://example.com/health", client=client)
    assert outcome.up is False
    assert outcome.status_code == 503
    assert "503" in (outcome.error or "")


@pytest.mark.asyncio
async def test_check_url_timeout_is_down():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("took too long")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        outcome = await check_url("https://example.com/health", client=client)
    assert outcome.up is False
    assert outcome.status_code is None
    assert outcome.error
