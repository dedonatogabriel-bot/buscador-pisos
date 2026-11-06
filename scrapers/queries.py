"""URLs de búsqueda por portal y barrio, generadas desde config/busqueda.yaml.

Sirven para dar de alta las alertas por email (G-06). Imprimir el documento:
`uv run python -m scrapers.queries > docs/busquedas.md`.

Los filtros de ambientes no van en la URL: ningún formato está verificado, así que se aplican en la
pantalla del portal antes de crear la alerta (ver `docs/busquedas.md`).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from enrich.config import SearchConfig, load_config

RENT_CAP_MARGIN_PCT = 25  # C-09: tope de alquiler +25%
MIN_ROOMS = 2

ARGENPROP = "https://www.argenprop.com/departamentos/alquiler/{slug}/hasta-{cap}-pesos"
ZONAPROP = "https://www.zonaprop.com.ar/departamentos-alquiler-{slug}-menos-{cap}-pesos.html"
MERCADOLIBRE = "https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/{slug}/_PriceRange_0-{cap}_NoIndex_True"

# Estado de verificación de cada formato de URL. Cambiarlo solo con evidencia.
VERIFIED = {
    "argenprop": "verificada el 2026-11-06 (la URL de Palermo devolvió 759 avisos)",
    "zonaprop": "formato del scraper viejo (sep-2026); pendiente de abrir en G-06",
    "mercadolibre": "formato del scraper viejo (verificado el 14/09/2026); pendiente de abrir en G-06",
}


@dataclass(frozen=True)
class PortalSearch:
    portal: str
    neighborhood: str
    url: str


def slugify(text: str) -> str:
    """'Villa Pueyrredón' -> 'villa-pueyrredon'."""
    plain = unicodedata.normalize("NFKD", text)
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def _ars(amount: int) -> str:
    return f"${amount:,}".replace(",", ".")


def rent_cap(cfg: SearchConfig) -> int:
    return cfg.budget.max_rent * (100 + RENT_CAP_MARGIN_PCT) // 100


_TEMPLATES: dict[str, str] = {
    "argenprop": ARGENPROP,
    "zonaprop": ZONAPROP,
    "mercadolibre": MERCADOLIBRE,
}


def build_searches(cfg: SearchConfig) -> list[PortalSearch]:
    cap = rent_cap(cfg)
    return [
        PortalSearch(portal, hood, tpl.format(slug=slugify(hood), cap=cap))
        for portal, tpl in _TEMPLATES.items()
        for hood in cfg.neighborhoods.accepted
    ]


def render_markdown(cfg: SearchConfig) -> str:
    cap = rent_cap(cfg)
    searches = build_searches(cfg)
    lines = [
        "# Búsquedas guardadas para las alertas por email",
        "",
        "> Archivo generado por `uv run python -m scrapers.queries`. No editar a mano: "
        "cambiá `config/busqueda.yaml` y volvé a generarlo.",
        "",
        f"Tope de alquiler: **{_ars(cap)}** "
        f"({_ars(cfg.budget.max_rent)} de la config + {RENT_CAP_MARGIN_PCT}%).",
        f"Barrios: {len(cfg.neighborhoods.accepted)}. Portales: {len(_TEMPLATES)}. "
        f"Total de URLs: {len(searches)}.",
        "",
        "## Paso a paso (G-06)",
        "",
        "1. Creá el Gmail exclusivo de alertas. No lo uses para nada más.",
        "2. Registrate con ese Gmail en Zonaprop, Argenprop y MercadoLibre.",
        "3. Abrí la primera URL de un portal. Confirmá que muestra resultados de ese barrio y que "
        "el precio máximo es el tope de arriba.",
        f"4. Aplicá en la pantalla el filtro de **{MIN_ROOMS} ambientes o más** (no va en la URL).",
        '5. Tocá "Crear alerta" / "Guardar búsqueda" y elegí frecuencia **inmediata**, al email de alertas.',
        "6. Repetí con los demás barrios. Si el portal deja elegir varios barrios en una sola alerta, "
        "agrupalos y ahorrás pasos: lo que importa es cubrir todos los de la lista.",
        "7. Esperá al menos 1 email de alerta por portal y comentalo en el issue #6.",
        "",
        "Si una URL no abre resultados válidos, anotá cuál en el issue #6 en vez de corregirla a mano.",
        "",
        "## Estado de verificación de los formatos",
        "",
        *[f"- **{p}**: {v}" for p, v in VERIFIED.items()],
        "",
    ]
    for portal in _TEMPLATES:
        lines += [f"## {portal.capitalize()}", "", "| Barrio | URL |", "| --- | --- |"]
        lines += [f"| {s.neighborhood} | {s.url} |" for s in searches if s.portal == portal]
        lines.append("")
    return "\n".join(lines)


def main(write: Callable[[str], object] = print, path: Path | None = None) -> None:
    write(render_markdown(load_config(*([path] if path else []))))


if __name__ == "__main__":
    main()
