"""
Contrato común de los scrapers.
Cada portal implementa buscar() y devuelve una lista de Aviso.
"""

import re
import time
from typing import List, Optional, Tuple

from models import Aviso


class ScraperBase:
    nombre = "base"
    pausa_entre_paginas = 10.0

    def buscar(self, max_paginas: int = 3) -> List[Aviso]:
        raise NotImplementedError

    # ------------------------------------------------------------ NÚMEROS

    # Un número con separador de miles, o un número suelto.
    NUMERO = re.compile(r"\d{1,3}(?:[.\s]\d{3})+|\d+")

    @classmethod
    def parse_precio(cls, texto: str) -> Tuple[Optional[int], str]:
        """
        Toma SOLO el primer número del texto.
        Las tarjetas suelen traer alquiler y expensas juntos:
        '$ 1.300.000 + $ 410.000 expensas' -> (1300000, 'ARS')

        '$ 650.000'   -> (650000, 'ARS')
        'USD 800'     -> (800, 'USD')
        'Consultar'   -> (None, 'ARS')
        """
        if not texto:
            return None, "ARS"
        if re.search(r"consultar|a\s+convenir", texto, re.I):
            return None, "ARS"

        m = cls.NUMERO.search(texto)
        if not m:
            return None, "ARS"

        # La moneda se busca SOLO alrededor del número, no en toda la
        # descripción. Si no, cualquier mención suelta a dólares en el
        # texto largo del aviso falsea el precio.
        zona = texto[max(0, m.start() - 20):m.end() + 6]
        moneda = "USD" if re.search(r"u\$s|usd|d[oó]lar", zona, re.I) else "ARS"

        return int(re.sub(r"[^\d]", "", m.group())), moneda

    @classmethod
    def parse_expensas(cls, texto: str) -> Optional[int]:
        """
        Busca el número pegado a la palabra 'expensas'.
        Mira antes y después: los portales lo escriben de las dos formas.
          '$ 410.000 expensas'   y   'Expensas: $ 410.000'

        Ignora montos menores a 10.000: '2 amb' o '1 baño' no son expensas.
        Devuelve None si dice 'sin expensas'.
        """
        if not texto:
            return None

        for m in re.finditer(r"expensas?", texto, re.I):
            ventana_previa = texto[max(0, m.start() - 18):m.start()]
            ventana_post = texto[m.end():m.end() + 40]

            # "sin expensas" / "no incluye expensas": no hay monto.
            if re.search(r"\b(sin|no\s+incluye|excluye)\s*$", ventana_previa, re.I):
                continue

            candidatos = cls.NUMERO.findall(ventana_post)
            candidatos += list(reversed(cls.NUMERO.findall(ventana_previa)))

            for c in candidatos:
                valor = int(re.sub(r"[^\d]", "", c))
                if valor >= 10_000:
                    return valor
        return None

    @staticmethod
    def parse_entero(texto: str) -> Optional[int]:
        """Primer entero del texto. '58 m2' -> 58."""
        if not texto:
            return None
        m = re.search(r"\d+", str(texto).replace(".", ""))
        return int(m.group()) if m else None

    # ------------------------------------------------------------ RITMO

    def dormir(self) -> None:
        """Pausa entre páginas. No le pegues seguido a los portales."""
        time.sleep(self.pausa_entre_paginas)
