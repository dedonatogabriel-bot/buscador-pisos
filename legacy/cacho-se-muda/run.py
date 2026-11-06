"""
Orquestador. Esto es lo que corre cada 6 horas.

    python run.py                 # corrida normal
    python run.py --dry           # sin escribir en la base
    python run.py --actualizar-transporte
"""

import argparse
import re
import sys
from collections import Counter

import config
import finanzas
import filtros
import geo
import storage
from scrapers.mercadolibre import MercadoLibreScraper
from scrapers.ml_html import MercadoLibreHTMLScraper
from scrapers.portales_html import zonaprop, argenprop


def plata(valor):
    """Formatea un monto. Los avisos sin precio dicen 'consultar'."""
    return f"${valor:,}" if valor else "consultar"


def construir_scrapers():
    disponibles = {
        "mercadolibre": MercadoLibreScraper,
        "mercadolibre_html": MercadoLibreHTMLScraper,
        "zonaprop": zonaprop,
        "argenprop": argenprop,
    }
    return [disponibles[p]() for p in config.PORTALES if p in disponibles]


def procesar(aviso, con, dry=False):
    """
    Pasa el aviso por los filtros, del más barato al más caro en cómputo.
    Devuelve 'candidato', 'descartado' o 'duplicado'.
    """
    if storage.ya_visto(con, aviso):
        return "duplicado", ""

    # 1. Zona: descarta la mayoría sin tocar nada más.
    ok, motivo = geo.evaluar_ubicacion(aviso)
    if not ok:
        if not dry:
            storage.descartar(con, aviso, motivo)
        return "descartado", motivo

    # 2. Comodidades sobre el texto.
    ok, motivo = filtros.cumple_comodidades(aviso)
    if not ok:
        if not dry:
            storage.descartar(con, aviso, motivo)
        return "descartado", motivo

    # 3. Plata.
    ok, motivo = finanzas.evaluar(aviso)
    if not ok:
        if not dry:
            storage.descartar(con, aviso, motivo)
        return "descartado", motivo

    if not dry:
        storage.guardar(con, aviso)
    return "candidato", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--paginas", type=int, default=3)
    ap.add_argument("--actualizar-transporte", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="muestra cada descarte con su motivo")
    args = ap.parse_args()

    if args.actualizar_transporte:
        print("Bajando datasets del GCBA...")
        ok = geo.actualizar_paradas_desde_gcba()
        print("Listo." if ok else "Falló. Sigue usando el fallback aproximado.")
        return

    con = storage.conectar()
    precios_descartados = []
    resumen = {"candidato": 0, "descartado": 0, "duplicado": 0}
    motivos = Counter()
    excepcionales = []

    for scraper in construir_scrapers():
        print(f"\n[{scraper.nombre}] buscando...")
        try:
            avisos = scraper.buscar(max_paginas=args.paginas)
        except Exception as e:
            print(f"  [!] {scraper.nombre} falló entero: {e}")
            continue

        print(f"  {len(avisos)} avisos traídos")
        for aviso in avisos:
            estado, motivo = procesar(aviso, con, dry=args.dry)
            resumen[estado] += 1
            if estado == "descartado":
                # Agrupa por causa, sin los números concretos.
                clave = re.sub(r"[\d.,$]+", "N", motivo)
                motivos[clave] += 1
                if "supera el techo" in motivo and aviso.precio:
                    precios_descartados.append(aviso.precio)
                if args.verbose:
                    print(f"  [--] {motivo} | {aviso.url[:70]}")
            if estado == "candidato":
                marca = "REVISAR" if aviso.revisar_a_mano else "OK"
                print(f"  [{marca}] {aviso.barrio or '?'} | "
                      f"{plata(aviso.total_mensual)} | "
                      f"{aviso.m2 or '?'} m2 | {aviso.url or 'SIN LINK'}")
                if finanzas.es_oportunidad_excepcional(aviso):
                    excepcionales.append(aviso)

    print("\n" + "=" * 55)
    print(f"Candidatos nuevos : {resumen['candidato']}")
    print(f"Descartados       : {resumen['descartado']}")
    print(f"Ya conocidos      : {resumen['duplicado']}")

    if motivos:
        print("\nPor qué se descartaron:")
        for clave, n in motivos.most_common(12):
            print(f"  {n:4}  {clave}")

    if precios_descartados:
        precios_descartados.sort()
        total = len(precios_descartados)
        p25 = precios_descartados[total // 4]
        p50 = precios_descartados[total // 2]
        p75 = precios_descartados[3 * total // 4]
        p100 = precios_descartados[-1]
        print(f"\nPrecios de los descartados por presupuesto (en pesos):")
        print(f"  mínimo ${precios_descartados[0]:,}  "
              f"| p50 ${p50:,}  "
              f"| p75 ${p75:,}  "
              f"| máximo ${p100:,}")
        cerca = sum(1 for p in precios_descartados if p <= config.PRESUPUESTO_ALQUILER_MAX * 1.2)
        if cerca:
            print(f"  {cerca} de {total} están dentro del 20% del techo "
                  f"(≤ ${int(config.PRESUPUESTO_ALQUILER_MAX * 1.2):,})")

    if args.dry:
        print("\n(modo --dry: nada se guardó en la base)")
    if excepcionales:
        print(f"\n!! {len(excepcionales)} oportunidad(es) para mudarse YA:")
        for a in excepcionales:
            print(f"   {a.barrio} {plata(a.total_mensual)} -> {a.url}")
    print(storage.estadisticas(con))


if __name__ == "__main__":
    main()
