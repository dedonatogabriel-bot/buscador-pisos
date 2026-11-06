"""
Modelo único de aviso. Todos los scrapers devuelven esto.
Si un portal nuevo entra al sistema, solo debe producir Avisos.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
import hashlib
import json


@dataclass
class Aviso:
    # Identidad
    portal: str
    id_portal: str
    url: str

    # Plata
    precio: Optional[int] = None
    expensas: Optional[int] = None
    moneda: str = "ARS"

    # Ficha
    titulo: str = ""
    descripcion: str = ""
    m2: Optional[int] = None
    ambientes: Optional[int] = None
    dormitorios: Optional[int] = None
    piso: Optional[int] = None
    antiguedad: Optional[int] = None

    # Ubicación
    barrio: str = ""
    direccion: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None

    # Contacto
    anunciante: str = ""
    telefono: str = ""

    # Metadatos
    fotos: list = field(default_factory=list)
    visto_en: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Resultados del pipeline (los completan los filtros)
    total_mensual: Optional[int] = None
    score_transporte: Optional[float] = None
    metros_a_transporte: Optional[int] = None
    veredicto_financiero: str = ""
    ahorro_mensual: Optional[int] = None
    motivo_descarte: str = ""
    revisar_a_mano: bool = False

    @property
    def huella(self) -> str:
        """Identificador estable para deduplicar entre corridas y portales."""
        base = f"{self.portal}:{self.id_portal}"
        return hashlib.sha1(base.encode()).hexdigest()[:16]

    @property
    def huella_contenido(self) -> str:
        """
        Detecta el mismo depto republicado con otro ID.
        Usa dirección + m2 + precio redondeado.
        """
        precio_k = (self.precio or 0) // 10_000
        base = f"{self.direccion.lower().strip()}|{self.m2}|{precio_k}"
        return hashlib.sha1(base.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
