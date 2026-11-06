"""
Zonaprop y Argenprop.

Los dos están detrás de Cloudflare / DataDome. `requests` te come un 403
en el primer intento. Hay que usar navegador real: Playwright.

    pip install playwright && playwright install chromium

Los selectores CSS cambian cada pocos meses. Están todos juntos acá arriba
para que los corrijas en un solo lugar cuando se rompa.
"""

import re
from typing import List

import geo
from models import Aviso
from scrapers.base import ScraperBase


# ------------------------------------------------------- URLS ZONAPROP
# URL con todos los filtros aplicados desde zonaprop.com.ar (sep-2026, Gabi).
# Si el presupuesto cambia: volver a filtrar en Zonaprop y reemplazar _BASE_ZP.
_BASE_ZP = (
    "https://www.zonaprop.com.ar/casas-departamentos-ph-alquiler-"
    "agronomia-villa-del-parque-villa-pueyrredon-coghlan-parque-chas-"
    "villa-urquiza-villa-devoto-colegiales-villa-ortuzar-villa-santa-rita-"
    "saavedra-nunez-belgrano-monte-castro-versalles-velez-sarsfield-"
    "caballito-villa-luro-villa-real-villa-general-mitre-parque-chacabuco-"
    "recoleta-boedo-almagro-la-paternal-villa-crespo-palermo-san-cristobal-"
    "san-nicolas-san-telmo-balvanera-las-canitas-barracas-"
    "con-balcon-mas-de-1-bano-mas-50-m2-cubiertos-menos-700000-pesos"
)
ZP_URL_P1 = _BASE_ZP + ".html"
ZP_URL_PN = _BASE_ZP + "-pagina-{n}.html"  # usar .format(n=2), .format(n=3)

# ------------------------------------------------------------------ SELECTORES

SEL = {
    # Zonaprop migró a CSS modules: las clases llevan hash y cambian.
    # Por eso matcheamos por patrón (class*=) en vez de nombre exacto.
    "zonaprop": {
        "tarjeta": "div[data-qa='posting PROPERTY']",
        "precio": "[data-qa='POSTING_CARD_PRICE'], [class*='price' i], [class*='Price']",
        "expensas": "[data-qa='expensas'], [class*='expenses' i], [class*='Expenses']",
        "direccion": "[class*='address' i], [class*='Address']",
        "ubicacion": "[data-qa='POSTING_CARD_LOCATION'], [class*='location' i], [class*='Location']",
        "caracteristicas": "h3[data-qa='POSTING_CARD_FEATURES'], [class*='features' i]",
        "descripcion": "[data-qa='POSTING_CARD_DESCRIPTION'], [class*='description' i]",
        "link": "a[href*='/propiedades/'], a[data-to-posting], a[href]",
        "id_attr": "data-id",
    },
    "argenprop": {
        "tarjeta": "div.listing__item",
        "precio": "p.card__price",
        "expensas": "span.card__expenses",
        "direccion": "p.card__address",
        "ubicacion": "p.card__title--primary",
        "caracteristicas": "ul.card__main-features",
        "descripcion": "p.card__info",
        "link": "a.card, a[href*='/inmuebles/'], a[href]",
        "id_attr": "data-id",
    },
}

import unicodedata as _ud

# Barrios a scrapear en Zonaprop, uno por request (evita paginación y bloqueos).
BARRIOS_ZONAPROP = [
    "agronomia", "villa del parque", "villa pueyrredon", "coghlan",
    "parque chas", "villa urquiza", "villa devoto", "colegiales",
    "villa ortuzar", "villa santa rita", "saavedra", "nunez",
    "belgrano", "monte castro", "versalles", "velez sarsfield",
    "caballito", "villa luro", "villa real", "villa general mitre",
    "parque chacabuco", "recoleta", "boedo", "almagro", "paternal",
    "villa crespo", "floresta", "palermo", "san cristobal",
    "san nicolas", "san telmo", "balvanera", "barracas",
]


def _slug(texto: str) -> str:
    sin = _ud.normalize("NFKD", texto)
    sin = "".join(c for c in sin if not _ud.combining(c))
    return re.sub(r"\s+", "-", sin.lower().strip())


URLS = {
    # URL real de Zonaprop por barrio (confirmada por Gabi sep-2026).
    # Formato: /departamentos-alquiler-{barrio}.html
    # Con precio: /departamentos-alquiler-{barrio}-menos-{max}-pesos.html
    "zonaprop": (
        "https://www.zonaprop.com.ar/departamentos-alquiler-"
        "{slug}-menos-{max_holgura}-pesos.html"
    ),
    "argenprop": (
        "https://www.argenprop.com/departamento-alquiler-"
        "localidad-capital-federal-2-dormitorios?pagina-{p}"
    ),
}


