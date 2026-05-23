"""
╔══════════════════════════════════════════════════════════════════════════╗
║  RECEPTOR DE DATOS DHP                                                ║
║  ======================                                                ║
║                                                                        ║
║  Este servidor RECIBE los formularios DHP enviados desde el sistema    ║
║  de Declaración de Historial Personal (Cuerpo de Ingenieros de la      ║
║  Armada Bolivariana) y los almacena en su propia base de datos.        ║
║                                                                        ║
║  🌐 Despliega este archivo en tu servidor (o en cualquier hosting      ║
║     que soporte Python) para recibir los datos.                        ║
║                                                                        ║
║  PUESTA EN MARCHA:                                                     ║
║      pip install flask flask-cors                                      ║
║      python receiver_api.py                                            ║
║      # Escucha en http://0.0.0.0:5000                                  ║
║                                                                        ║
║  LUEGO CONFIGURA (en la máquina del DHP):                             ║
║      set DHP_EXTERNAL_ENABLED=true                                     ║
║      set DHP_EXTERNAL_API_URL=http://TU_IP:5000/api/dhp/recibir        ║
║      set DHP_EXTERNAL_API_KEY=mi-clave-secreta (opcional)              ║
║                                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
import os
import json
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

# ==========================================================================
# CONFIGURACIÓN
# ==========================================================================
HOST = os.environ.get("RECEIVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("RECEIVER_PORT", "5000"))
DB_PATH = os.environ.get("RECEIVER_DB_PATH", "dhp_received_records.db")
REQUIRED_API_KEY = os.environ.get("RECEIVER_API_KEY", "")
LOG_DIR = os.environ.get("RECEIVER_LOG_DIR", "logs")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Asegurar que el directorio de logs existe
os.makedirs(LOG_DIR, exist_ok=True)


# ==========================================================================
# BASE DE DATOS (receptora)
# ==========================================================================

def init_db():
    """Inicializa la base de datos receptora."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS received_dhp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT NOT NULL,
            nombre TEXT,
            apellido TEXT,
            data_json TEXT NOT NULL,
            fecha_recepcion TEXT NOT NULL,
            fuente TEXT DEFAULT 'DHP-API',
            ip_origen TEXT,
            user_agent TEXT,
            metadata_json TEXT DEFAULT '{}'
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_received_cedula 
        ON received_dhp(cedula)
    """)
    conn.commit()
    conn.close()


def save_received_record(cedula, nombre, apellido, data, fuente, ip_origen, user_agent, metadata):
    """Guarda un registro recibido en la base de datos receptora."""
    conn = sqlite3.connect(DB_PATH)
    
    # Verificar si ya existe un registro con esa cédula (update)
    existing = conn.execute(
        "SELECT id FROM received_dhp WHERE cedula = ? ORDER BY id DESC LIMIT 1",
        (cedula,)
    ).fetchone()
    
    fecha = datetime.now().isoformat()
    data_str = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
    metadata_str = json.dumps(metadata, ensure_ascii=False) if isinstance(metadata, dict) else "{}"
    
    if existing:
        conn.execute("""
            UPDATE received_dhp SET
                nombre = ?, apellido = ?, data_json = ?,
                fecha_recepcion = ?, fuente = ?, ip_origen = ?,
                user_agent = ?, metadata_json = ?
            WHERE id = ?
        """, (nombre, apellido, data_str, fecha, fuente, ip_origen,
              user_agent, metadata_str, existing[0]))
        nuevo = False
    else:
        conn.execute("""
            INSERT INTO received_dhp 
                (cedula, nombre, apellido, data_json, fecha_recepcion, 
                 fuente, ip_origen, user_agent, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cedula, nombre, apellido, data_str, fecha, fuente,
              ip_origen, user_agent, metadata_str))
        nuevo = True
    
    conn.commit()
    conn.close()
    return nuevo


