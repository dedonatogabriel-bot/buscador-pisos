"""
Filtro geográfico y score de transporte.

Fuente de datos de transporte:
  1. Datasets abiertos del GCBA (se bajan y cachean en data/).
  2. Si no hay red, usa el fallback aproximado de data/transporte_fallback.json.

Reemplazá el fallback por los datasets oficiales apenas puedas.
"""

import json
import math
import os
import unicodedata
from typing import Optional, Tuple

import config

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_TRANSPORTE = os.path.join(DATA_DIR, "transporte_cache.json")
FALLBACK_TRANSPORTE = os.path.join(DATA_DIR, "transporte_fallback.json")

# Datasets oficiales del GCBA.
URLS_GCBA = {
    "subte": "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/"
             "sbase/subte-estaciones/estaciones-de-subte.geojson",
    "metrobus": "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/"
                "transporte-y-obras-publicas/metrobus/estaciones-de-metrobus.geojson",
}


def normalizar(texto: str) -> str:
    """Saca tildes y baja a minúsculas. Compara barrios sin sorpresas."""
    if not texto:
        return ""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return sin_tildes.lower().strip()


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos puntos."""
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ------------------------------------------------------------------ TRANSPORTE

_paradas_cache = None


def cargar_paradas() -> list:
    """Devuelve [(nombre, tipo, lat, lon), ...]. Cachea en memoria."""
    global _paradas_cache
    if _paradas_cache is not None:
        return _paradas_cache

    if os.path.exists(CACHE_TRANSPORTE):
        with open(CACHE_TRANSPORTE, encoding="utf-8") as f:
            _paradas_cache = json.load(f)
            return _paradas_cache

    with open(FALLBACK_TRANSPORTE, encoding="utf-8") as f:
        _paradas_cache = json.load(f)
    return _paradas_cache


def actualizar_paradas_desde_gcba() -> bool:
    """
    Baja los GeoJSON oficiales y arma el cache.
    Corré esto una vez en la máquina que tenga red.
    """
    import urllib.request

    paradas = []
    for tipo, url in URLS_GCBA.items():
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                gj = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"  [!] No pude bajar {tipo}: {e}")
            continue

        for feat in gj.get("features", []):
            geom = feat.get("geometry") or {}
            if geom.get("type") != "Point":
                continue
            lon, lat = geom["coordinates"][:2]
            props = feat.get("properties", {})
            nombre = ""
            for clave in (
                "nombre", "NOMBRE", "estacion", "ESTACION", "nombre_estacion",
                "ESTACION_N", "name", "descripcion", "parada", "PARADA",
            ):
                valor = props.get(clave)
                if valor and str(valor).strip():
                    nombre = str(valor).strip()
                    break
            linea = props.get("linea") or props.get("LINEA") or props.get("Linea")
            if nombre and linea:
                nombre = f"{nombre} ({linea})"
            if not nombre:
                nombre = tipo
            paradas.append([nombre, tipo, lat, lon])
        print(f"  [ok] {tipo}: {len(gj.get('features', []))} paradas")

    if not paradas:
        return False

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CACHE_TRANSPORTE, "w", encoding="utf-8") as f:
        json.dump(paradas, f, ensure_ascii=False)

    global _paradas_cache
    _paradas_cache = paradas
    return True


def parada_mas_cercana(lat: float, lon: float) -> Tuple[Optional[str], int]:
    """Devuelve (nombre de la parada, metros)."""
    mejor, mejor_d = None, 10**9
    for nombre, tipo, plat, plon in cargar_paradas():
        d = haversine_m(lat, lon, plat, plon)
        if d < mejor_d:
            mejor, mejor_d = f"{nombre} ({tipo})", d
    if mejor is None:
        return None, 10**9
    return mejor, int(mejor_d)


def score_transporte(lat: float, lon: float) -> float:
    """
    0 a 1. Mide solo cercanía a subte o metrobús.
    600 m o menos = 1.0. Más de 1500 m = 0.
    """
    _, metros = parada_mas_cercana(lat, lon)
    if metros <= config.RADIO_TRANSPORTE_M:
        return 1.0
    if metros >= 1500:
        return 0.0
    return round(1 - (metros - config.RADIO_TRANSPORTE_M) / (1500 - config.RADIO_TRANSPORTE_M), 2)


# ------------------------------------------------------------------ BARRIOS

# Todos los barrios de CABA, para reconocerlos dentro de texto libre.
# Los sub-barrios comerciales se mapean a su barrio oficial.
BARRIOS_CABA = [
    "villa general mitre", "villa santa rita", "parque avellaneda",
    "villa del parque", "villa riachuelo", "parque chacabuco",
    "monte castro", "villa devoto", "villa lugano", "villa luro",
    "villa ortuzar", "villa pueyrredon", "villa real", "villa soldati",
    "villa urquiza", "villa crespo", "nueva pompeya", "parque patricios",
    "parque chas", "san cristobal", "puerto madero", "san nicolas",
    "velez sarsfield", "constitucion", "floresta", "agronomia", "almagro",
    "balvanera", "barracas", "belgrano", "boedo", "caballito", "chacarita",
    "coghlan", "colegiales", "flores", "liniers", "mataderos", "monserrat",
    "nunez", "palermo", "paternal", "recoleta", "retiro", "saavedra",
    "san telmo", "versalles", "la boca", "once", "catalinas",
]

SUBBARRIOS = {
    "palermo hollywood": "palermo", "palermo soho": "palermo",
    "palermo chico": "palermo", "palermo botanico": "palermo",
    "palermo viejo": "palermo", "las canitas": "palermo",
    "alto palermo": "palermo", "barrio norte": "recoleta",
    "abasto": "balvanera", "congreso": "balvanera",
    "microcentro": "san nicolas", "tribunales": "san nicolas",
    "centro": "san nicolas", "distrito arcos": "palermo",
    "caballito norte": "caballito", "caballito sur": "caballito",
    "parque centenario": "caballito", "primera junta": "caballito",
    "villa freud": "palermo", "belgrano r": "belgrano",
    "belgrano c": "belgrano", "barrio chino": "belgrano",
}

# Primero los nombres largos, para que "villa crespo" gane sobre "crespo".
_ORDENADOS = sorted(
    list(SUBBARRIOS.keys()) + BARRIOS_CABA, key=len, reverse=True
)


def detectar_barrio(*textos: str) -> str:
    """
    Busca un barrio conocido dentro de texto libre.
    'Departamento en Alquiler en Caballito, Capital Federal' -> 'Caballito'
    'Palermo Hollywood' -> 'Palermo'
    Devuelve '' si no reconoce ninguno.
    """
    for texto in textos:
        t = normalizar(texto)
        if not t:
            continue
        for nombre in _ORDENADOS:
            if nombre in t:
                return SUBBARRIOS.get(nombre, nombre)
    return ""


# ------------------------------------------------------------------ ZONA

def dentro_de_zona(aviso) -> Tuple[bool, str]:
    """
    La zona la definen los barrios, y nada mas.

    Ya NO hay corte por latitud. El limite sur duro en Av. Juan de Garay
    se elimino en sep-2026: partia al medio barrios que estaban
    explicitamente habilitados (Caballito sur, Parque Chacabuco, Barracas)
    y generaba una asimetria absurda, porque solo se podia aplicar a los
    avisos que traian lat/lon. Si un barrio esta en BARRIOS_OK, entra
    completo; si esta en BARRIOS_EXCLUIDOS, queda afuera completo.

    Devuelve (pasa, motivo_si_no_pasa).
    """
    barrio = normalizar(aviso.barrio)

    if barrio and barrio in config.BARRIOS_EXCLUIDOS:
        return False, f"barrio excluido: {aviso.barrio}"

    if barrio and barrio not in config.BARRIOS_OK:
        return False, f"barrio fuera de rango: {aviso.barrio}"

    if not barrio and aviso.lat is None:
        return False, "sin ubicación verificable"

    return True, ""


def distancia_al_trabajo_km(lat: float, lon: float) -> float:
    tlat, tlon = config.TRABAJO
    return round(haversine_m(lat, lon, tlat, tlon) / 1000, 2)


def evaluar_ubicacion(aviso) -> Tuple[bool, str]:
    """
    Filtra por barrio y por cercanía a transporte público.

    NO usa distancia en línea recta al trabajo: es un proxy demasiado
    inexacto para CABA, donde el tiempo real depende de las líneas de
    subte, no de los kilómetros. Si el depto está en un barrio habilitado
    y cerca de una estación, confiamos en que el viaje es razonable.
    La distancia real requeriría la API de Google Maps Directions.
    """
    ok, motivo = dentro_de_zona(aviso)
    if not ok:
        return False, motivo

    if aviso.lat is None or aviso.lon is None:
        aviso.revisar_a_mano = True
        return True, ""

    nombre, metros = parada_mas_cercana(aviso.lat, aviso.lon)
    aviso.metros_a_transporte = metros
    aviso.score_transporte = score_transporte(aviso.lat, aviso.lon)

    if aviso.score_transporte == 0.0:
        return False, f"sin transporte cerca ({metros} m)"

    return True, ""
