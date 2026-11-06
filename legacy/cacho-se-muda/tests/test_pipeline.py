"""
Avisos sintéticos que cubren los casos límite.
Corré:  python tests/test_pipeline.py
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import filtros
import finanzas
import geo
from models import Aviso

HOY = date(2026, 9, 14)

CASOS = [
    # --- deberían PASAR
    dict(
        esperado="pasa",
        nota="Almagro, cumple todo",
        aviso=Aviso(
            portal="test", id_portal="1", url="http://x/1",
            precio=620_000, expensas=170_000,
            titulo="Depto 2 ambientes en Almagro",
            descripcion="55 m2, balcon al frente, calefaccion por radiadores, "
                        "edificio con ascensor, 20 anos de antiguedad",
            barrio="Almagro", lat=-34.6060, lon=-58.4200,
        ),
    ),
    dict(
        esperado="pasa",
        nota="Caballito, datos incompletos -> revisar a mano",
        aviso=Aviso(
            portal="test", id_portal="2", url="http://x/2",
            precio=580_000,
            titulo="Departamento en Caballito",
            descripcion="Luminoso, excelente ubicacion",
            barrio="Caballito", lat=-34.6180, lon=-58.4380,
        ),
    ),
    dict(
        esperado="pasa",
        nota="Balvanera barato -> candidato a mudarse ya",
        aviso=Aviso(
            portal="test", id_portal="3", url="http://x/3",
            precio=380_000, expensas=120_000,
            titulo="2 ambientes Balvanera",
            descripcion="52 m2 con balcon, calefaccion central, ascensor, "
                        "antiguedad 30 anos",
            barrio="Balvanera", lat=-34.6090, lon=-58.4020,
        ),
    ),

    # --- deberían CAER
    dict(
        esperado="cae", motivo_esperado="barrio",
        nota="Mataderos: zona excluida",
        aviso=Aviso(
            portal="test", id_portal="4", url="http://x/4",
            precio=400_000, expensas=100_000,
            titulo="Depto en Mataderos", descripcion="60 m2 balcon calefaccion ascensor",
            barrio="Mataderos", lat=-34.6580, lon=-58.5050,
        ),
    ),
    dict(
        esperado="pasa",
        nota="Boedo al sur de Juan de Garay: entra (ya no hay corte por latitud)",
        aviso=Aviso(
            portal="test", id_portal="5", url="http://x/5",
            precio=500_000, expensas=100_000,
            titulo="Depto zona sur", descripcion="55 m2 balcon calefaccion ascensor",
            barrio="Boedo", lat=-34.6400, lon=-58.4100,
        ),
    ),
    dict(
        esperado="pasa",
        nota="Barracas: barrio habilitado en sep-2026, bien al sur de Garay",
        aviso=Aviso(
            portal="test", id_portal="13", url="http://x/13",
            precio=520_000, expensas=120_000,
            titulo="Depto en Barracas",
            descripcion="58 m2 balcon calefaccion ascensor 15 anos de antiguedad",
            barrio="Barracas", lat=-34.6412, lon=-58.3712,
        ),
    ),
    dict(
        esperado="pasa",
        nota="Parque Chacabuco: barrio entero habilitado, antes caia por latitud",
        aviso=Aviso(
            portal="test", id_portal="14", url="http://x/14",
            precio=560_000, expensas=130_000,
            titulo="Depto en Parque Chacabuco",
            descripcion="52 m2 balcon calefaccion ascensor",
            barrio="Parque Chacabuco", lat=-34.6364, lon=-58.4310,
        ),
    ),
    dict(
        esperado="pasa",
        nota="Caballito sur: barrio entero habilitado, antes caia por latitud",
        aviso=Aviso(
            portal="test", id_portal="15", url="http://x/15",
            precio=580_000, expensas=140_000,
            titulo="Depto en Caballito",
            descripcion="54 m2 balcon calefaccion ascensor",
            barrio="Caballito", lat=-34.6320, lon=-58.4400,
        ),
    ),
    dict(
        esperado="cae", motivo_esperado="barrio excluido",
        nota="La Boca: al sur y excluido. Ahora lo frena la lista, no la latitud",
        aviso=Aviso(
            portal="test", id_portal="16", url="http://x/16",
            precio=450_000, expensas=90_000,
            titulo="Depto en La Boca",
            descripcion="60 m2 balcon calefaccion ascensor",
            barrio="La Boca", lat=-34.6350, lon=-58.3630,
        ),
    ),
    dict(
        esperado="cae", motivo_esperado="m2",
        nota="40 m2, por debajo del mínimo",
        aviso=Aviso(
            portal="test", id_portal="6", url="http://x/6",
            precio=450_000, expensas=100_000,
            titulo="Depto chico Palermo",
            descripcion="40 m2 con balcon y calefaccion, ascensor",
            barrio="Palermo", lat=-34.5800, lon=-58.4250,
        ),
    ),
    dict(
        esperado="cae", motivo_esperado="monoambiente",
        nota="Monoambiente",
        aviso=Aviso(
            portal="test", id_portal="7", url="http://x/7",
            precio=400_000, expensas=90_000,
            titulo="Monoambiente en Recoleta",
            descripcion="Monoambiente de 50 m2 con balcon, calefaccion, ascensor",
            barrio="Recoleta", lat=-34.5950, lon=-58.3950,
        ),
    ),
    dict(
        esperado="cae", motivo_esperado="balcón",
        nota="Dice explícitamente sin balcón",
        aviso=Aviso(
            portal="test", id_portal="8", url="http://x/8",
            precio=500_000, expensas=120_000,
            titulo="2 amb Villa Crespo",
            descripcion="55 m2, sin balcon, calefaccion, ascensor",
            barrio="Villa Crespo", lat=-34.5980, lon=-58.4380,
        ),
    ),
    dict(
        esperado="cae", motivo_esperado="amoblado",
        nota="Amoblado",
        aviso=Aviso(
            portal="test", id_portal="9", url="http://x/9",
            precio=600_000, expensas=150_000,
            titulo="2 amb amoblado Palermo",
            descripcion="55 m2 amoblado, balcon, calefaccion, ascensor",
            barrio="Palermo", lat=-34.5800, lon=-58.4250,
        ),
    ),
    dict(
        esperado="cae", motivo_esperado="supera",
        nota="Se pasa del presupuesto total",
        aviso=Aviso(
            portal="test", id_portal="10", url="http://x/10",
            precio=690_000, expensas=300_000,
            titulo="2 amb Recoleta",
            descripcion="60 m2 balcon calefaccion ascensor 15 anos",
            barrio="Recoleta", lat=-34.5950, lon=-58.3950,
        ),
    ),
    dict(
        esperado="cae", motivo_esperado="temporario",
        nota="Alquiler temporario",
        aviso=Aviso(
            portal="test", id_portal="11", url="http://x/11",
            precio=500_000, expensas=100_000,
            titulo="Alquiler temporario Palermo",
            descripcion="55 m2 balcon calefaccion ascensor, alquiler temporario",
            barrio="Palermo", lat=-34.5800, lon=-58.4250,
        ),
    ),
    dict(
        esperado="pasa",
        nota="Villa Urquiza: pasa (barrio OK + colectivos, sin subte cercano)",
        aviso=Aviso(
            portal="test", id_portal="12", url="http://x/12",
            precio=450_000, expensas=100_000,
            titulo="2 amb Villa Urquiza",
            descripcion="55 m2 balcon calefaccion ascensor",
            barrio="Villa Urquiza", lat=-34.5720, lon=-58.4900,
        ),
    ),
]


def correr(aviso):
    ok, motivo = geo.evaluar_ubicacion(aviso)
    if not ok:
        return False, motivo
    ok, motivo = filtros.cumple_comodidades(aviso)
    if not ok:
        return False, motivo
    ok, motivo = finanzas.evaluar(aviso, hoy=HOY)
    if not ok:
        return False, motivo
    return True, ""


def probar_contrato_scrapers():
    """
    Verifica que los scrapers tengan todos sus métodos.
    Atrapa archivos truncados o imports rotos antes de salir a la red.
    """
    from scrapers.base import ScraperBase
    from scrapers.mercadolibre import MercadoLibreScraper
    from scrapers.portales_html import zonaprop, argenprop

    requeridos = ["buscar", "parse_precio", "parse_expensas",
                  "parse_entero", "dormir"]
    fallos = 0

    for nombre, obj in [
        ("ScraperBase", ScraperBase),
        ("MercadoLibre", MercadoLibreScraper()),
        ("Zonaprop", zonaprop()),
        ("Argenprop", argenprop()),
    ]:
        faltan = [m for m in requeridos if not hasattr(obj, m)]
        if faltan:
            print(f"[MAL] {nombre}: le faltan {faltan}")
            fallos += 1
        else:
            print(f"[OK ] {nombre}: contrato completo")

    # Casos de parseo que ya nos rompieron una vez.
    casos = [
        ("$ 1.300.000 + $ 410.000 expensas", 1300000, 410000),
        ("$ 615.000\n+ $ 180.000 Expensas\n58 m2 2 amb 1 baño", 615000, 180000),
        ("$ 520.000 sin expensas informadas", 520000, None),
        ("Consultar", None, None),
    ]
    for texto, precio_ok, exp_ok in casos:
        precio, _ = ScraperBase.parse_precio(texto)
        exp = ScraperBase.parse_expensas(texto)
        if precio != precio_ok or exp != exp_ok:
            print(f"[MAL] parseo {texto[:30]!r}: dio ({precio}, {exp}), "
                  f"esperaba ({precio_ok}, {exp_ok})")
            fallos += 1
    if not fallos:
        print("[OK ] parseo de precios y expensas")

    print()
    return fallos


def main():
    fallos = probar_contrato_scrapers()
    print(f"Meses hasta mayo: {finanzas.meses_hasta_vencimiento(HOY)}\n")

    for caso in CASOS:
        aviso = caso["aviso"]
        paso, motivo = correr(aviso)
        esperaba_pasar = caso["esperado"] == "pasa"

        bien = paso == esperaba_pasar
        if bien and not esperaba_pasar:
            bien = caso["motivo_esperado"].lower() in motivo.lower()

        marca = "OK " if bien else "MAL"
        if not bien:
            fallos += 1

        print(f"[{marca}] {caso['nota']}")
        if paso:
            print(f"        total ${aviso.total_mensual:,} | "
                  f"transporte {aviso.metros_a_transporte} m | "
                  f"{'REVISAR' if aviso.revisar_a_mano else 'completo'}")
            print(f"        {aviso.veredicto_financiero}")
            if aviso.revisar_a_mano and aviso.motivo_descarte:
                print(f"        dudas: {aviso.motivo_descarte}")
        else:
            print(f"        descartado: {motivo}")
        print()

    print("=" * 55)
    print(f"{len(CASOS) - fallos}/{len(CASOS)} casos correctos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
