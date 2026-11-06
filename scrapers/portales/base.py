"""Interfaz común de los scrapers de listado de portales."""

from __future__ import annotations

import random
import re
import time
import unicodedata
from collections.abc import Callable
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from enrich.config import SearchConfig

# CLAUDE.md: máximo 1 página cada 5-10 s por portal, con espera aleatoria.
MIN_DELAY_S = 5.0
MAX_DELAY_S = 10.0
# C-05: las URLs llevan el tope de alquiler +25%; el filtro duro fino se aplica después.
RENT_CAP_MARGIN_PCT = 25


class ListingStub(BaseModel):
    """Lo que se ve en la tarjeta del listado. La ficha completa es C-11."""

    model_config = ConfigDict(frozen=True)

    portal: str
    external_id: str
    url: str
    price: int | None = Field(default=None, ge=0)
    currency: Literal["ARS", "USD"] = "ARS"
    expenses: int | None = Field(default=None, ge=0)
    expenses_currency: Literal["ARS", "USD"] = "ARS"
    area_m2: float | None = Field(default=None, gt=0)
    rooms: int | None = Field(default=None, ge=1)
    neighborhood: str | None = None
    main_photo: str | None = None


class SearchQuery(BaseModel):
    """Búsqueda derivada de config/busqueda.yaml."""

    model_config = ConfigDict(frozen=True)

    neighborhoods: tuple[str, ...]
    max_rent: int = Field(gt=0)
    currency: Literal["ARS", "USD"] = "ARS"
    max_pages: int = Field(default=3, ge=1)

    @classmethod
    def from_config(cls, cfg: SearchConfig, max_pages: int = 3) -> SearchQuery:
        cap = cfg.budget.max_rent * (100 + RENT_CAP_MARGIN_PCT) // 100
        return cls(
            neighborhoods=tuple(cfg.neighborhoods.accepted),
            max_rent=cap,
            currency=cfg.budget.currency,
            max_pages=max_pages,
        )


class ListingSource(Protocol):
    name: str

    def fetch_list(self, query: SearchQuery) -> list[ListingStub]: ...


def slugify(text: str) -> str:
    """'Villa Pueyrredón' -> 'villa-pueyrredon'."""
    plain = unicodedata.normalize("NFKD", text)
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def parse_amount(text: str | None) -> tuple[int | None, str]:
    """'$ 1.300.000' -> (1300000, 'ARS'); 'USD 950' -> (950, 'USD'); 'Consultar' -> (None, 'ARS')."""
    if not text:
        return None, "ARS"
    match = re.search(r"\d[\d.,\s]*", text)
    if not match:
        return None, "ARS"
    digits = re.sub(r"\D", "", match.group())
    currency = "USD" if re.search(r"u\$s|usd|d[oó]lar", text, re.I) else "ARS"
    return (int(digits) if digits else None), currency


def parse_area(text: str) -> float | None:
    """'38  m² cubie.' -> 38.0; '7,80 m²' -> 7.8."""
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*m", text)
    return float(match.group(1).replace(",", ".")) if match else None


def parse_rooms(text: str) -> int | None:
    """'3 ambientes' -> 3; 'Monoam.' -> 1."""
    if re.search(r"monoam", text, re.I):
        return 1
    match = re.search(r"(\d+)\s*amb", text, re.I)
    return int(match.group(1)) if match else None


def within_cap(stub: ListingStub, query: SearchQuery) -> bool:
    """Descarta lo que supera el tope. Sin precio o en otra moneda se deja pasar (decide C-15)."""
    if stub.price is None or stub.currency != query.currency:
        return True
    return stub.price <= query.max_rent


def polite_sleep(
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
) -> float:
    """Espera aleatoria de 5 a 10 s entre páginas del mismo portal."""
    delay = (rng or random).uniform(MIN_DELAY_S, MAX_DELAY_S)
    sleep(delay)
    return delay
