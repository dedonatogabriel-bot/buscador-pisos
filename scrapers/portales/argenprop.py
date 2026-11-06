"""Listado de Argenprop. Parser sobre HTML estático y fuente con Playwright."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

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

BASE_URL = "https://www.argenprop.com"
CARD = "div.listing__item"


def search_urls(query: SearchQuery, neighborhood: str) -> list[str]:
    """URLs de un barrio, una por página: /departamentos/alquiler/{barrio}/hasta-{N}-pesos?pagina-{n}."""
    base = f"{BASE_URL}/departamentos/alquiler/{slugify(neighborhood)}/hasta-{query.max_rent}-pesos"
    return [base] + [f"{base}?pagina-{n}" for n in range(2, query.max_pages + 1)]


def _text(card: Tag, selector: str) -> str:
    el = card.select_one(selector)
    return el.get_text(" ", strip=True) if el else ""


def _main_photo(card: Tag) -> str | None:
    img = card.select_one("ul.card__photos img")
    if img is None:
        return None
    return str(img.get("src") or img.get("data-src") or "") or None


def _neighborhood(address: str) -> str | None:
    """'Mansilla 3400, Piso 6, Palermo' -> 'Palermo'. Llevarlo al barrio oficial es trabajo de C-21."""
    parts = [p.strip() for p in address.split(",") if p.strip()]
    return parts[-1] if len(parts) > 1 else None


def _parse_card(card: Tag) -> ListingStub | None:
    link = card.select_one("a.card")
    if link is None:
        return None
    external_id = str(link.get("data-item-card") or "").strip()
    href = str(link.get("href") or "")
    if not external_id or not href:
        return None

    price, currency = parse_amount(_text(card, "p.card__price"))
    expenses_text = _text(card, "p.card__expenses")
    expenses, exp_currency = parse_amount(expenses_text) if expenses_text else (None, "ARS")

    features = [li.get_text(" ", strip=True) for li in card.select("ul.card__main-features li")]
    covered = next((f for f in features if "m²" in f and "semi" not in f.lower()), "")
    rooms_text = next((f for f in features if parse_rooms(f) is not None), "")

    return ListingStub(
        portal="argenprop",
        external_id=external_id,
        url=href if href.startswith("http") else BASE_URL + href,
        price=price,
        currency=currency,  # type: ignore[arg-type]
        expenses=expenses,
        expenses_currency=exp_currency,  # type: ignore[arg-type]
        area_m2=parse_area(covered),
        rooms=parse_rooms(rooms_text),
        neighborhood=_neighborhood(_text(card, "p.card__address")),
        main_photo=_main_photo(card),
    )


def parse_listing_html(html: str) -> list[ListingStub]:
    soup = BeautifulSoup(html, "lxml")
    stubs = (_parse_card(c) for c in soup.select(CARD))
    return [s for s in stubs if s is not None]


class ArgenpropSource:
    name = "argenprop"

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
                    if "listing__items" not in html:
                        Path("debug_argenprop.html").write_text(html, encoding="utf-8")
                        raise BlockedError(f"argenprop: sin listado en {url}, posible bloqueo")
                    log(f"argenprop: {hood} sin más avisos en {url}")
                    break
                for stub in stubs:
                    if within_cap(stub, query):
                        found.setdefault(stub.external_id, stub)
        return list(found.values())
