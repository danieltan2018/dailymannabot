"""Minimal Telegram Bot API client — just enough to post a message."""

import errno
import http.client
import json
import logging
import os
import socket
import time
import urllib.error
import urllib.request

TELEGRAM_MAX_LENGTH = 4096
CONNECT_TIMEOUT = 3
REQUEST_TIMEOUT = 10
CONNECT_ATTEMPTS = 3
logger = logging.getLogger(__name__)


class _RetryingHTTPSConnection(http.client.HTTPSConnection):
    """Retry connection setup only, before any Telegram request bytes are sent."""

    def connect(self):
        request_timeout = self.timeout
        try:
            self.timeout = CONNECT_TIMEOUT
            for attempt in range(CONNECT_ATTEMPTS):
                try:
                    super().connect()
                    self.sock.settimeout(request_timeout)
                    return
                except OSError as error:
                    # Preserve HTTPConnection's request state and buffered body;
                    # close() would reset them in the middle of request().
                    if self.sock is not None:
                        self.sock.close()
                        self.sock = None
                    if isinstance(error, socket.gaierror):
                        transient = error.errno == socket.EAI_AGAIN
                    else:
                        transient = isinstance(error, (socket.timeout, TimeoutError)) or error.errno in {
                            errno.EADDRNOTAVAIL, errno.ECONNREFUSED,
                            errno.ECONNRESET, errno.ETIMEDOUT,
                            errno.ENETUNREACH, errno.EHOSTUNREACH,
                        }
                    if not transient or attempt == CONNECT_ATTEMPTS - 1:
                        raise
                    delay = 0.5 * (2 ** attempt)
                    logger.warning("Telegram connection failed; retrying connection (attempt %s/%s, errno=%s)",
                                   attempt + 2, CONNECT_ATTEMPTS, error.errno)
                    time.sleep(delay)
        finally:
            self.timeout = request_timeout


class _RetryingHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
        return self.do_open(_RetryingHTTPSConnection, request, context=self._context)


def send_message(chat_id: str, text: str, token: str = None, **options) -> dict:
    """POST once, retrying transient connection setup failures before sending.

    Never retry request writes, response reads, or HTTP/API errors: Telegram
    may already have posted the message if the response is lost.
    """
    token = token or os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is not set")
    body = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        **options,
    }
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        opener = urllib.request.build_opener(_RetryingHTTPSHandler())
        with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
            result = json.load(response)
    except urllib.error.HTTPError as e:
        # Telegram returns 4xx with a JSON body explaining what was wrong.
        raise RuntimeError(f"Telegram API error {e.code}: {e.read().decode('utf-8', 'replace')}") from e
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API returned failure: {result}")
    return result
