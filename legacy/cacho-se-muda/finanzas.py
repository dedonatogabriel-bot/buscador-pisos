"""
Motor financiero. Corre solo, para cada aviso.

Responde una sola pregunta:
¿conviene mudarse ya y pagar la multa, o esperar a mayo?
"""

from datetime import date
from typing import Tuple

import config


def meses_hasta_vencimiento(hoy: date = None) -> int:
    """Meses enteros que faltan hasta que el contrato actual venza."""
    hoy = hoy or date.today()
    fin = date.fromisoformat(config.CONTRATO_VENCE)
    if hoy >= fin:
        return 0
    return (fin.year - hoy.year) * 12 + (fin.month - hoy.month)


def proyectar_alquiler_actual(meses: int) -> int:
    """
    Suma lo que va a pagar del contrato actual hasta mayo.
    Ajusta por IPC cada trimestre.
    """
    total = 0
    monto = config.ALQUILER_ACTUAL
    for m in range(meses):
        if m > 0 and m % 3 == 0:
            monto = int(monto * (1 + config.AJUSTE_TRIMESTRAL_IPC_EST))
        total += monto
    return total


def costo_entrada(alquiler_nuevo: int, factor_inflacion: float = 1.0) -> int:
    """Depósito + comisión + mudanza."""
    alq = int(alquiler_nuevo * factor_inflacion)
    return (
        alq * config.DEPOSITO_MESES
        + alq * config.COMISION_MESES
        + int(config.MUDANZA_FIJA * factor_inflacion)
    )


def total_mensual(aviso) -> Tuple[int, bool]:
    """
    Alquiler + expensas. Devuelve (total, expensas_estimadas).
    """
    precio = aviso.precio or 0
    if aviso.expensas is not None:
        return precio + aviso.expensas, False
    return precio + config.EXPENSAS_ESTIMADAS_SI_FALTAN, True


def evaluar(aviso, hoy: date = None) -> Tuple[bool, str]:
    """
    Escribe total_mensual, ahorro_mensual y veredicto_financiero en el aviso.
    Devuelve (pasa, motivo_si_no_pasa).
    """
    if not aviso.precio:
        aviso.revisar_a_mano = True
        return True, ""

    if aviso.moneda == "USD":
        # Convertimos y seguimos con la evaluación normal.
        aviso.precio = int(aviso.precio * config.TIPO_CAMBIO_USD)
        aviso.moneda = "ARS"
        aviso.revisar_a_mano = True
    elif aviso.moneda != "ARS":
        aviso.revisar_a_mano = True
        aviso.veredicto_financiero = f"precio en {aviso.moneda}, revisar a mano"
        return True, ""

    total, estimadas = total_mensual(aviso)
    aviso.total_mensual = total
    if estimadas:
        aviso.revisar_a_mano = True

    # --- precio absurdo = probablemente venta, no alquiler
    # Los alquileres en CABA no superan los $5M. Las ventas arrancan en $30M+.
    # $9M es un corte conservador que no toca ningún alquiler legítimo.
    PRECIO_MAX_ALQUILER = config.PRESUPUESTO_TOTAL_MAX * 10
    if aviso.precio and aviso.precio > PRECIO_MAX_ALQUILER:
        return False, f"precio ${aviso.precio:,} sugiere aviso de venta"

    # --- techo duro: solo el total (alquiler + expensas).
    # Un alquiler alto con expensas bajas puede cuadrar igual.
    # Ej: $800k alquiler + $80k expensas = $880k total -> pasa.
    if total > config.PRESUPUESTO_TOTAL_MAX:
        return False, f"total ${total:,} supera ${config.PRESUPUESTO_TOTAL_MAX:,}"

    # --- comparación mudarse ya vs esperar
    n = meses_hasta_vencimiento(hoy)
    aviso.ahorro_mensual = config.ALQUILER_ACTUAL - aviso.precio

    if n == 0:
        aviso.veredicto_financiero = "Contrato vencido: mudarse sin multa"
        return True, ""

    multa = config.ALQUILER_ACTUAL * config.MULTA_MESES
    inflacion_a_mayo = (1 + config.AJUSTE_TRIMESTRAL_IPC_EST) ** (n / 3)

    costo_mudarse_ya = (
        multa
        + costo_entrada(aviso.precio)
        + total * n
    )
    costo_esperar = (
        proyectar_alquiler_actual(n)
        + costo_entrada(aviso.precio, inflacion_a_mayo)
    )

    diferencia = costo_mudarse_ya - costo_esperar

    if diferencia < 0:
        aviso.veredicto_financiero = (
            f"MUDARSE YA: ahorra ${abs(diferencia):,} aun pagando la multa"
        )
    else:
        aviso.veredicto_financiero = (
            f"Esperar a mayo: mudarse ya costaría ${diferencia:,} extra"
        )

    return True, ""


def es_oportunidad_excepcional(aviso) -> bool:
    """Marca los avisos que justifican romper el contrato antes de mayo."""
    return aviso.veredicto_financiero.startswith("MUDARSE YA")
