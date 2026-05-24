#!/usr/bin/env python3
"""
Punto de entrada principal del sistema DHP.

Uso:
    python run.py                    → Inicia solo Streamlit
    python run.py --api              → Inicia solo la API local
    python run.py --receiver         → Inicia el receptor externo
    python run.py --all              → Inicia Streamlit + API
"""
import sys
import os
import subprocess
import threading
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def start_streamlit():
    """Inicia la interfaz Streamlit."""
    web_path = os.path.join(PROJECT_DIR, "app", "controllers", "web.py")
    print(f"[DHP] Iniciando Streamlit...")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", web_path],
        cwd=PROJECT_DIR,
    )


def start_api():
    """Inicia la API local en un hilo."""
    from app.controllers.api import start_api_server
    from app.models import database as db
    db.init_db()
    print(f"[DHP] Iniciando API local...")
    start_api_server()


def start_receiver():
    """Inicia el servidor receptor externo."""
    from receiver.server import app, init_db
    from receiver.server import RECEIVER_PORT, RECEIVER_DB_PATH, RECEIVER_API_KEY
    
    init_db()
    print("=" * 55)
    print("  DHP - RECEPTOR DE DATOS")
    print("=" * 55)
    print(f"  Puerto:      {RECEIVER_PORT}")
    print(f"  Base datos:  {RECEIVER_DB_PATH}")
    print(f"  API Key:     {'ACTIVADA' if RECEIVER_API_KEY else 'DESACTIVADA'}")
    print("=" * 55)
    print(f"  POST http://0.0.0.0:{RECEIVER_PORT}/api/dhp/recibir")
    print("=" * 55)
    app.run(host="0.0.0.0", port=RECEIVER_PORT, debug=False)


def start_all():
    """Inicia API + Streamlit."""
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    time.sleep(2)
    start_streamlit()


def show_help():
    print(__doc__)
    print("Opciones:")
    print("  --all        Inicia todo (API + Streamlit)")
    print("  --api        Solo API local")
    print("  --receiver   Solo receptor externo")
    print("  (sin args)   Solo Streamlit")
    print()


if __name__ == "__main__":
    # Agregar raíz del proyecto al path
    sys.path.insert(0, PROJECT_DIR)
    
    args = [a.lower() for a in sys.argv[1:]]
    
    if "--help" in args or "-h" in args:
        show_help()
    elif "--api" in args:
        start_api()
    elif "--receiver" in args:
        start_receiver()
    elif "--all" in args:
        start_all()
    else:
        start_streamlit()
