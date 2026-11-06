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

# Una alerta por portal (camino recomendado). Ninguna de estas tres está verificada: se derivan de los
# formatos de arriba cambiando el barrio por "todos" o por la CABA entera.
ARGENPROP_CABA = "https://www.argenprop.com/departamentos/alquiler/capital-federal/hasta-{cap}-pesos"
ZONAPROP_MULTI = "https://www.zonaprop.com.ar/departamentos-alquiler-{slugs}-menos-{cap}-pesos.html"
MERCADOLIBRE_CABA = "https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal/_PriceRange_0-{cap}_NoIndex_True"

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


def one_alert_urls(cfg: SearchConfig) -> dict[str, str]:
    """Una URL por portal: Zonaprop con todos los barrios, los otros dos con CABA entera."""
    cap = rent_cap(cfg)
    slugs = "-".join(slugify(h) for h in cfg.neighborhoods.accepted)
    return {
        "zonaprop": ZONAPROP_MULTI.format(slugs=slugs, cap=cap),
        "argenprop": ARGENPROP_CABA.format(cap=cap),
        "mercadolibre": MERCADOLIBRE_CABA.format(cap=cap),
    }


def render_markdown(cfg: SearchConfig) -> str:
    cap = rent_cap(cfg)
    searches = build_searches(cfg)
    hoods = cfg.neighborhoods.accepted
    one = one_alert_urls(cfg)
    lines = [
        "# Búsquedas guardadas para las alertas por email",
        "",
        "> Archivo generado por `uv run python -m scrapers.queries`. No editar a mano: "
        "cambiá `config/busqueda.yaml` y volvé a generarlo.",
        "",
        f"Tope de alquiler: **{_ars(cap)}** "
        f"({_ars(cfg.budget.max_rent)} de la config + {RENT_CAP_MARGIN_PCT}%).",
        f"Ambientes: **{MIN_ROOMS} o más**. Alquiler tradicional.",
        "",
        "## Qué hacer: una alerta por portal",
        "",
        "No hace falta una alerta por barrio. Con **una alerta inmediata por portal** alcanza.",
        "",
        "1. Creá el Gmail exclusivo de alertas. No lo uses para nada más.",
        "2. Registrate con ese Gmail en Zonaprop, Argenprop y MercadoLibre.",
        "3. En cada portal abrí la URL de la tabla de abajo.",
        "4. Si no muestra resultados, tocá **Departamentos** + **Alquiler** + **Capital Federal** a mano "
        "y anotá en el issue #6 qué URL falló.",
        f"5. En los filtros marcá **todos los barrios de la lista** (o dejá CABA entera), precio máximo "
        f"**{_ars(cap)}** y **{MIN_ROOMS} ambientes o más**.",
        '6. Tocá "Crear alerta" / "Guardar búsqueda", frecuencia **inmediata**, al Gmail de alertas.',
        "7. Esperá al menos 1 email por portal y comentalo en el issue #6.",
        "",
        "| Portal | URL de partida | Qué cubre |",
        "| --- | --- | --- |",
        f"| Zonaprop | {one['zonaprop']} | Todos los barrios de la lista |",
        f"| Argenprop | {one['argenprop']} | CABA entera (marcá los barrios en el filtro si podés) |",
        f"| MercadoLibre | {one['mercadolibre']} | CABA entera (marcá los barrios en el filtro si podés) |",
        "",
        "Si el portal te manda avisos de barrios que no están en la lista, no pasa nada: el sistema "
        "los descarta al procesar el email.",
        "",
        "### Barrios a marcar",
        "",
        ", ".join(hoods) + ".",
        "",
        "## Estado de verificación",
        "",
        "Las URLs de arriba **no están verificadas**: se derivaron de los formatos de abajo.",
        "",
        *[f"- **{p}** (formato por barrio): {v}" for p, v in VERIFIED.items()],
        "",
        "## Plan B: una alerta por barrio",
        "",
        "Solo si un portal no te deja elegir varios barrios ni CABA entera. "
        f"Son {len(searches)} URLs en total ({len(hoods)} por portal). Mismos pasos 5 a 7, repetidos.",
        "",
    ]
    for portal in _TEMPLATES:
        lines += [f"### {portal.capitalize()}", "", "| Barrio | URL |", "| --- | --- |"]
        lines += [f"| {s.neighborhood} | {s.url} |" for s in searches if s.portal == portal]
        lines.append("")
    return "\n".join(lines)


def main(write: Callable[[str], object] = print, path: Path | None = None) -> None:
    write(render_markdown(load_config(*([path] if path else []))))


if __name__ == "__main__":
    main()