def get_all_received(search=None):
    """Obtiene todos los registros recibidos, opcionalmente filtrados."""
    conn = sqlite3.connect(DB_PATH)
    if search:
        cursor = conn.execute("""
            SELECT cedula, nombre, apellido, fecha_recepcion, fuente, id
            FROM received_dhp
            WHERE cedula LIKE ? OR nombre LIKE ? OR apellido LIKE ?
            ORDER BY fecha_recepcion DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cursor = conn.execute("""
            SELECT cedula, nombre, apellido, fecha_recepcion, fuente, id
            FROM received_dhp
            ORDER BY fecha_recepcion DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_received_by_cedula(cedula):
    """Obtiene el último registro recibido por cédula."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("""
        SELECT cedula, nombre, apellido, data_json, fecha_recepcion, fuente, metadata_json
        FROM received_dhp
        WHERE cedula = ?
        ORDER BY fecha_recepcion DESC
        LIMIT 1
    """, (cedula,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "cedula": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "data": json.loads(row[3]) if row[3] else {},
            "fecha_recepcion": row[4],
            "fuente": row[5],
            "metadata": json.loads(row[6]) if row[6] else {},
        }
    return None


def log_request(cedula, status_code, ip):
    """Registra en un archivo de log la recepción."""
    log_file = os.path.join(LOG_DIR, f"dhp_receiver_{datetime.now().strftime('%Y%m')}.log")
    timestamp = datetime.now().isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] CEDULA={cedula} IP={ip} STATUS={status_code}\n")


# ==========================================================================
# MIDDLEWARE DE AUTENTICACIÓN
# ==========================================================================

def check_auth():
    """Valida la API Key si está configurada."""
    if not REQUIRED_API_KEY:
        return True  # No requiere key
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return token == REQUIRED_API_KEY
    return False


# ==========================================================================
# ENDPOINTS
# ==========================================================================

@app.route("/api/dhp/health", methods=["GET"])
def health():
    """Endpoint de salud."""
    return jsonify({
        "ok": True,
        "service": "dhp-receiver",
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/dhp/recibir", methods=["POST"])
def recibir_dhp():
    """
    ENDPOINT PRINCIPAL: Recibe el formulario DHP completo.
    
    Body esperado (JSON):
    {
        "cedula": "V-12345678",
        "nombre": "JUAN",
        "apellido": "PÉREZ",
        "data": { ... },          // Objeto completo del formulario
        "fecha_envio": "2025-...",
        "fuente": "DHP-WebApp"
    }
    """
    # Verificar autenticación
    if not check_auth():
        return jsonify({"error": "API Key inválida o ausente."}), 401
    
    # Obtener payload
    payload = request.get_json(silent=True) or {}
    
    cedula = payload.get("cedula", "").strip()
    nombre = payload.get("nombre", "").strip()
    apellido = payload.get("apellido", "").strip()
    data = payload.get("data")
    fuente = payload.get("fuente", "DHP-Desconocido")
    fecha_envio = payload.get("fecha_envio", "")
    
    if not cedula:
        return jsonify({"error": "El campo 'cedula' es obligatorio."}), 400
    if data is None:
        return jsonify({"error": "El campo 'data' es obligatorio."}), 400
    
    # Guardar
    ip_origen = request.remote_addr or "desconocida"
    user_agent = request.headers.get("User-Agent", "")
    
    metadata = {
        "fecha_envio_original": fecha_envio,
        "content_type": request.content_type or "",
    }
    
    try:
        es_nuevo = save_received_record(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            data=data,
            fuente=fuente,
            ip_origen=ip_origen,
            user_agent=user_agent,
            metadata=metadata,
        )
        
        log_request(cedula, 200, ip_origen)
        
        return jsonify({
            "ok": True,
            "mensaje": "Registro DHP recibido y almacenado correctamente.",
            "cedula": cedula,
            "nuevo": es_nuevo,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        log_request(cedula, 500, ip_origen)
        return jsonify({"error": f"Error interno al almacenar: {str(e)}"}), 500


@app.route("/api/dhp/listar", methods=["GET"])
def listar_recibidos():
    """Lista todos los registros DHP recibidos."""
    if not check_auth():
        return jsonify({"error": "API Key inválida o ausente."}), 401
    
    search = request.args.get("q", "").strip()
    rows = get_all_received(search if search else None)
    
    records = [
        {
            "cedula": r[0],
            "nombre": r[1],
            "apellido": r[2],
            "fecha_recepcion": r[3],
            "fuente": r[4],
            "id": r[5],
        }
        for r in rows
    ]
    return jsonify({"records": records, "total": len(records)})


@app.route("/api/dhp/consulta/<cedula>", methods=["GET"])
def consultar_recibido(cedula):
    """Consulta un registro DHP específico por cédula."""
    if not check_auth():
        return jsonify({"error": "API Key inválida o ausente."}), 401
    
    record = get_received_by_cedula(cedula)
    if not record:
        return jsonify({"error": "No se encontró registro con esa cédula."}), 404
    return jsonify(record)


@app.route("/api/dhp/stats", methods=["GET"])
def stats():
    """Estadísticas básicas de los registros recibidos."""
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM received_dhp").fetchone()[0]
    ultimo = conn.execute("""
        SELECT cedula, fecha_recepcion FROM received_dhp 
        ORDER BY fecha_recepcion DESC LIMIT 1
    """).fetchone()
    conn.close()
    
    return jsonify({
        "total_recibidos": total,
        "ultimo_registro": {
            "cedula": ultimo[0] if ultimo else None,
            "fecha": ultimo[1] if ultimo else None,
        } if ultimo else None,
        "timestamp": datetime.now().isoformat(),
    })


# ==========================================================================
# ARRANQUE
# ==========================================================================

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🚀 RECEPTOR DHP iniciado                                 ║
║  ──────────────────────                                    ║
║  Escuchando en: http://{HOST}:{PORT}                         ║
║  Endpoint:     POST /api/dhp/recibir                      ║
║  Base datos:   {DB_PATH}                           ║
║  Logs:         {LOG_DIR}/                                   ║
║                                                            ║
║  Para probar:                                              ║
║    curl -X POST http://localhost:{PORT}/api/dhp/recibir \\   ║
║      -H "Content-Type: application/json" \\                 ║
║      -d '{{"cedula":"V-12345678","nombre":"PRUEBA",         ║
║            "apellido":"TEST","data":{{"ok":true}}}}'        ║
╚══════════════════════════════════════════════════════════════╝
    """)
    init_db()
    app.run(host=HOST, port=PORT, debug=False)
