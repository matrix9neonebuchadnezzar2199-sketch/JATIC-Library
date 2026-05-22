"""httpx client with one-time HTTP/2 to HTTP/1.1 fallback."""

from __future__ import annotations

import asyncio
import ssl
from types import TracebackType

import httpx
from loguru import logger

# Process-wide: after fallback, do not retry HTTP/2
_http1_only = False
_fallback_logged = False


def _is_http2_negotiation_error(exc: BaseException) -> bool:
    """Return True when the failure is likely HTTP/2 negotiation related."""
    if isinstance(exc, ssl.SSLError):
        return True
    msg = str(exc).lower()
    markers = ("http2", "h2", "alpn", "protocol", "negotiation")
    return any(m in msg for m in markers)


class JarticHttpClient:
    """Async HTTP client for JARTIC downloads."""

    def __init__(self, timeout_sec: float = 60.0) -> None:
        self._timeout = timeout_sec
        self._client: httpx.AsyncClient | None = None
        self._use_http2 = not _http1_only
        self._fallback_lock = asyncio.Lock()

    async def __aenter__(self) -> JarticHttpClient:
        await self._ensure_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def _ensure_client(self) -> None:
        if self._client is not None:
            return
        global _http1_only
        self._use_http2 = not _http1_only
        self._client = httpx.AsyncClient(
            http2=self._use_http2,
            timeout=self._timeout,
            follow_redirects=True,
        )

    async def _fallback_to_http1(self) -> None:
        global _http1_only, _fallback_logged
        async with self._fallback_lock:
            if not self._use_http2 and self._client is not None:
                return
            if self._client is not None:
                await self._client.aclose()
                self._client = None
            _http1_only = True
            self._use_http2 = False
            if not _fallback_logged:
                logger.warning("HTTP/2 unavailable, fell back to HTTP/1.1")
                _fallback_logged = True
            await self._ensure_client()

    async def head(self, url: str) -> httpx.Response:
        """Send HEAD with optional HTTP/2 fallback."""
        return await self._request("HEAD", url)

    async def get_stream(self, url: str) -> httpx.Response:
        """Send GET for streaming download (caller must aclose the response)."""
        await self._ensure_client()
        assert self._client is not None
        try:
            request = self._client.build_request("GET", url)
            response = await self._client.send(request, stream=True)
            response.raise_for_status()
            return response
        except (httpx.HTTPError, ssl.SSLError, OSError) as exc:
            if self._use_http2 and _is_http2_negotiation_error(exc):
                await self._fallback_to_http1()
                assert self._client is not None
                request = self._client.build_request("GET", url)
                response = await self._client.send(request, stream=True)
                response.raise_for_status()
                return response
            raise

    async def _request(self, method: str, url: str) -> httpx.Response:
        await self._ensure_client()
        assert self._client is not None
        try:
            response = await self._client.request(method, url)
            response.raise_for_status()
            return response
        except (httpx.HTTPError, ssl.SSLError, OSError) as exc:
            if self._use_http2 and _is_http2_negotiation_error(exc):
                await self._fallback_to_http1()
                assert self._client is not None
                response = await self._client.request(method, url)
                response.raise_for_status()
                return response
            raise

    async def aclose(self) -> None:
        """Close the underlying client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def reset_http_fallback_state_for_tests() -> None:
    """Reset module-level fallback flags (tests only)."""
    global _http1_only, _fallback_logged
    _http1_only = False
    _fallback_logged = False
