"""
Configuración central de la aplicación DHP.

Toda la configuración se lee de variables de entorno.
NO se necesita editar este archivo; usar variables de entorno.

Variables disponibles:
    DHP_API_PORT        : Puerto para la API local (defecto: 8765)
    DHP_DB_PATH         : Ruta a la base de datos SQLite (defecto: data/dhp_records.db)
    DHP_EXTERNAL_API_URL   : URL de tu API externa donde se enviarán los datos.
                                Ej: "https://tu-servidor.com/api/dhp/recibir"
                                Si está vacía, NO se envía a externo.
    DHP_EXTERNAL_API_KEY   : API Key para autenticación Bearer (opcional).
    DHP_EXTERNAL_ENABLED   : "true" para activar el envío externo automático.
                                Por defecto: "false" (solo almacenamiento local).
"""
import os
from functools import lru_cache


def _get_project_root() -> str:
    """Retorna la raíz del proyecto (donde está run.py)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_api_port() -> int:
    """Puerto para la API local."""
    return int(os.environ.get("DHP_API_PORT", "8765"))


def get_db_path() -> str:
    """Ruta completa a la base de datos SQLite local."""
    env_path = os.environ.get("DHP_DB_PATH", "").strip()
    if env_path:
        return env_path
    return os.path.join(_get_project_root(), "data", "dhp_records.db")


@lru_cache()
def get_external_api_config():
    """
    Retorna un dict con la configuración de la API externa.
    Solo se lee UNA vez (caché) para evitar leer variables de entorno repetidamente.
    """
    enabled = os.environ.get("DHP_EXTERNAL_ENABLED", "false").strip().lower() == "true"
    url = os.environ.get("DHP_EXTERNAL_API_URL", "").strip()
    key = os.environ.get("DHP_EXTERNAL_API_KEY", "").strip()
    
    return {
        "enabled": enabled,
        "url": url,
        "key": key,
    }


def is_external_enabled() -> bool:
    """¿Está habilitado el envío automático a la API externa?"""
    return get_external_api_config()["enabled"]


def get_external_url() -> str:
    """URL de la API externa."""
    return get_external_api_config()["url"]


def get_external_key() -> str:
    """API Key para la API externa."""
    return get_external_api_config()["key"]
