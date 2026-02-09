"""Development web server for the Celery CnC UI."""

from __future__ import annotations

import argparse
import logging
import os
import threading
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Protocol
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from django.conf import settings as django_settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application

from celery_cnc.config import get_settings
from celery_cnc.logging.setup import configure_process_logging

if TYPE_CHECKING:
    from wsgiref.types import WSGIApplication


class _EventLike(Protocol):
    def wait(self, timeout: float | None = None) -> bool:  # pragma: no cover - protocol definition
        ...


class _ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def _build_wsgi_app() -> WSGIApplication:
    application = get_wsgi_application()
    if django_settings.DEBUG:
        application = StaticFilesHandler(application)
    return application


def serve(host: str, port: int, *, shutdown_event: _EventLike | None = None) -> None:
    """Serve the Django WSGI app with a lightweight dev server."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "celery_cnc.web.settings")
    application = _build_wsgi_app()
    httpd = make_server(
        host,
        port,
        application,
        server_class=_ThreadedWSGIServer,
        handler_class=WSGIRequestHandler,
    )
    logger = logging.getLogger(__name__)
    if shutdown_event is not None:

        def _wait_for_shutdown() -> None:
            shutdown_event.wait()
            httpd.shutdown()

        threading.Thread(target=_wait_for_shutdown, daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Dev server interrupted; shutting down.")
    finally:
        httpd.shutdown()
        httpd.server_close()


def main() -> None:
    """Entry point for running the dev server from the CLI."""
    config = get_settings()
    configure_process_logging(config, component="web")
    parser = argparse.ArgumentParser(description="Run the Celery CnC dev web server.")
    parser.add_argument("--host", default=config.web_host)
    parser.add_argument("--port", type=int, default=config.web_port)
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.info("Starting dev server on %s:%s", args.host, args.port)
    serve(args.host, args.port)


if __name__ == "__main__":
    main()
