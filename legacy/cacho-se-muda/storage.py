"""
Persistencia y deduplicación.

SQLite alcanza para este volumen.
Si lo movés a n8n + Supabase, reemplazá solo este archivo.
"""

import os
import sqlite3
from typing import List

import config
from models import Aviso

SCHEMA = """
CREATE TABLE IF NOT EXISTS avisos (
    huella            TEXT PRIMARY KEY,
    huella_contenido  TEXT,
    portal            TEXT,
    id_portal         TEXT,
    url               TEXT,
    precio            INTEGER,
    expensas          INTEGER,
    total_mensual     INTEGER,
    moneda            TEXT,
    titulo            TEXT,
    descripcion       TEXT,
    m2                INTEGER,
    dormitorios       INTEGER,
    piso              INTEGER,
    antiguedad        INTEGER,
    barrio            TEXT,
    direccion         TEXT,
    lat               REAL,
    lon               REAL,
    anunciante        TEXT,
    telefono          TEXT,
    score_transporte  REAL,
    metros_a_transporte INTEGER,
    veredicto_financiero TEXT,
    ahorro_mensual    INTEGER,
    revisar_a_mano    INTEGER,
    estado            TEXT DEFAULT 'nuevo',
    visto_en          TEXT,
    notificado        INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_contenido ON avisos(huella_contenido);
CREATE INDEX IF NOT EXISTS idx_estado ON avisos(estado);

CREATE TABLE IF NOT EXISTS descartes (
    huella   TEXT PRIMARY KEY,
    portal   TEXT,
    url      TEXT,
    motivo   TEXT,
    visto_en TEXT
);
"""


def conectar(path: str = None) -> sqlite3.Connection:
    path = path or config.DB_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def ya_visto(con, aviso: Aviso) -> bool:
    """True si el aviso o el mismo depto republicado ya pasó por acá."""
    cur = con.execute(
        "SELECT 1 FROM avisos WHERE huella=? OR huella_contenido=? LIMIT 1",
        (aviso.huella, aviso.huella_contenido),
    )
    if cur.fetchone():
        return True
    cur = con.execute("SELECT 1 FROM descartes WHERE huella=? LIMIT 1", (aviso.huella,))
    return cur.fetchone() is not None


def guardar(con, aviso: Aviso) -> None:
    con.execute(
        """
        INSERT OR REPLACE INTO avisos (
            huella, huella_contenido, portal, id_portal, url, precio, expensas,
            total_mensual, moneda, titulo, descripcion, m2, dormitorios, piso,
            antiguedad, barrio, direccion, lat, lon, anunciante, telefono,
            score_transporte, metros_a_transporte, veredicto_financiero,
            ahorro_mensual, revisar_a_mano, visto_en
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            aviso.huella, aviso.huella_contenido, aviso.portal, aviso.id_portal,
            aviso.url, aviso.precio, aviso.expensas, aviso.total_mensual,
            aviso.moneda, aviso.titulo, aviso.descripcion[:2000], aviso.m2,
            aviso.dormitorios, aviso.piso, aviso.antiguedad, aviso.barrio,
            aviso.direccion, aviso.lat, aviso.lon, aviso.anunciante,
            aviso.telefono, aviso.score_transporte, aviso.metros_a_transporte,
            aviso.veredicto_financiero, aviso.ahorro_mensual,
            int(aviso.revisar_a_mano), aviso.visto_en,
        ),
    )
    con.commit()


def descartar(con, aviso: Aviso, motivo: str) -> None:
    con.execute(
        "INSERT OR REPLACE INTO descartes (huella, portal, url, motivo, visto_en) "
        "VALUES (?,?,?,?,?)",
        (aviso.huella, aviso.portal, aviso.url, motivo, aviso.visto_en),
    )
    con.commit()


def pendientes_de_notificar(con) -> List[sqlite3.Row]:
    return con.execute(
        "SELECT * FROM avisos WHERE notificado=0 ORDER BY total_mensual ASC"
    ).fetchall()


def marcar_notificado(con, huella: str) -> None:
    con.execute("UPDATE avisos SET notificado=1 WHERE huella=?", (huella,))
    con.commit()


def estadisticas(con) -> dict:
    return {
        "candidatos": con.execute("SELECT COUNT(*) c FROM avisos").fetchone()["c"],
        "descartados": con.execute("SELECT COUNT(*) c FROM descartes").fetchone()["c"],
        "a_revisar": con.execute(
            "SELECT COUNT(*) c FROM avisos WHERE revisar_a_mano=1"
        ).fetchone()["c"],
    }
