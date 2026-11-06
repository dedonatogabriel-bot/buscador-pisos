"""Listado de Zonaprop. Parser sobre HTML estático (fixture real del 2026-11-06) y fuente con Playwright."""

from __future__ import annotations

from collections.abc import Callable

from bs4 import BeautifulSoup, Tag

from scrapers.portales.base import (
    ListingStub,
    SearchQuery,
    parse_amount,
    parse_area,
    parse_rooms,
    slugify,
    within_cap,
)
from scrapers.portales.browser import BlockedError, log, page_fetcher

BASE_URL = "https://www.zonaprop.com.ar"
CARD = "div[data-qa='posting PROPERTY']"


def search_urls(query: SearchQuery, neighborhood: str) -> list[str]:
    """Formato del scraper viejo: /departamentos-alquiler-{barrio}-menos-{N}-pesos[-pagina-{n}].html."""
    base = f"{BASE_URL}/departamentos-alquiler-{slugify(neighborhood)}-menos-{query.max_rent}-pesos"
    return [f"{base}.html"] + [f"{base}-pagina-{n}.html" for n in range(2, query.max_pages + 1)]


def _text(card: Tag, selector: str) -> str:
    el = card.select_one(selector)
    return el.get_text(" ", strip=True) if el else ""


def _parse_card(card: Tag) -> ListingStub | None:
    external_id = str(card.get("data-id") or "").strip()
    link = card.select_one("a[href*='/propiedades/']") or card.select_one("a[data-to-posting]")
    href = str(link.get("href") or "") if link else str(card.get("data-to-posting") or "")
    if not external_id or not href:
        return None

    price_text = _text(card, "[data-qa='POSTING_CARD_PRICE']")
    price, currency = parse_amount(price_text)
    expenses_text = _text(card, "[data-qa='expensas']")
    expenses, exp_currency = parse_amount(expenses_text) if expenses_text else (None, "ARS")

    features = _text(card, "[data-qa='POSTING_CARD_FEATURES']")
    img = card.select_one("img")
    photo = str(img.get("src") or img.get("data-src") or "") or None if img else None
    location = _text(card, "[data-qa='POSTING_CARD_LOCATION']")
    parts = [p.strip() for p in location.split(",") if p.strip()]

    return ListingStub(
        portal="zonaprop",
        external_id=external_id,
        url=href if href.startswith("http") else BASE_URL + href,
        price=price,
        currency=currency,  # type: ignore[arg-type]
        expenses=expenses,
        expenses_currency=exp_currency,  # type: ignore[arg-type]
        area_m2=parse_area(features),
        rooms=parse_rooms(features),
        neighborhood=parts[0] if parts else None,
        main_photo=photo,
    )


def parse_listing_html(html: str) -> list[ListingStub]:
    soup = BeautifulSoup(html, "lxml")
    stubs = (_parse_card(c) for c in soup.select(CARD))
    return [s for s in stubs if s is not None]


class ZonapropSource:
    name = "zonaprop"

    def __init__(self, fetch: Callable[[str], str] | None = None, headless: bool = False) -> None:
        self._fetch = fetch
        self._headless = headless

    def fetch_list(self, query: SearchQuery) -> list[ListingStub]:
        if self._fetch is not None:
            return self._run(self._fetch, query)
        with page_fetcher(headless=self._headless) as fetch:
            return self._run(fetch, query)

    def _run(self, fetch: Callable[[str], str], query: SearchQuery) -> list[ListingStub]:
        found: dict[str, ListingStub] = {}
        for hood in query.neighborhoods:
            for url in search_urls(query, hood):
                html = fetch(url)
                stubs = parse_listing_html(html)
                if not stubs:
                    # Sin tarjetas: o es la última página, o es el desafío de Cloudflare. No se reintenta.
                    if "posting PROPERTY" not in html and "Un momento" in html:
                        raise BlockedError(f"zonaprop: desafío anti-bot en {url}")
                    log(f"zonaprop: {hood} sin más avisos en {url}")
                    break
                for stub in stubs:
                    if within_cap(stub, query):
                        found.setdefault(stub.external_id, stub)
        return list(found.values())
