"""Descarga de páginas con Playwright. Solo desde la PC (IP residencial), nunca GitHub Actions."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress

from scrapers.portales.base import polite_sleep


class BlockedError(RuntimeError):
    """El portal devolvió una pantalla anti-bot en vez del listado. No se reintenta."""


@contextmanager
def page_fetcher(headless: bool = False) -> Iterator[Callable[[str], str]]:
    """Devuelve `fetch(url) -> html`. Espera 5-10 s entre llamadas; un contexto nuevo por página."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        first = True

        def fetch(url: str) -> str:
            nonlocal first
            if not first:
                polite_sleep()
            first = False
            ctx = browser.new_context(
                locale="es-AR",
                timezone_id="America/Argentina/Buenos_Aires",
                viewport={"width": 1440, "height": 900},
            )
            try:
                page = ctx.new_page()
                page.goto(url, timeout=60_000, wait_until="domcontentloaded")
                # Algunas páginas nunca quedan "idle": se usa lo que haya cargado.
                with suppress(PlaywrightTimeoutError):
                    page.wait_for_load_state("networkidle", timeout=20_000)
                page.wait_for_timeout(2_000)
                return page.content()
            finally:
                ctx.close()

        try:
            yield fetch
        finally:
            browser.close()


def log(msg: str) -> None:
    print(msg, file=sys.stderr)
