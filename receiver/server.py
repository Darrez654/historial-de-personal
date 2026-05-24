"""
==============================================================================
  RECEPTOR DE DATOS DHP — API REST
==============================================================================
  Despliega este archivo en TU SERVIDOR para recibir los formularios DHP
  desde las computadoras de los usuarios.

  Instalación rápida (en tu servidor):
      pip install flask flask-cors
      python receiver/server.py

  Luego configura las PC de los usuarios con:
      DHP_EXTERNAL_ENABLED=true
      DHP_EXTERNAL_API_URL=http://TU_IP:5000/api/dhp/recibir
      DHP_EXTERNAL_API_KEY=mi-clave-secreta

  Endpoints:
      POST /api/dhp/recibir         → Recibe formulario DHP
      GET  /api/dhp/listar?q=...    → Busca registros
      GET  /api/dhp/consulta/<ci>   → Consulta un registro por cédula
      GET  /api/dhp/stats           → Estadísticas
      GET  /api/dhp/health          → Health check

  Variables de entorno (opcional):
      RECEIVER_PORT      : Puerto (defecto: 5000)
      RECEIVER_API_KEY   : API Key para autenticación Bearer
      RECEIVER_DB_PATH   : Ruta a la base de datos SQLite
==============================================================================
"""
import os
import json
import sqlite3
from datetime import datetime

from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================================================
# CONFIGURACIÓN
# ==========================================================================
RECEIVER_PORT = int(os.environ.get("RECEIVER_PORT", "5000"))
RECEIVER_API_KEY = os.environ.get("RECEIVER_API_KEY", "").strip()
RECEIVER_DB_PATH = os.environ.get(
    "RECEIVER_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "dhp_received_records.db"),
)
RECEIVER_DB_PATH = os.path.abspath(RECEIVER_DB_PATH)

os.makedirs(os.path.dirname(RECEIVER_DB_PATH), exist_ok=True)


# ==========================================================================
# BASE DE DATOS
# ==========================================================================
def init_db():
    conn = sqlite3.connect(RECEIVER_DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS received_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT NOT NULL,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            data_json TEXT NOT NULL,
            fecha_recepcion TEXT NOT NULL,
            fuente TEXT DEFAULT ''
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_rec_cedula ON received_records(cedula)")
    conn.commit()
    conn.close()


def save_received(cedula, nombre, apellido, data_json, fuente=""):
    conn = sqlite3.connect(RECEIVER_DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        """INSERT INTO received_records (cedula, nombre, apellido, data_json, fecha_recepcion, fuente)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (cedula, nombre, apellido, data_json, now, fuente),
    )
    conn.commit()
    conn.close()


def search_records(query=""):
    conn = sqlite3.connect(RECEIVER_DB_PATH)
    c = conn.cursor()
    if query:
        q = f"%{query}%"
        c.execute(
            """SELECT cedula, nombre, apellido, fecha_recepcion, fuente
               FROM received_records
               WHERE cedula LIKE ? OR nombre LIKE ? OR apellido LIKE ?
               ORDER BY fecha_recepcion DESC LIMIT 50""",
            (q, q, q),
        )
    else:
        c.execute(
            """SELECT cedula, nombre, apellido, fecha_recepcion, fuente
               FROM received_records
               ORDER BY fecha_recepcion DESC LIMIT 50"""
        )
    rows = c.fetchall()
    conn.close()
    return rows


def get_record_by_cedula(cedula):
    conn = sqlite3.connect(RECEIVER_DB_PATH)
    c = conn.cursor()
    c.execute(
        """SELECT cedula, nombre, apellido, data_json, fecha_recepcion, fuente
           FROM received_records WHERE cedula = ? ORDER BY fecha_recepcion DESC LIMIT 1""",
        (cedula,),
    )
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "cedula": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "data": json.loads(row[3]),
            "fecha_recepcion": row[4],
            "fuente": row[5],
        }
    return None


# ==========================================================================
# ENDPOINTS
# ==========================================================================
@app.before_request
def check_auth():
    """Autenticación simple vía API Key (si está configurada)."""
    if request.method == "OPTIONS":
        return
    if RECEIVER_API_KEY:
        auth = request.headers.get("Authorization", "")
        expected = f"Bearer {RECEIVER_API_KEY}"
        if auth != expected:
            return jsonify({"error": "No autorizado"}), 401


@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/dhp/recibir", methods=["POST"])
def recibir_dhp():
    """Recibe un formulario DHP completo desde la aplicación del usuario."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON inválido"}), 400

    cedula = (data.get("cedula") or "").strip().upper()
    nombre = (data.get("nombre") or "").strip()
    apellido = (data.get("apellido") or "").strip()
    payload = data.get("data", {})
    fuente = data.get("fuente", "desconocida")

    if not cedula:
        return jsonify({"error": "Cédula requerida"}), 400

    save_received(cedula, nombre, apellido, json.dumps(payload, ensure_ascii=False), fuente)
    print(f"[RECEPTOR] Recibido: {cedula} ({nombre} {apellido})")
    return jsonify({
        "ok": True,
        "mensaje": "Datos recibidos correctamente",
        "cedula": cedula,
    })


@app.route("/api/dhp/listar", methods=["GET"])
def listar_dhp():
    """Lista los registros recibidos, opcionalmente filtrados."""
    query = request.args.get("q", "").strip()
    rows = search_records(query)
    results = [
        {
            "cedula": r[0],
            "nombre": r[1],
            "apellido": r[2],
            "fecha_recepcion": r[3],
            "fuente": r[4],
        }
        for r in rows
    ]
    return jsonify({"ok": True, "total": len(results), "registros": results})


@app.route("/api/dhp/consulta/<cedula>", methods=["GET"])
def consulta_dhp(cedula):
    """Consulta un registro específico por cédula."""
    record = get_record_by_cedula(cedula.upper())
    if record:
        return jsonify({"ok": True, "registro": record})
    return jsonify({"error": "No encontrado"}), 404


@app.route("/api/dhp/stats", methods=["GET"])
def stats():
    """Estadísticas: total de registros."""
    conn = sqlite3.connect(RECEIVER_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM received_records")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT cedula) FROM received_records")
    distinct = c.fetchone()[0]
    conn.close()
    return jsonify({
        "ok": True,
        "total_registros": total,
        "personas_unicas": distinct,
    })


@app.route("/api/dhp/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "servicio": "DHP-Receiver",
        "base_datos": os.path.basename(RECEIVER_DB_PATH),
    })


# ==========================================================================
# INICIO
# ==========================================================================
if __name__ == "__main__":
    init_db()
    print("=" * 55)
    print("  DHP - RECEPTOR DE DATOS")
    print("=" * 55)
    print(f"  Puerto:      {RECEIVER_PORT}")
    print(f"  Base datos:  {RECEIVER_DB_PATH}")
    print(f"  API Key:     {'ACTIVADA' if RECEIVER_API_KEY else 'DESACTIVADA'}")
    print("=" * 55)
    print("  Endpoints:")
    print(f"  POST http://0.0.0.0:{RECEIVER_PORT}/api/dhp/recibir")
    print(f"  GET  http://0.0.0.0:{RECEIVER_PORT}/api/dhp/health")
    print("=" * 55)
    app.run(host="0.0.0.0", port=RECEIVER_PORT, debug=False)
