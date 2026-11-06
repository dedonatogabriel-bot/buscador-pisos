"""
MercadoLibre Inmuebles — scraper HTML via Playwright.

No requiere token ni API. Funciona sobre las URLs públicas de inmuebles.mercadolibre.com.ar.

Selectores verificados en el browser el 14/09/2026:
  - Tarjeta:    li.ui-search-layout__item
  - Precio:     .andes-money-amount__fraction  (primer elemento = precio actual)
  - Moneda:     .andes-money-amount__currency-symbol
  - Link:       a.ui-search-link  o  primer a[href*='mercadolibre']
  - Ubicación:  .ui-search-item__location
  - Atributos:  .ui-search-card-attributes  (ambientes, baños, m²)

Paginación: 48 resultados por página.
  Página 1: /barrio/_PriceRange_0-{max}_NoIndex_True
  Página 2: /barrio/_Desde_48_PriceRange_0-{max}_NoIndex_True
  Página 3: /barrio/_Desde_96_PriceRange_0-{max}_NoIndex_True

Las expensas NO aparecen en el listado, solo en el aviso individual.
Los avisos candidatos se marcan revisar_a_mano y se estiman con EXPENSAS_ESTIMADAS_SI_FALTAN.
"""

import re
import time
from typing import List, Optional

import config
import geo
from models import Aviso
from scrapers.base import ScraperBase

# ------------------------------------------------------------ BARRIOS

# Misma lista que Zonaprop. Los slugs siguen el mismo formato ASCII-con-guiones.
BARRIOS_ML = [
    "agronomia", "villa-del-parque", "villa-pueyrredon", "coghlan",
    "parque-chas", "villa-urquiza", "villa-devoto", "colegiales",
    "villa-ortuzar", "villa-santa-rita", "saavedra", "nunez",
    "belgrano", "monte-castro", "versalles", "velez-sarsfield",
    "caballito", "villa-luro", "villa-real", "villa-general-mitre",
    "parque-chacabuco", "recoleta", "boedo", "almagro", "paternal",
    "villa-crespo", "floresta", "palermo", "san-cristobal",
    "san-nicolas", "san-telmo", "balvanera", "barracas",
]

# ------------------------------------------------------------ URLs

BASE = "https://inmuebles.mercadolibre.com.ar/departamentos/alquiler/capital-federal"

def _url(slug: str, offset: int, max_precio: int) -> str:
    precio_filtro = f"_PriceRange_0-{max_precio}_NoIndex_True"
    if offset == 0:
        return f"{BASE}/{slug}/{precio_filtro}"
    return f"{BASE}/{slug}/_Desde_{offset}{precio_filtro}"


# ------------------------------------------------------------ SCRAPER

class MercadoLibreHTMLScraper(ScraperBase):
    nombre = "mercadolibre_html"
    pausa_entre_paginas = 5.0   # ML es más permisivo que Zonaprop

    def __init__(self, headless: bool = True):
        self.headless = headless

    def buscar(self, max_paginas: int = 2) -> List[Aviso]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("  [!] Falta Playwright. pip install playwright")
            return []

        max_precio = int(config.PRESUPUESTO_ALQUILER_MAX * 1.3)
        avisos: List[Aviso] = []

        with sync_playwright() as pw:
            navegador = pw.chromium.launch(headless=self.headless)

            for slug in BARRIOS_ML:
                # Un contexto nuevo por barrio: limpia cookies entre requests.
                ctx = navegador.new_context(
                    locale="es-AR",
                    timezone_id="America/Argentina/Buenos_Aires",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1440, "height": 900},
                )
                ctx.add_init_script(
                    "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
                )
                pagina = ctx.new_page()

                for n in range(max_paginas):
                    offset = n * 48
                    url = _url(slug, offset, max_precio)

                    try:
                        pagina.goto(url, timeout=45_000, wait_until="domcontentloaded")
                        pagina.wait_for_selector(
                            "li.ui-search-layout__item", timeout=20_000
                        )
                    except Exception as e:
                        msg = str(e).split("\n")[0][:80]
                        print(f"  [!] ML {slug} p{n+1}: {msg}")
                        break

                    tarjetas = pagina.query_selector_all("li.ui-search-layout__item")
                    if not tarjetas:
                        break

                    antes = len(avisos)
                    for t in tarjetas:
                        a = self._parsear(t, slug)
                        if a:
                            avisos.append(a)

                    nuevos = len(avisos) - antes
                    print(f"    {slug} p{n+1}: {nuevos} avisos")

                    # Si trajo menos de 48, no hay página siguiente.
                    if len(tarjetas) < 48:
                        break

                    time.sleep(self.pausa_entre_paginas)

                pagina.close()
                ctx.close()
                time.sleep(self.pausa_entre_paginas)

            navegador.close()

        return avisos

    # ---------------------------------------------------- parseo de tarjeta

    def _parsear(self, tarjeta, slug_barrio: str) -> Optional[Aviso]:
        try:
            texto = tarjeta.inner_text()

            # Precio y moneda.
            precio_el = tarjeta.query_selector(".andes-money-amount__fraction")
            moneda_el = tarjeta.query_selector(".andes-money-amount__currency-symbol")
            precio_txt = precio_el.inner_text() if precio_el else ""
            moneda_sym = moneda_el.inner_text() if moneda_el else "$"
            moneda = "USD" if "U" in moneda_sym or "u" in moneda_sym else "ARS"
            precio = int(re.sub(r"[^\d]", "", precio_txt)) if precio_txt else None

            # Link e ID.
            link_el = (
                tarjeta.query_selector("a.ui-search-link")
                or tarjeta.query_selector("a[href*='mercadolibre']")
                or tarjeta.query_selector("a")
            )
            url = link_el.get_attribute("href") if link_el else ""
            m = re.search(r"MLA-?(\d+)", url or "")
            id_portal = m.group(0) if m else (url or texto[:30])

            # Ubicación y barrio.
            ubic_el = tarjeta.query_selector(".ui-search-item__location")
            ubicacion = ubic_el.inner_text() if ubic_el else ""
            barrio = geo.detectar_barrio(ubicacion, texto)

            # Atributos: ambientes, m².
            attr_el = tarjeta.query_selector(
                ".ui-search-card-attributes, [class*='attributes']"
            )
            attr_txt = attr_el.inner_text() if attr_el else texto

            m2 = self.parse_entero(
                next(iter(re.findall(r"(\d+)\s*m²", attr_txt)), "")
            )
            ambs_m = re.search(r"(\d+)\s*amb", attr_txt, re.I)
            ambientes = int(ambs_m.group(1)) if ambs_m else None

            # Título (fallback al texto completo de la tarjeta).
            titulo_el = tarjeta.query_selector(
                "[class*='title'], [class*='Title']"
            )
            titulo = (titulo_el.inner_text() if titulo_el else texto[:120]).strip()

            return Aviso(
                portal=self.nombre,
                id_portal=id_portal,
                url=url or "",
                precio=precio,
                moneda=moneda,
                expensas=None,      # ML no muestra expensas en el listado.
                titulo=titulo[:200],
                descripcion=texto[:500],
                m2=m2,
                ambientes=ambientes,
                barrio=barrio,
                direccion=ubicacion,
                revisar_a_mano=True,  # siempre: sin expensas, hay que verificar.
            )
        except Exception:
            return None
