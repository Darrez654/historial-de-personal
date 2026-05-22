import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pandas as pd
from datetime import datetime

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="DHP - Sistema de Declaración de Historial Personal",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para la interfaz de Streamlit
st.markdown("""
<style>
    .main-title {
        color: #1E3A8A;
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #4B5563;
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 8px 8px 0px 0px;
        gap: 8px;
        padding-left: 20px;
        padding-right: 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Directorio del proyecto
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

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
            
        # Reemplazar la referencia de style.css por el CSS inyectado
        html = html.replace('<link rel="stylesheet" href="style.css">', f'<style>\n{css}\n</style>')
        # Reemplazar la referencia de app.js por el JS inyectado
        html = html.replace('<script src="app.js"></script>', f'<script>\n{js}\n</script>')
        
        return html
    except Exception as e:
        st.error(f"Error al compilar el HTML autocontenido: {e}")
        return None

def main():
    st.markdown('<h1 class="main-title">⚓ Armada Bolivariana - Cuerpo de Ingenieros</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Declaración de Historial Personal (DHP) — Plataforma Streamlit</p>', unsafe_allow_html=True)

    # Crear pestañas para las dos opciones de visualización
    tab_iframe, tab_native = st.tabs([
        "🌐 Interfaz Web Integrada (Recomendado)",
        "🐍 Formulario Nativo Python (Edición y Exportación)"
    ])

    # ==========================================================================
    # PESTAÑA 1: APLICACIÓN WEB INTEGRADA (HTML/JS COMPLETO)
    # ==========================================================================
    with tab_iframe:
        st.info(
            "💡 **Nota de Uso:** Esta pestaña ejecuta el sistema DHP con su diseño web original. "
            "Soporta auto-guardado local en el navegador, importación/exportación de copias de seguridad en JSON, "
            "y la visualización estricta de 4 páginas de impresión oficial."
        )
        
        html_content = get_self_contained_html()
        
        if html_content:
            # Renderizar el HTML en Streamlit dentro de un Iframe
            # Se le asigna un alto generoso para interactuar de forma cómoda
            components.html(html_content, height=900, scrolling=True)
        else:
            st.error("No se pudo cargar la interfaz web. Verifique que index.html, style.css y app.js existan en la misma carpeta.")

    # ==========================================================================
    # PESTAÑA 2: FORMULARIO NATIVO DE STREAMLIT (CON EXPORTACIÓN A HTML IMPRIMIBLE)
    # ==========================================================================
    with tab_native:
        st.subheader("Formulario de Datos DHP")
        st.write("Complete la información utilizando componentes nativos de Streamlit.")

        # Inicialización de estado para persistir datos
        if 'simple_fields' not in st.session_state:
            st.session_state.simple_fields = {}

        # Crear un wizard con columnas o selectores
        step = st.selectbox("Seleccione el Paso del Formulario", [
            "Paso 1: Identificación y Fisonomía",
            "Paso 2: Datos Militares",
            "Paso 3: Datos Familiares y Viajes",
            "Paso 4: Antecedentes Laborales",
            "Paso 5: Datos Sociales",
            "Paso 6: Referencias Personales",
            "Paso 7: Datos Educativos",
            "Paso 8: Datos Administrativos e Historial"
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

        # Acciones de Backup / Generación de Datos en Python Nativo
        st.markdown("---")
        st.subheader("Guardar y Exportar Datos")
        
        # Generar JSON de Respaldo
        full_native_state = {
            "simpleFields": st.session_state.simple_fields,
            "dynamicTables": {
                "familiares": st.session_state.df_familiares.to_dict('records') if 'df_familiares' in st.session_state else [],
                "familiaresExterior": st.session_state.df_fam_exterior.to_dict('records') if 'df_fam_exterior' in st.session_state else [],
                "viajes": st.session_state.df_viajes.to_dict('records') if 'df_viajes' in st.session_state else [],
                "laboral": st.session_state.df_laboral.to_dict('records') if 'df_laboral' in st.session_state else [],
                "social": st.session_state.df_social.to_dict('records') if 'df_social' in st.session_state else []
            }
        }
        
        json_str = json.dumps(full_native_state, indent=2, ensure_ascii=False)
        st.download_button(
            label="💾 Descargar Respaldo de Datos (JSON)",
            data=json_str,
            file_name="respaldo_dhp.json",
            mime="application/json"
        )
        
        st.write("Para generar e imprimir la planilla oficial, por favor utilice la **Pestaña 1 (Interfaz Web Integrada)**, la cual tiene soporte de impresión de 4 páginas pixel-perfect optimizado con estilos CSS.")

if __name__ == "__main__":
    main()
