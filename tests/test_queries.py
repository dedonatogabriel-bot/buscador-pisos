from pathlib import Path

import pytest

from enrich.config import load_config
from scrapers import queries

DOC = Path(__file__).resolve().parent.parent / "docs" / "busquedas.md"


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_cap_is_config_rent_plus_25_percent(cfg) -> None:
    assert queries.rent_cap(cfg) == 875_000


def test_one_url_per_portal_and_neighborhood(cfg) -> None:
    searches = queries.build_searches(cfg)
    assert len(searches) == 3 * len(cfg.neighborhoods.accepted)
    assert len({s.url for s in searches}) == len(searches)


def test_known_urls(cfg) -> None:
    urls = {(s.portal, s.neighborhood): s.url for s in queries.build_searches(cfg)}
    assert urls[("argenprop", "Palermo")] == (
        "https://www.argenprop.com/departamentos/alquiler/palermo/hasta-875000-pesos"
    )
    assert urls[("zonaprop", "Villa Pueyrredón")] == (
        "https://www.zonaprop.com.ar/departamentos-alquiler-villa-pueyrredon-menos-875000-pesos.html"
    )
    assert urls[("mercadolibre", "Núñez")].endswith(
        "/capital-federal/nunez/_PriceRange_0-875000_NoIndex_True"
    )


def test_slugs_are_ascii_without_double_dashes(cfg) -> None:
    for s in queries.build_searches(cfg):
        slug_part = s.url.lower()
        assert "--" not in slug_part.split("://", 1)[1]
        assert s.url.isascii()


def test_one_alert_per_portal(cfg) -> None:
    urls = queries.one_alert_urls(cfg)
    assert set(urls) == {"zonaprop", "argenprop", "mercadolibre"}
    assert all("875000" in u and u.isascii() for u in urls.values())
    # Zonaprop lleva todos los barrios aceptados
    for hood in cfg.neighborhoods.accepted:
        assert queries.slugify(hood) in urls["zonaprop"]


def test_committed_doc_is_up_to_date(cfg) -> None:
    assert DOC.read_text(encoding="utf-8").strip() == queries.render_markdown(cfg).strip()
