"""
Diagnóstico. Prueba cada capa por separado y te dice qué falla.

    python diagnostico.py          # todo
    python diagnostico.py --meli   # solo MercadoLibre
    python diagnostico.py --html   # solo Zonaprop y Argenprop (abre navegador)
"""

import argparse
import os
import sys


def titulo(txt):
    print(f"\n{'=' * 58}\n{txt}\n{'=' * 58}")


# --------------------------------------------------------------- 1. LÓGICA

def probar_logica():
    titulo("1. LÓGICA DE FILTRADO (sin red)")
    import subprocess
    r = subprocess.run(
        [sys.executable, "tests/test_pipeline.py"],
        capture_output=True, text=True,
    )
    print(r.stdout[-1200:])
    if r.returncode == 0:
        print(">> OK. Los filtros funcionan.")
    else:
        print(">> FALLA. Revisá config.py antes de seguir.")
    return r.returncode == 0


# --------------------------------------------------------------- 2. RED

def probar_red():
    """
    Un 403 NO es falta de red: significa que el servidor contestó.
    Solo un timeout o un error de DNS indican que no hay conexión.
    """
    import urllib.error
    import urllib.request

    destinos = {
        "MercadoLibre API": (
            "https://api.mercadolibre.com/sites/MLA",
            "403 esperado sin token",
        ),
        "Zonaprop": (
            "https://www.zonaprop.com.ar",
            "403 esperado: Cloudflare bloquea urllib, para eso usamos Playwright",
        ),
        "Argenprop": (
            "https://www.argenprop.com",
            "403 esperado: mismo caso que Zonaprop",
        ),
    }

    hay_internet = False
    for nombre, (url, nota) in destinos.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                print(f"  [{r.status}] {nombre} -> responde")
                hay_internet = True
        except urllib.error.HTTPError as e:
            # El servidor contestó. Hay red.
            print(f"  [{e.code}] {nombre} -> alcanzable ({nota})")
            hay_internet = True
        except Exception as e:
            print(f"  [SIN RED] {nombre} -> {e}")

    if hay_internet:
        print("\n  >> Hay conexión. Los 403 son normales y esperados.")
    else:
        print("\n  >> No hay salida a internet. Revisá firewall o proxy.")
    return hay_internet


# --------------------------------------------------------- 3. TRANSPORTE

def probar_transporte():
    titulo("3. DATOS DE TRANSPORTE")
    import geo
    paradas = geo.cargar_paradas()
    fuente = "cache GCBA" if os.path.exists(geo.CACHE_TRANSPORTE) else "fallback aproximado"
    print(f"  {len(paradas)} paradas cargadas ({fuente})")

    # Callao y Corrientes debería dar casi 0 metros.
    nombre, metros = geo.parada_mas_cercana(-34.6042, -58.3925)
    print(f"  Callao y Corrientes -> {nombre} a {metros} m")
    if metros > 400:
        print("  >> Sospechoso. Corré: python run.py --actualizar-transporte")
    else:
        print("  >> OK")
    return True


# ------------------------------------------------------- 4. MERCADOLIBRE

def probar_meli(paginas=1):
    titulo("4. MERCADOLIBRE (API oficial)")
    from scrapers.mercadolibre import MercadoLibreScraper

    token = os.environ.get("ML_ACCESS_TOKEN", "")
    print(f"  Token: {'presente' if token else 'AUSENTE (probando igual)'}")

    s = MercadoLibreScraper()
    # Una sola consulta para no quemar cuota.
    s_barrios = __import__("scrapers.mercadolibre", fromlist=["BARRIOS_A_CONSULTAR"])
    original = s_barrios.BARRIOS_A_CONSULTAR[:]
    s_barrios.BARRIOS_A_CONSULTAR = ["Almagro"]

    try:
        avisos = s.buscar(max_paginas=paginas)
    except Exception as e:
        print(f"  >> FALLA: {e}")
        return False
    finally:
        s_barrios.BARRIOS_A_CONSULTAR = original

    print(f"  {len(avisos)} avisos traídos")
    if not avisos:
        print("  >> 0 avisos. Probablemente falte el token.")
        print("     Sacalo en developers.mercadolibre.com.ar")
        return False

    for a in avisos[:3]:
        print(f"    - {a.barrio} | ${a.precio} {a.moneda} | {a.m2} m2 | {a.url[:60]}")

    sin_geo = sum(1 for a in avisos if a.lat is None)
    print(f"  {sin_geo}/{len(avisos)} sin coordenadas")
    return True


# ----------------------------------------------------- 5. ZONAPROP/ARGENPROP

