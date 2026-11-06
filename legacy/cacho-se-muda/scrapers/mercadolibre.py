"""
MercadoLibre Inmuebles vía API oficial.

Es el único de los tres que tiene API pública. Arrancá siempre por acá:
no se rompe con cambios de HTML y no te bloquean.

Necesita un access token. Sacalo en https://developers.mercadolibre.com.ar
y exportalo:  export ML_ACCESS_TOKEN="APP_USR-..."
"""

import json
import os
import urllib.parse
import urllib.request
from typing import List

from models import Aviso
from scrapers.base import ScraperBase

API = "https://api.mercadolibre.com"

# IDs de MercadoLibre Argentina.
CATEGORIA_INMUEBLES = "MLA1459"
OPERACION_ALQUILER = "242073"
TIPO_DEPARTAMENTO = "242062"

BARRIOS_A_CONSULTAR = [
    "Recoleta", "Balvanera", "San Nicolas", "Almagro", "Caballito",
    "Villa Crespo", "Palermo", "Colegiales", "Monserrat", "Retiro",
]


class MercadoLibreScraper(ScraperBase):
    nombre = "mercadolibre"

    def __init__(self, token: str = None):
        self.token = token or os.environ.get("ML_ACCESS_TOKEN", "")

    def _get(self, path: str, params: dict) -> dict:
        url = f"{API}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))

    def buscar(self, max_paginas: int = 3) -> List[Aviso]:
        avisos = []
        for barrio in BARRIOS_A_CONSULTAR:
            for pagina in range(max_paginas):
                params = {
                    "category": CATEGORIA_INMUEBLES,
                    "OPERATION": OPERACION_ALQUILER,
                    "PROPERTY_TYPE": TIPO_DEPARTAMENTO,
                    "q": f"departamento alquiler {barrio} CABA",
                    "limit": 50,
                    "offset": pagina * 50,
                    "sort": "date_desc",
                }
                try:
                    data = self._get("/sites/MLA/search", params)
                except Exception as e:
                    print(f"  [!] MELI {barrio} p{pagina}: {e}")
                    break

                resultados = data.get("results", [])
                if not resultados:
                    break

                for item in resultados:
                    avisos.append(self._a_aviso(item, barrio))

                self.dormir()
        return avisos

    def _a_aviso(self, item: dict, barrio_query: str) -> Aviso:
        atributos = {a["id"]: a for a in item.get("attributes", [])}

        def attr(aid):
            a = atributos.get(aid)
            if not a:
                return None
            return a.get("value_name") or a.get("value_struct", {}).get("number")

        ubicacion = item.get("location") or {}
        barrio = (ubicacion.get("neighborhood") or {}).get("name") or barrio_query

        geo = item.get("geolocation") or {}

        return Aviso(
            portal=self.nombre,
            id_portal=item.get("id", ""),
            url=item.get("permalink", ""),
            precio=int(item["price"]) if item.get("price") else None,
            moneda=item.get("currency_id", "ARS"),
            expensas=self.parse_entero(str(attr("MAINTENANCE_FEE") or "")),
            titulo=item.get("title", ""),
            descripcion=item.get("title", ""),
            m2=self.parse_entero(str(attr("TOTAL_AREA") or "")),
            ambientes=self.parse_entero(str(attr("ROOMS") or "")),
            dormitorios=self.parse_entero(str(attr("BEDROOMS") or "")),
            barrio=barrio,
            direccion=(ubicacion.get("address_line") or ""),
            lat=geo.get("latitude"),
            lon=geo.get("longitude"),
            fotos=[item.get("thumbnail", "")],
        )

    def traer_descripcion(self, id_portal: str) -> str:
        """
        La búsqueda no trae descripción completa. Pedila solo para candidatos
        que ya pasaron los filtros baratos: ahorra llamadas a la API.
        """
        try:
            data = self._get(f"/items/{id_portal}/description", {})
            return data.get("plain_text", "")
        except Exception:
            return ""
