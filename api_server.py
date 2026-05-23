"""API REST local para que el frontend web guarde y consulte expedientes DHP."""
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

import database as db

API_PORT = int(os.environ.get("DHP_API_PORT", "8765"))

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "dhp-api"})


@app.route("/api/records", methods=["GET"])
def list_records():
    q = request.args.get("q", "").strip()
    rows = db.get_all_records(q if q else None)
    records = [
        {
            "cedula": r[0],
            "nombre": r[1],
            "apellido": r[2],
            "fecha_actualizacion": r[3],
        }
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
        db.save_or_update_record(cedula, nombre, apellido, data)
        record = db.get_record_by_cedula(cedula)
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
    db.init_db()
    app.run(host="127.0.0.1", port=API_PORT, threaded=True, use_reloader=False)


if __name__ == "__main__":
    start_api_server()
