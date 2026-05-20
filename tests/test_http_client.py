"""Tests for HTTP client."""

import httpx
import pytest

from jatic_library.core.http_client import (
    JarticHttpClient,
    _is_http2_negotiation_error,
    reset_http_fallback_state_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_http() -> None:
    reset_http_fallback_state_for_tests()


def test_http2_error_detection() -> None:
    assert _is_http2_negotiation_error(RuntimeError("HTTP/2 negotiation failed")) is True
    assert _is_http2_negotiation_error(RuntimeError("connection reset")) is False


@pytest.mark.asyncio
async def test_head_success() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "HEAD"
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    client = JarticHttpClient(timeout_sec=5.0)
    client._client = httpx.AsyncClient(transport=transport, http2=False)
    try:
        response = await client.head("https://example.test/file.zip")
    finally:
        await client.aclose()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_stream_get() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        return httpx.Response(200, content=b"data")

    transport = httpx.MockTransport(handler)
    client = JarticHttpClient(timeout_sec=5.0)
    client._client = httpx.AsyncClient(transport=transport, http2=False)
    try:
        response = await client.get_stream("https://example.test/file.zip")
        body = await response.aread()
    finally:
        await response.aclose()
        await client.aclose()
    assert body == b"data"
