import re
from pathlib import Path

import pytest

from enrich.config import load_config
from scrapers.portales import argenprop, zonaprop
from scrapers.portales.base import (
    MAX_DELAY_S,
    MIN_DELAY_S,
    ListingStub,
    SearchQuery,
    parse_amount,
    parse_area,
    parse_rooms,
    polite_sleep,
    slugify,
    within_cap,
)
from scrapers.portales.browser import BlockedError

FIXTURES = Path(__file__).resolve().parent.parent / "scrapers" / "fixtures"
ARGENPROP_HTML = (FIXTURES / "argenprop_listado_palermo.html").read_text(encoding="utf-8")
ZONAPROP_FIXTURE = FIXTURES / "zonaprop_listado.html"


@pytest.fixture
def query() -> SearchQuery:
    return SearchQuery.from_config(load_config(), max_pages=2)


def test_query_applies_25_percent_cap(query: SearchQuery) -> None:
    assert query.max_rent == 875_000  # 700000 de config +25%
    assert "Palermo" in query.neighborhoods


def test_parse_helpers() -> None:
    assert parse_amount("$ 1.300.000") == (1_300_000, "ARS")
    assert parse_amount("USD 950") == (950, "USD")
    assert parse_amount("Consultar") == (None, "ARS")
    assert parse_amount("+ $185.000\nexpensas") == (185_000, "ARS")
    assert parse_area("38  m² cubie.") == 38.0
    assert parse_area("7,80  m² Semicubierta") == 7.8
    assert parse_rooms("Monoam.") == 1
    assert parse_rooms("3 ambientes") == 3
    assert parse_rooms("1 baño") is None
    assert slugify("Villa Pueyrredón") == "villa-pueyrredon"


def test_polite_sleep_stays_in_5_to_10_seconds() -> None:
    slept: list[float] = []
    for _ in range(50):
        polite_sleep(sleep=slept.append)
    assert all(MIN_DELAY_S <= s <= MAX_DELAY_S for s in slept)
    assert len(set(slept)) > 1  # aleatoria, no fija


def test_argenprop_urls(query: SearchQuery) -> None:
    urls = argenprop.search_urls(query, "Villa Crespo")
    assert urls == [
        "https://www.argenprop.com/departamentos/alquiler/villa-crespo/hasta-875000-pesos",
        "https://www.argenprop.com/departamentos/alquiler/villa-crespo/hasta-875000-pesos?pagina-2",
    ]


def test_argenprop_parses_fixture() -> None:
    stubs = argenprop.parse_listing_html(ARGENPROP_HTML)
    assert len(stubs) == 20
    assert len({s.external_id for s in stubs}) == 20
    assert all(s.portal == "argenprop" and s.url.startswith("https://www.argenprop.com/") for s in stubs)
    assert all(s.price and s.main_photo and s.neighborhood for s in stubs)


def test_argenprop_card_fields() -> None:
    by_id = {s.external_id: s for s in argenprop.parse_listing_html(ARGENPROP_HTML)}
    first = by_id["20700057"]
    assert first == ListingStub(
        portal="argenprop",
        external_id="20700057",
        url=first.url,
        price=590_000,
        currency="ARS",
        expenses=105_000,
        area_m2=26.0,
        rooms=1,
        neighborhood="Botánico",
        main_photo=first.main_photo,
    )
    assert first.url.endswith("--20700057")
    # Sin expensas en la tarjeta
    assert by_id["11593670"].expenses is None
    # Dos ambientes y m² con decimales o semicubierta aparte
    assert by_id["16381059"].rooms == 2 and by_id["16381059"].area_m2 == 47.0


def test_argenprop_usd_price_keeps_currency() -> None:
    html = re.sub(
        r'<p class="card__price">.*?</p>',
        '<p class="card__price">USD 590</p>',
        ARGENPROP_HTML,
        count=1,
        flags=re.S,
    )
    stub = argenprop.parse_listing_html(html)[0]  # el reemplazo toca la primera tarjeta
    assert (stub.price, stub.currency) == (590, "USD")


def test_within_cap_skips_only_known_ars_over_cap(query: SearchQuery) -> None:
    cheap = ListingStub(portal="x", external_id="1", url="u", price=875_000)
    dear = ListingStub(portal="x", external_id="2", url="u", price=875_001)
    unknown = ListingStub(portal="x", external_id="3", url="u")
    usd = ListingStub(portal="x", external_id="4", url="u", price=2_000, currency="USD")
    assert [within_cap(s, query) for s in (cheap, dear, unknown, usd)] == [True, False, True, True]


def test_argenprop_source_dedups_and_filters_cap(query: SearchQuery) -> None:
    calls: list[str] = []

    def fake_fetch(url: str) -> str:
        calls.append(url)
        return ARGENPROP_HTML if "?pagina-" not in url else "<div class='listing__items'></div>"

    q = query.model_copy(update={"neighborhoods": ("Palermo", "Caballito")})
    stubs = argenprop.ArgenpropSource(fetch=fake_fetch).fetch_list(q)
    assert len(stubs) == 20  # mismo HTML para los dos barrios: se deduplica por external_id
    assert all(s.price is None or s.price <= q.max_rent for s in stubs)
    # Página 2 vacía corta el barrio, no sigue paginando
    assert len(calls) == 4


def test_argenprop_source_raises_on_block(query: SearchQuery) -> None:
    source = argenprop.ArgenpropSource(fetch=lambda url: "<html><title>Un momento…</title></html>")
    with pytest.raises(BlockedError):
        source.fetch_list(query)


def test_zonaprop_urls(query: SearchQuery) -> None:
    assert zonaprop.search_urls(query, "Palermo") == [
        "https://www.zonaprop.com.ar/departamentos-alquiler-palermo-menos-875000-pesos.html",
        "https://www.zonaprop.com.ar/departamentos-alquiler-palermo-menos-875000-pesos-pagina-2.html",
    ]


def test_zonaprop_source_raises_on_cloudflare(query: SearchQuery) -> None:
    source = zonaprop.ZonapropSource(fetch=lambda url: "<html><title>Un momento…</title></html>")
    with pytest.raises(BlockedError):
        source.fetch_list(query)


def test_zonaprop_parses_fixture() -> None:
    stubs = zonaprop.parse_listing_html(ZONAPROP_FIXTURE.read_text(encoding="utf-8"))
    assert len(stubs) == 30
    assert len({s.external_id for s in stubs}) == 30
    assert all(s.portal == "zonaprop" and s.url.startswith("https://www.zonaprop.com.ar/") for s in stubs)
    assert all(s.price and s.area_m2 and s.rooms and s.main_photo and s.neighborhood for s in stubs)
    first = stubs[0]
    assert (first.external_id, first.price, first.currency, first.expenses) == (
        "60305711",
        790_000,
        "ARS",
        85_000,
    )
    assert (first.area_m2, first.rooms, first.neighborhood) == (34.0, 2, "Las Cañitas")