def probar_html(portal="zonaprop", headless=False):
    titulo(f"5. {portal.upper()} (Playwright)")
    try:
        import playwright  # noqa
    except ImportError:
        print("  >> Falta Playwright:")
        print("     pip install playwright && playwright install chromium")
        return False

    from scrapers.portales_html import PortalHTMLScraper

    s = PortalHTMLScraper(portal, headless=headless)
    print(f"  headless={headless} (poné False para ver el navegador)")
    try:
        avisos = s.buscar(max_paginas=1)
    except Exception as e:
        resumen = str(e).split("\n")[0][:160]
        print(f"  >> No pude abrir el navegador: {resumen}")
        if "XServer" in str(e) or "DISPLAY" in str(e):
            print("     Estás en un entorno sin pantalla. Usá headless=True.")
        else:
            print("     Probá: playwright install chromium")
        return False

    print(f"  {len(avisos)} avisos traídos")
    if not avisos:
        print("  >> 0 avisos. Causas probables, en orden:")
        print("     1. Cloudflare te bloqueó -> corré con headless=False")
        print("     2. Cambiaron los selectores -> revisá SEL en portales_html.py")
        print("     3. Cambió la URL de búsqueda -> revisá URLS")
        return False

    for a in avisos[:3]:
        print(f"    - {a.barrio} | ${a.precio} | {a.m2} m2 | {a.titulo[:40]}")

    vacios = sum(1 for a in avisos if a.precio is None)
    if vacios:
        print(f"  >> {vacios} avisos sin precio: revisá el selector 'precio'")
    return True


# --------------------------------------------------------- 5b. INSPECCIONAR

def inspeccionar(portal="zonaprop", headless=True):
    """
    Abre el portal, toma la primera tarjeta y te muestra qué selector
    matchea y cuál no. Es lo que usás cuando un portal deja de andar.
    """
    titulo(f"INSPECCIÓN DE TARJETA: {portal.upper()}")
    from playwright.sync_api import sync_playwright
    from scrapers.portales_html import SEL, URLS
    import config, geo

    sel = SEL[portal]
    url = URLS[portal].format(p=1, max=config.PRESUPUESTO_ALQUILER_MAX)
    print(f"URL: {url}\n")

    with sync_playwright() as pw:
        nav = pw.chromium.launch(headless=headless)
        ctx = nav.new_context(
            locale="es-AR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
        )
        ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        pg = ctx.new_page()
        pg.goto(url, timeout=45_000, wait_until="domcontentloaded")
        try:
            pg.wait_for_selector(sel["tarjeta"], timeout=20_000)
        except Exception:
            print(f">> El selector de tarjeta NO matchea: {sel['tarjeta']}")
            print("   Abrí la URL en Chrome, F12, y buscá el contenedor del aviso.")
            nav.close()
            return

        tarjetas = pg.query_selector_all(sel["tarjeta"])
        print(f"Tarjetas encontradas: {len(tarjetas)}\n")
        t = tarjetas[0]

        print("--- SELECTORES ---")
        for clave in ("precio", "expensas", "direccion", "ubicacion",
                      "caracteristicas", "descripcion", "link"):
            el = t.query_selector(sel[clave])
            if el:
                valor = el.inner_text().strip().replace("\n", " | ")[:70]
                print(f"  [OK ] {clave:16} -> {valor}")
            else:
                print(f"  [--] {clave:16} -> NO MATCHEA ({sel[clave]})")

        texto = t.inner_text()
        print("\n--- TEXTO COMPLETO DE LA TARJETA ---")
        print(texto[:700])

        print("\n--- QUÉ DETECTA EL SISTEMA ---")
        from scrapers.base import ScraperBase as SB
        print(f"  barrio   : {geo.detectar_barrio(texto) or '(ninguno)'}")
        print(f"  precio   : {SB.parse_precio(texto)}")
        print(f"  expensas : {SB.parse_expensas(texto)}")

        print("\n--- HTML (primeros 1500 caracteres) ---")
        print(t.inner_html()[:1500])

        nav.close()


# ------------------------------------------------------------- 6. PIPELINE

def probar_pipeline_real():
    titulo("6. PIPELINE COMPLETO (dry run, no escribe)")
    import subprocess
    r = subprocess.run(
        [sys.executable, "run.py", "--dry", "--paginas", "1"],
        capture_output=True, text=True,
    )
    print(r.stdout[-1500:])
    if r.stderr:
        print("STDERR:", r.stderr[-500:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meli", action="store_true")
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--ver-navegador", action="store_true")
    ap.add_argument("--inspeccionar", metavar="PORTAL",
                    help="zonaprop o argenprop: muestra la tarjeta cruda")
    args = ap.parse_args()

    if args.inspeccionar:
        inspeccionar(args.inspeccionar, headless=not args.ver_navegador)
        return
    if args.meli:
        probar_meli()
        return
    if args.html:
        probar_html("zonaprop", headless=not args.ver_navegador)
        probar_html("argenprop", headless=not args.ver_navegador)
        return

    probar_logica()
    hay_red = probar_red()
    probar_transporte()
    if hay_red:
        probar_meli()
        probar_html("zonaprop", headless=False)
        probar_html("argenprop", headless=False)
        probar_pipeline_real()
    else:
        print("\n>> Sin red a MercadoLibre. Salteo las pruebas de portales.")


if __name__ == "__main__":
    main()
