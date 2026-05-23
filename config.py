"""
Configuración central del sistema DHP.

Toda la configuración se define mediante VARIABLES DE ENTORNO.
Los usuarios finales NUNCA ven esta configuración.

Variables disponibles:
    DHP_EXTERNAL_API_URL   : URL de tu API externa donde se enviarán los datos.
                              Ej: "https://tu-servidor.com/api/dhp/recibir"
                              Si está vacía, NO se envía a externo.
    
    DHP_EXTERNAL_API_KEY   : API Key para autenticación Bearer (opcional).
    
    DHP_EXTERNAL_ENABLED   : "true" para activar el envío externo automático.
                              Por defecto: "false" (solo almacenamiento local).
    
    DHP_API_PORT           : Puerto para la API local (por defecto: 8765).
"""
import os
from functools import lru_cache


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
        "enabled": enabled and bool(url),  # Solo activo si enabled=true y hay URL
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


def get_api_port() -> int:
    """Puerto para la API local."""
    return int(os.environ.get("DHP_API_PORT", "8765"))
