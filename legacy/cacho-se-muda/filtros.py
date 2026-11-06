"""
Filtro de comodidades sobre el texto del aviso.

Regla central: si el dato NO aparece, no se descarta.
Se marca revisar_a_mano. Los avisos mal redactados suelen ser los baratos.
"""

import re
from typing import Optional, Tuple

import config
from geo import normalizar

# ------------------------------------------------------------------ PATRONES

NEGACIONES = r"(?:sin|no\s+(?:tiene|posee|cuenta\s+con)|carece\s+de)\s+"

PAT_BALCON = re.compile(r"balc[oó]n|balcones|terraza\s+propia|balcon\s+aterrazado")
PAT_SIN_BALCON = re.compile(NEGACIONES + r"balc[oó]n")

PAT_CALEFACCION = re.compile(
    r"calefacci[oó]n|calefactor|radiador|losa\s+radiante|"
    r"tiro\s+balanceado|split\s+fr[ií]o[\s/-]*calor|aire\s+fr[ií]o[\s/-]*calor|"
    r"caldera|termotanque\s+y\s+calefacci[oó]n"
)
PAT_SIN_CALEFACCION = re.compile(NEGACIONES + r"calefacci[oó]n")

PAT_ASCENSOR = re.compile(r"ascensor")
PAT_SIN_ASCENSOR = re.compile(NEGACIONES + r"ascensor|por\s+escalera")

PAT_AMOBLADO = re.compile(r"amoblado|amueblado|equipado\s+completo|con\s+muebles")
PAT_SIN_AMOBLAR = re.compile(r"sin\s+amoblar|sin\s+amueblar|desamoblado|no\s+amoblado")

PAT_M2 = re.compile(r"(\d{2,4})\s*(?:m2|m²|mts2|mts\.?\s*2|metros\s+cuadrados)")
PAT_DORMITORIOS = re.compile(
    r"(\d|un|una|dos|tres|cuatro)\s*(?:dormitorio|habitaci[oó]n|cuarto|hab\b|dorm\b)"
)
PAT_AMBIENTES = re.compile(r"(\d|un|dos|tres|cuatro)\s*ambiente")
PAT_MONOAMBIENTE = re.compile(r"monoambiente|mono\s*ambiente|studio|loft")
PAT_ANTIGUEDAD = re.compile(r"(\d{1,3})\s*a[nñ]os\s+de\s+antig[uü]edad|antig[uü]edad[:\s]+(\d{1,3})")
PAT_ESTRENAR = re.compile(r"a\s+estrenar|estrenar|nuevo\s+a\s+estrenar")
PAT_TEMPORAL = re.compile(r"temporario|temporal|alquiler\s+por\s+d[ií]a|airbnb|por\s+mes\s+turista")

PALABRAS_NUM = {
    "un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
}


def _num(txt: str) -> Optional[int]:
    txt = txt.strip().lower()
    if txt.isdigit():
        return int(txt)
    return PALABRAS_NUM.get(txt)


# ------------------------------------------------------------------ EXTRACCIÓN

def enriquecer(aviso) -> None:
    """Completa campos faltantes leyendo el texto del aviso."""
    texto = normalizar(f"{aviso.titulo} {aviso.descripcion}")

    if aviso.m2 is None:
        m = PAT_M2.search(texto)
        if m:
            aviso.m2 = int(m.group(1))

    if aviso.dormitorios is None:
        if PAT_MONOAMBIENTE.search(texto):
            aviso.dormitorios = 0
        else:
            m = PAT_DORMITORIOS.search(texto)
            if m:
                aviso.dormitorios = _num(m.group(1))

    if aviso.ambientes is None:
        m = PAT_AMBIENTES.search(texto)
        if m:
            aviso.ambientes = _num(m.group(1))

    # 2 ambientes = 1 dormitorio en la jerga porteña.
    if aviso.dormitorios is None and aviso.ambientes:
        aviso.dormitorios = max(aviso.ambientes - 1, 0)

    if aviso.antiguedad is None:
        if PAT_ESTRENAR.search(texto):
            aviso.antiguedad = 0
        else:
            m = PAT_ANTIGUEDAD.search(texto)
            if m:
                aviso.antiguedad = int(m.group(1) or m.group(2))


# ------------------------------------------------------------------ FILTRO

def cumple_comodidades(aviso) -> Tuple[bool, str]:
    """
    Devuelve (pasa, motivo_si_no_pasa).
    Marca revisar_a_mano cuando falta el dato en lugar de descartar.
    """
    enriquecer(aviso)
    texto = normalizar(f"{aviso.titulo} {aviso.descripcion}")
    dudas = []

    # --- descartes duros
    if PAT_TEMPORAL.search(texto):
        return False, "alquiler temporario"

    if aviso.m2 is not None and aviso.m2 < config.M2_MINIMO:
        return False, f"{aviso.m2} m2 (mínimo {config.M2_MINIMO})"

    if aviso.dormitorios is not None and aviso.dormitorios < config.DORMITORIOS:
        return False, "monoambiente o sin dormitorio"

    if config.AMOBLADO is False and PAT_AMOBLADO.search(texto):
        if not PAT_SIN_AMOBLAR.search(texto):
            return False, "amoblado"

    if config.REQUIERE_BALCON and PAT_SIN_BALCON.search(texto):
        return False, "sin balcón"

    if config.REQUIERE_CALEFACCION and PAT_SIN_CALEFACCION.search(texto):
        return False, "sin calefacción"

    if config.REQUIERE_ASCENSOR and PAT_SIN_ASCENSOR.search(texto):
        return False, "sin ascensor"

    if (
        aviso.antiguedad is not None
        and aviso.antiguedad > config.ANTIGUEDAD_MAX_ANIOS
    ):
        return False, f"{aviso.antiguedad} años de antigüedad"

    # --- dudas: no descartan, marcan para revisión
    if config.REQUIERE_BALCON and not PAT_BALCON.search(texto):
        dudas.append("balcón no mencionado")

    if config.REQUIERE_CALEFACCION and not PAT_CALEFACCION.search(texto):
        dudas.append("calefacción no mencionada")

    if config.REQUIERE_ASCENSOR and not PAT_ASCENSOR.search(texto):
        dudas.append("ascensor no mencionado")

    if aviso.m2 is None:
        dudas.append("m2 no informados")

    if aviso.dormitorios is None:
        dudas.append("dormitorios no informados")

    if dudas:
        aviso.revisar_a_mano = True
        aviso.motivo_descarte = "; ".join(dudas)

    return True, ""
