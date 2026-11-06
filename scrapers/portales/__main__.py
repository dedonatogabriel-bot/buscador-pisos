"""Corrida real desde la PC: `uv run python -m scrapers.portales argenprop --barrios Palermo --paginas 2`.

Imprime los stubs en JSON (uno por línea). El envío a Supabase es C-07.
"""

from __future__ import annotations

import argparse
import sys

from enrich.config import load_config
from scrapers.portales.argenprop import ArgenpropSource
from scrapers.portales.base import ListingSource, SearchQuery
from scrapers.portales.zonaprop import ZonapropSource

SOURCES: dict[str, type[ArgenpropSource] | type[ZonapropSource]] = {
    "argenprop": ArgenpropSource,
    "zonaprop": ZonapropSource,
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="scrapers.portales")
    ap.add_argument("portal", choices=sorted(SOURCES))
    ap.add_argument("--barrios", nargs="*", help="Limita a estos barrios (default: todos los aceptados)")
    ap.add_argument("--paginas", type=int, default=3)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args(argv)

    query = SearchQuery.from_config(load_config(), max_pages=args.paginas)
    if args.barrios:
        query = query.model_copy(update={"neighborhoods": tuple(args.barrios)})

    source: ListingSource = SOURCES[args.portal](headless=args.headless)
    stubs = source.fetch_list(query)
    for stub in stubs:
        print(stub.model_dump_json())
    print(f"{args.portal}: {len(stubs)} stubs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
