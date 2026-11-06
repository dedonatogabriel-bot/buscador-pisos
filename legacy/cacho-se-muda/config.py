"""
Criterios de búsqueda. Todo lo tuneable vive acá.
Cambiá números en este archivo, nunca en la lógica.
"""

# ---------------------------------------------------------------- PRESUPUESTO

# Techo mensual del depto nuevo (alquiler + expensas).
PRESUPUESTO_ALQUILER_MAX = 700_000
PRESUPUESTO_EXPENSAS_MAX = 200_000
PRESUPUESTO_TOTAL_MAX = 900_000

# Si el aviso no discrimina expensas, asumimos este valor al estimar el total.
EXPENSAS_ESTIMADAS_SI_FALTAN = 180_000

# Para convertir avisos publicados en dólares. Actualizalo cada tanto.
TIPO_CAMBIO_USD = 1_450

# ------------------------------------------------------- CONTRATO ACTUAL

ALQUILER_ACTUAL = 640_000          # lo que paga hoy
MULTA_MESES = 2                    # meses de multa por rescisión anticipada
CONTRATO_VENCE = "2027-05-01"      # a partir de acá no hay multa
AJUSTE_TRIMESTRAL_IPC_EST = 0.055  # 5,5% trimestral estimado, para proyectar

# Costos de entrada al alquiler nuevo (en meses de alquiler nuevo).
DEPOSITO_MESES = 1
COMISION_MESES = 1                 # 0 si es trato directo con dueño
MUDANZA_FIJA = 250_000

# ------------------------------------------------------------ COMODIDADES

M2_MINIMO = 50
DORMITORIOS = 1
REQUIERE_BALCON = True
REQUIERE_CALEFACCION = True
REQUIERE_ASCENSOR = True
AMOBLADO = False                   # busca SIN amoblar
ANTIGUEDAD_MAX_ANIOS = 40          # 25 es lo ideal, 40 el techo tolerable

# --------------------------------------------------------------- GEOGRAFÍA

# No hay límite por coordenadas. La zona la definen BARRIOS_OK y
# BARRIOS_EXCLUIDOS. El viejo LAT_LIMITE_SUR (Av. Juan de Garay, -34.6285)
# se eliminó en sep-2026: cortaba al medio barrios habilitados.

# Barrios habilitados. Todo lo que no esté acá se descarta.
BARRIOS_OK = {
    # Lista completa según elección de Gabi (sep 2026).
    "agronomia", "villa del parque", "villa pueyrredon", "coghlan",
    "parque chas", "villa urquiza", "villa devoto", "colegiales",
    "villa ortuzar", "villa santa rita", "saavedra", "nunez",
    "belgrano", "monte castro", "versalles", "velez sarsfield",
    "caballito", "villa luro", "villa real", "villa general mitre",
    "parque chacabuco", "recoleta", "boedo", "almagro", "paternal",
    "villa crespo", "floresta", "palermo", "san cristobal",
    "san nicolas", "san telmo", "balvanera",
    # Habilitado a pedido (sep 2026). Estaba en BARRIOS_EXCLUIDOS.
    "barracas",
    # Mantenidos del setup original.
    "monserrat", "retiro", "chacarita", "puerto madero",
    "flores", "paternal", "agronomia", "san telmo",
    "parque chacabuco", "parque chas",
}

# Exclusión explícita por seguridad, aunque el barrio figure OK.
BARRIOS_EXCLUIDOS = {
    "villa soldati", "mataderos", "nueva pompeya",
    "la boca", "parque patricios", "villa lugano", "villa riachuelo",
    "constitucion",
}

# --------------------------------------------------------------- TRANSPORTE

TRABAJO = (-34.6042, -58.3925)     # Callao y Corrientes
RADIO_TRANSPORTE_M = 600           # metros a pie hasta subte o metrobús
DISTANCIA_MAX_TRABAJO_KM = 7.0     # proxy grueso de 30-40 min en transporte

# ---------------------------------------------------------------- OPERATIVA

FRECUENCIA_HORAS = 6
PORTALES = ["mercadolibre_html", "zonaprop", "argenprop"]
DB_PATH = "data/avisos.db"