class PortalHTMLScraper(ScraperBase):
    """Scraper genérico para Zonaprop y Argenprop."""

    def __init__(self, portal: str, headless: bool = True):
        assert portal in SEL, f"portal desconocido: {portal}"
        self.nombre = portal
        self.sel = SEL[portal]
        self.headless = headless

    def buscar(self, max_paginas: int = 3) -> List[Aviso]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print(f"  [!] Falta Playwright. pip install playwright")
            return []

        import config

        avisos = []

        # Zonaprop: URL única pre-filtrada con todos los barrios y condiciones.
        # Argenprop: URL paginada estándar.
        if self.nombre == "zonaprop":
            urls_paginas = [ZP_URL_P1] + [
                ZP_URL_PN.format(n=n) for n in range(2, max_paginas + 1)
            ]
        else:
            urls_paginas = [
                URLS[self.nombre].format(p=n)
                for n in range(1, max_paginas + 1)
            ]

        ctx_args = dict(
            locale="es-AR",
            timezone_id="America/Argentina/Buenos_Aires",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
        )
        init_script = "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"

        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=self.headless)

            for idx, url in enumerate(urls_paginas):
                # Contexto nuevo por página: limpia cookies, reduce bloqueos.
                ctx = navegador.new_context(**ctx_args)
                ctx.add_init_script(init_script)
                pagina = ctx.new_page()

                try:
                    pagina.goto(url, timeout=45_000, wait_until="domcontentloaded")
                    tarjeta_visible = False
                    for intento in range(3):
                        try:
                            pagina.wait_for_selector(
                                self.sel["tarjeta"], timeout=20_000
                            )
                            tarjeta_visible = True
                            break
                        except Exception:
                            if intento < 2:
                                import time as _t
                                print(f"    (reintento {intento + 1}/2...)")
                                _t.sleep(8)
                                pagina.reload(wait_until="domcontentloaded", timeout=40_000)
                    if not tarjeta_visible:
                        print(f"  [CF] {self.nombre} pág {idx + 1}: bloqueado.")
                        pagina.close(); ctx.close()
                        break
                except Exception as e:
                    print(f"  [!] {self.nombre} pág {idx + 1}: {str(e).split(chr(10))[0][:80]}")
                    pagina.close(); ctx.close()
                    break

                tarjetas = pagina.query_selector_all(self.sel["tarjeta"])
                antes = len(avisos)
                for t in tarjetas:
                    a = self._a_aviso(t)
                    if a:
                        avisos.append(a)
                print(f"    pág {idx + 1}: {len(avisos) - antes} avisos")

                pagina.close(); ctx.close()

                if not tarjetas:
                    break

                # Simula comportamiento humano antes de pasar de página:
                # scroll gradual hasta el fondo y pausa larga.
                try:
                    pagina.evaluate("""
                        () => new Promise(resolve => {
                            let y = 0;
                            const step = () => {
                                y += 300;
                                window.scrollTo(0, y);
                                if (y < document.body.scrollHeight) {
                                    setTimeout(step, 120);
                                } else {
                                    resolve();
                                }
                            };
                            step();
                        })
                    """)
                except Exception:
                    pass

                self.dormir()

            navegador.close()
        return avisos

    # ------------------------------------------------------------ parseo

    def _texto(self, tarjeta, clave: str) -> str:
        el = tarjeta.query_selector(self.sel[clave])
        return el.inner_text().strip() if el else ""

    def _a_aviso(self, tarjeta):
        try:
            precio_txt = self._texto(tarjeta, "precio")
            precio, moneda = self.parse_precio(precio_txt)

            # Las expensas pueden venir en su propio elemento o pegadas
            # al precio en la misma tarjeta.
            expensas_txt = self._texto(tarjeta, "expensas")
            expensas = self.parse_expensas(expensas_txt) or self.parse_expensas(precio_txt)

            link_el = tarjeta.query_selector(self.sel["link"])
            href = link_el.get_attribute("href") if link_el else ""
            if href and href.startswith("/"):
                base = (
                    "https://www.zonaprop.com.ar"
                    if self.nombre == "zonaprop"
                    else "https://www.argenprop.com"
                )
                href = base + href

            id_portal = tarjeta.get_attribute(self.sel["id_attr"]) or href

            caracteristicas = self._texto(tarjeta, "caracteristicas")
            descripcion = self._texto(tarjeta, "descripcion")
            ubicacion = self._texto(tarjeta, "ubicacion")
            direccion = self._texto(tarjeta, "direccion")

            # Red de seguridad: el texto completo de la tarjeta.
            # Si cambian los selectores, esto sigue funcionando.
            try:
                texto_tarjeta = tarjeta.inner_text()
            except Exception:
                texto_tarjeta = ""

            barrio = geo.detectar_barrio(
                ubicacion, direccion, descripcion, texto_tarjeta
            )

            # Si los selectores finos fallaron, usamos la tarjeta entera.
            if not (caracteristicas or descripcion):
                descripcion = texto_tarjeta
            if precio is None:
                precio, moneda = self.parse_precio(texto_tarjeta)
            if expensas is None:
                expensas = self.parse_expensas(texto_tarjeta)

            return Aviso(
                portal=self.nombre,
                id_portal=str(id_portal),
                url=href,
                precio=precio,
                moneda=moneda,
                expensas=expensas,
                titulo=(ubicacion or direccion or texto_tarjeta[:120]),
                descripcion=f"{caracteristicas} {descripcion}",
                m2=self._m2_desde(caracteristicas or texto_tarjeta),
                barrio=barrio,
                direccion=direccion,
            )
        except Exception:
            return None

    @staticmethod
    def _m2_desde(texto: str):
        m = re.search(r"(\d{2,4})\s*m", texto or "")
        return int(m.group(1)) if m else None


def zonaprop(**kw):
    return PortalHTMLScraper("zonaprop", **kw)


def argenprop(**kw):
    return PortalHTMLScraper("argenprop", **kw)
