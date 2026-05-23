"""Persistencia SQLite para expedientes DHP (texto, tablas e imagen en JSON)."""
import json
import os
import sqlite3
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "dhp_records.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dhp_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            json_data TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            fecha_actualizacion TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_dhp_cedula ON dhp_records(cedula)"
    )
    conn.commit()
    conn.close()


def _normalize_cedula(cedula):
    return (cedula or "").strip().upper()


def save_or_update_record(cedula, nombre, apellido, json_data):
    cedula = _normalize_cedula(cedula)
    if not cedula:
        raise ValueError("La cédula es obligatoria para guardar el expediente.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_str = json.dumps(json_data, ensure_ascii=False)

    cursor.execute("SELECT id FROM dhp_records WHERE cedula = ?", (cedula,))
    row = cursor.fetchone()

    if row:
        cursor.execute(
            """
            UPDATE dhp_records
            SET nombre = ?, apellido = ?, json_data = ?, fecha_actualizacion = ?
            WHERE cedula = ?
            """,
            (nombre, apellido, json_str, now_str, cedula),
        )
    else:
        cursor.execute(
            """
            INSERT INTO dhp_records
            (cedula, nombre, apellido, json_data, fecha_creacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (cedula, nombre, apellido, json_str, now_str, now_str),
        )

    conn.commit()
    conn.close()


def get_all_records(search_query=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if search_query:
        query = "%" + search_query.strip() + "%"
        cursor.execute(
            """
            SELECT cedula, nombre, apellido, fecha_actualizacion
            FROM dhp_records
            WHERE cedula LIKE ? OR nombre LIKE ? OR apellido LIKE ?
            ORDER BY fecha_actualizacion DESC
            """,
            (query, query, query),
        )
    else:
        cursor.execute(
            """
            SELECT cedula, nombre, apellido, fecha_actualizacion
            FROM dhp_records
            ORDER BY fecha_actualizacion DESC
            """
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_record_by_cedula(cedula):
    cedula = _normalize_cedula(cedula)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT cedula, nombre, apellido, json_data, fecha_creacion, fecha_actualizacion
        FROM dhp_records WHERE cedula = ?
        """,
        (cedula,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "cedula": row[0],
        "nombre": row[1],
        "apellido": row[2],
        "data": json.loads(row[3]),
        "fecha_creacion": row[4],
        "fecha_actualizacion": row[5],
    }


def delete_record(cedula):
    cedula = _normalize_cedula(cedula)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dhp_records WHERE cedula = ?", (cedula,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
