import streamlit as st
import anthropic
import pandas as pd
from pypdf import PdfReader
import io
import json
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import streamlit_authenticator as stauth

st.set_page_config(page_title="RecrutAI Pro", page_icon="=", layout="wide")

# ── AUTENTICACION ─────────────────────────────────────────────────────────────
credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            "password": stauth.Hasher(["admin123"]).generate()[0]
        },
        "cliente1": {
            "name": "Cliente Empresa",
            "password": stauth.Hasher(["cliente123"]).generate()[0]
        }
    }
}
authenticator = stauth.Authenticate(
    credentials, "recrutai_cookie", "recrutai_secret_key_2024", cookie_expiry_days=30
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
  .stApp, .stApp > div,
  [data-testid="stAppViewContainer"],
  [data-testid="stAppViewContainer"] > section,
  [data-testid="stAppViewContainer"] > section > div,
  .main, .block-container { background-color: #12111a !important; }
  [data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"] { background-color: transparent !important; }
  .stApp, .stApp p, .stApp span, .stApp div, .stApp label,
  .stMarkdown, .stMarkdown p { color: #f0eeff !important; }
  [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
    background-color: #1a1730 !important; border-right: 2px solid #534AB7 !important; }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span { color: #ffffff !important; font-weight: 500 !important; }
  input[type="text"], input[type="password"], .stTextInput input, .stTextArea textarea {
    background-color: #ffffff !important; color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important; border-radius: 8px !important; font-size: 14px !important; }
  input::placeholder, textarea::placeholder { color: #9490b8 !important; }
  .stSelectbox > div > div, .stSelectbox [data-baseweb="select"] > div {
    background-color: #ffffff !important; color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important; border-radius: 8px !important; }
  .stSelectbox [data-baseweb="select"] span,
  .stSelectbox [data-baseweb="select"] div { color: #1a1035 !important; }
  [data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"] {
    background-color: #ffffff !important; color: #1a1035 !important; }
  [data-baseweb="option"]:hover { background-color: #ede9ff !important; }
  .stMultiSelect > div > div {
    background-color: #ffffff !important; border: 1.5px solid #7F77DD !important;
    border-radius: 8px !important; color: #1a1035 !important; }
  .stTextArea textarea {
    background-color: #ffffff !important; color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important; border-radius: 8px !important; }
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #534AB7, #7F77DD) !important;
    border: none !important; border-radius: 10px !important;
    color: white !important; font-weight: 600 !important; font-size: 15px !important; }
  .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #6b61cc, #9890e8) !important; transform: translateY(-1px); }
  .stButton > button {
    border-radius: 8px !important; border: 1.5px solid #534AB7 !important;
    color: #e0dbff !important; background: transparent !important; }
  .stButton > button:hover { background: #26215C !important; }
  [data-testid="stFileUploader"] {
    background: #1e1b2e !important; border: 2px dashed #7F77DD !important; border-radius: 12px !important; }
  [data-testid="stFileUploader"] label,
  [data-testid="stFileUploader"] span,
  [data-testid="stFileUploader"] p { color: #f0eeff !important; }
  .stTabs [data-baseweb="tab-list"] {
    background: #1e1b2e !important; border-radius: 10px !important;
    padding: 4px !important; border: 1px solid #3C3489 !important; }
  .stTabs [data-baseweb="tab"] { color: #AFA9EC !important; border-radius: 8px !important; font-weight: 500 !important; }
  .stTabs [aria-selected="true"] { background: #534AB7 !important; color: white !important; }
  .stForm { background: #1e1b2e !important; border: 1.5px solid #534AB7 !important;
    border-radius: 16px !important; padding: 2rem !important; }
  .stForm label { color: #ffffff !important; font-weight: 600 !important; font-size: 14px !important; }
  .stForm input { background: #f5f3ff !important; color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important; border-radius: 8px !important; }
  .stProgress > div > div { background: linear-gradient(90deg, #534AB7, #AFA9EC) !important; }
  .metric-card { background: #1e1b2e; border: 1.5px solid #534AB7;
    padding: 20px; border-radius: 14px; text-align: center; }
  .metric-card h2 { font-size: 2rem; margin: 0; font-weight: 700; color: white !important; }
  .metric-card p  { margin: 4px 0 0; font-size: 13px; color: #AFA9EC !important; }
  .candidate-card, .proveedor-card { background: #1e1b2e; border: 1.5px solid #3C3489;
    border-radius: 12px; padding: 16px; margin: 8px 0; }
  .proveedor-card { border-color: #0F6E56; }
  .badge-alto   { background:#1a4731; color:#4ade80;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-medio  { background:#4a3800; color:#fbbf24;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-bajo   { background:#4a1c1c; color:#f87171;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-prov-a { background:#0a2e1f; color:#34d399;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-prov-b { background:#1a2e0a; color:#86efac;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-prov-c { background:#2e2a0a; color:#fde68a;  padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  hr { border-color: #534AB7 !important; }
  h1, h2, h3, h4 { color: #f0eeff !important; }
  [data-testid="stDataFrame"] { border: 1px solid #534AB7 !important; border-radius: 8px !important; }
  .logo-header { display: flex; align-items: center; gap: 14px; padding: 0 0 1rem 0; }
  .logo-icon { width: 48px; height: 48px; border-radius: 12px;
    background: linear-gradient(135deg, #534AB7, #7F77DD);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 800; color: white; }
</style>
""", unsafe_allow_html=True)

# ── LOGIN ─────────────────────────────────────────────────────────────────────
def mostrar_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0 1.5rem;">
          <div style="width:64px;height:64px;border-radius:16px;
               background:linear-gradient(135deg,#534AB7,#7F77DD);
               display:inline-flex;align-items:center;justify-content:center;
               font-size:28px;font-weight:800;color:white;margin-bottom:16px;">RA</div>
          <h2 style="color:#f0eeff;margin:0;font-size:1.8rem;font-weight:700;">RecrutAI Pro</h2>
          <p style="color:#AFA9EC;margin:4px 0 0;font-size:14px;letter-spacing:2px;">POWERED BY CLAUDE AI</p>
        </div>""", unsafe_allow_html=True)

name, authentication_status, username = authenticator.login(
    fields={"Form name": "Iniciar sesion", "Username": "Usuario", "Password": "Contrasena", "Login": "Entrar"}
)
if authentication_status == False:
    mostrar_login(); st.error("Usuario o contrasena incorrectos"); st.stop()
if authentication_status is None:
    mostrar_login(); st.info("Ingresa tus credenciales para acceder"); st.stop()

# ── API ───────────────────────────────────────────────────────────────────────
try:
    api_key_segura = st.secrets["CLAUDE_API_KEY"]
except Exception:
    st.error("No se encontro la API Key en los Secrets de Streamlit Cloud."); st.stop()
client = anthropic.Anthropic(api_key=api_key_segura)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "df_candidatos"   not in st.session_state: st.session_state.df_candidatos   = None
if "df_proveedores"  not in st.session_state: st.session_state.df_proveedores  = None
if "proveedores_web" not in st.session_state: st.session_state.proveedores_web = []
if "modulo_activo"   not in st.session_state: st.session_state.modulo_activo   = "cvs"

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:12px 0 8px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
        <div style="width:36px;height:36px;border-radius:9px;
             background:linear-gradient(135deg,#534AB7,#7F77DD);
             display:flex;align-items:center;justify-content:center;
             font-size:15px;font-weight:800;color:white;">RA</div>
        <div>
          <div style="color:#ffffff;font-weight:700;font-size:15px;">RecrutAI Pro</div>
          <div style="color:#AFA9EC;font-size:11px;letter-spacing:1px;">POWERED BY CLAUDE AI</div>
        </div>
      </div>
      <div style="color:#e0dbff;font-size:12px;margin-top:8px;">
        Bienvenido, <strong style="color:white;">{name}</strong>
      </div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    modulo = st.radio("Modulo activo", ["Analisis de CVs", "Analisis de Proveedores"],
                      index=0 if st.session_state.modulo_activo == "cvs" else 1)
    st.session_state.modulo_activo = "cvs" if "CVs" in modulo else "proveedores"
    st.divider()

    if st.session_state.modulo_activo == "cvs":
        st.markdown("<p style='color:#ffffff;font-size:15px;font-weight:700;margin-bottom:12px;'>Configurar Puesto</p>", unsafe_allow_html=True)
        puesto          = st.text_input("Nombre del puesto", placeholder="Ej: Analista de Datos")
        experiencia_min = st.slider("\U0001f4c5 A\u00f1os m\u00ednimos de experiencia", 0, 20, 2)
        educacion_req   = st.selectbox("Educacion minima", ["Cualquiera","Tecnico","Bachiller","Licenciatura","Maestria","Doctorado"])
        habilidades_req = st.text_area("Habilidades requeridas (una por linea)", placeholder="Python\nExcel\nSQL")
        idioma_req      = st.selectbox("Idioma requerido", ["No requerido","Ingles","Ingles avanzado","Portugues","Frances"])
        st.divider()
        st.markdown("<p style='color:#ffffff;font-weight:700;margin-bottom:4px;'>Pesos de puntuacion</p>", unsafe_allow_html=True)
        peso_exp = st.slider("Experiencia", 0, 100, 35)
        peso_edu = st.slider("Educacion",   0, 100, 25)
        peso_hab = st.slider("Habilidades", 0, 100, 30)
        peso_idi = st.slider("Idiomas",     0, 100, 10)
    else:
        st.markdown("<p style='color:#ffffff;font-size:15px;font-weight:700;margin-bottom:12px;'>Configurar Busqueda</p>", unsafe_allow_html=True)
        pais_busqueda   = st.text_input("Pais o region", placeholder="Ej: Peru, LATAM, Espana")
        rubro_busqueda  = st.text_input("Rubro o industria", placeholder="Ej: Software, Logistica")
        presupuesto_ref = st.selectbox("Presupuesto referencial", ["No especificado","< $10,000","$10,000 - $50,000","$50,000 - $200,000","> $200,000"])
        cert_requeridas = st.text_area("Certificaciones requeridas (una por linea)", placeholder="ISO 9001\nAWS Certified")
        cobertura_req   = st.selectbox("Cobertura geografica minima", ["Local","Nacional","Regional LATAM","Internacional"])
        st.divider()
        st.markdown("<p style='color:#ffffff;font-weight:700;margin-bottom:4px;'>Pesos de evaluacion</p>", unsafe_allow_html=True)
        ppeso_precio = st.slider("Precio/Condiciones", 0, 100, 30)
        ppeso_cert   = st.slider("Certificaciones",    0, 100, 25)
        ppeso_rep    = st.slider("Reputacion",         0, 100, 25)
        ppeso_cob    = st.slider("Cobertura",          0, 100, 20)

    st.divider()
    authenticator.logout("Cerrar sesion", "sidebar")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="logo-header">
  <div class="logo-icon">RA</div>
  <div>
    <h1 style="margin:0;font-size:1.9rem;font-weight:700;color:#f0eeff !important;">RecrutAI Pro</h1>
    <p style="margin:0;color:#AFA9EC;font-size:13px;letter-spacing:2px;">PLATAFORMA INTELIGENTE DE RECLUTAMIENTO Y PROVEEDORES</p>
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── HELPERS ───────────────────────────────────────────────────────────────────
def limpiar_json(texto):
    texto = texto.strip()
    if "```" in texto:
        partes = texto.split("```")
        for p in partes:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{") or p.startswith("["):
                texto = p
                break
    inicio = texto.find("{")
    fin    = texto.rfind("}") + 1
    if inicio == -1 or fin == 0:
        raise ValueError("No se encontro JSON en la respuesta")
    return json.loads(texto[inicio:fin])

def safe_float(val):
    try:
        return float(str(val).replace(",", "."))
    except:
        return 0.0

def exportar_excel_cvs(df_exp):
    """Excel de CVs con fondo blanco, texto negro y columnas bien dimensionadas."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_exp.to_excel(writer, index=False, sheet_name="Candidatos")
        ws = writer.sheets["Candidatos"]
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side, GradientFill

        header_fill = PatternFill(start_color="26215C", end_color="26215C", fill_type="solid")
        alto_fill   = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        medio_fill  = PatternFill(start_color="FFF9E6", end_color="FFF9E6", fill_type="solid")
        bajo_fill   = PatternFill(start_color="FDECEA", end_color="FDECEA", fill_type="solid")
        par_fill    = PatternFill(start_color="F5F3FF", end_color="F5F3FF", fill_type="solid")
        blanco_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        borde = Border(
            left=Side(style="thin",   color="CCCCCC"),
            right=Side(style="thin",  color="CCCCCC"),
            top=Side(style="thin",    color="CCCCCC"),
            bottom=Side(style="thin", color="CCCCCC")
        )

        # Anchos por columna
        anchos = {
            "Ranking": 8, "Nombre": 24, "Correo": 30, "Telefono": 16,
            "Educacion_Maxima": 20, "Universidad": 26, "Carrera": 22,
            "Ultimo_Cargo": 26, "Ultima_Empresa": 24, "Experiencia_Anos": 14,
            "Habilidades_Tecnicas": 38, "Habilidades_Blandas": 30,
            "Idiomas": 16, "Certificaciones": 26, "Puntaje": 10,
            "Nivel_Potencial": 16, "Justificacion": 44,
            "Cumple_Requisitos": 16, "Requisitos_Cumplidos": 32,
            "Requisitos_Faltantes": 32, "Archivo": 30,
        }

        # Encabezados
        for cn, col in enumerate(df_exp.columns, 1):
            c = ws.cell(row=1, column=cn)
            c.value     = col.replace("_", " ")
            c.font      = Font(bold=True, color="FFFFFF", size=11, name="Calibri")
            c.fill      = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border    = borde
            letra = c.column_letter
            ws.column_dimensions[letra].width = anchos.get(col, 20)

        ws.row_dimensions[1].height = 36

        # Filas de datos
        nivel_col_idx = None
        for ci, col in enumerate(df_exp.columns, 1):
            if col == "Nivel_Potencial":
                nivel_col_idx = ci
                break

        for rn, (_, row_data) in enumerate(df_exp.iterrows(), 2):
            nivel = str(row_data.get("Nivel_Potencial", ""))
            if nivel == "Alto":
                fila_fill = alto_fill
                nivel_color = "1B5E20"
            elif nivel == "Medio":
                fila_fill = medio_fill
                nivel_color = "E65100"
            elif nivel == "Bajo":
                fila_fill = bajo_fill
                nivel_color = "B71C1C"
            else:
                fila_fill = par_fill if rn % 2 == 0 else blanco_fill
                nivel_color = "000000"

            for cn in range(1, len(df_exp.columns) + 1):
                c = ws.cell(row=rn, column=cn)
                c.font      = Font(size=10, name="Calibri", color="1a1035")
                c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                c.border    = borde
                c.fill      = fila_fill
                # Columna Nivel_Potencial con color especial
                if cn == nivel_col_idx:
                    c.font = Font(size=10, name="Calibri", bold=True, color=nivel_color)
                # Columna Puntaje en negrita
                if df_exp.columns[cn-1] == "Puntaje":
                    c.font = Font(size=11, name="Calibri", bold=True, color="26215C")
                    c.alignment = Alignment(horizontal="center", vertical="center")

            ws.row_dimensions[rn].height = 38

        # Congelar primera fila
        ws.freeze_panes = "A2"

    return output.getvalue()


def exportar_excel_proveedores(df_exp):
    """Excel de proveedores con fondo blanco, texto negro y columnas bien dimensionadas."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_exp.to_excel(writer, index=False, sheet_name="Proveedores")
        ws = writer.sheets["Proveedores"]
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

        header_fill  = PatternFill(start_color="085041", end_color="085041", fill_type="solid")
        muy_rec_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
        rec_fill     = PatternFill(start_color="E3F2FD", end_color="E3F2FD", fill_type="solid")
        viable_fill  = PatternFill(start_color="FFF9E6", end_color="FFF9E6", fill_type="solid")
        norec_fill   = PatternFill(start_color="FDECEA", end_color="FDECEA", fill_type="solid")
        par_fill     = PatternFill(start_color="F0FFF4", end_color="F0FFF4", fill_type="solid")
        blanco_fill  = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        borde = Border(
            left=Side(style="thin",   color="CCCCCC"),
            right=Side(style="thin",  color="CCCCCC"),
            top=Side(style="thin",    color="CCCCCC"),
            bottom=Side(style="thin", color="CCCCCC")
        )

        anchos = {
            "nombre": 26, "nombre_empresa": 26, "descripcion": 40,
            "sitio_web": 30, "pais_sede": 14, "cobertura": 16,
            "anos_experiencia": 14, "certificaciones": 28,
            "productos_servicios": 36, "rango_precio": 20,
            "condiciones_comerciales": 30, "tiempo_entrega": 16,
            "clientes_referencia": 30, "fortalezas": 36, "debilidades": 30,
            "puntaje_precio": 12, "puntaje_certificaciones": 16,
            "puntaje_reputacion": 14, "puntaje_cobertura": 14,
            "puntaje_recomendacion": 16, "nivel_recomendacion": 20,
            "justificacion": 44, "razon_recomendacion": 44,
            "cumple_certificaciones": 18, "certificaciones_faltantes": 30,
            "contacto": 24, "Archivo": 30, "Fuente": 14,
        }

        # Mapa de nombres legibles con tildes para encabezados Excel Proveedores
        nombres_col_prov = {
            "nombre": "Nombre", "nombre_empresa": "Nombre Empresa",
            "descripcion": "Descripci\u00f3n", "sitio_web": "Sitio Web",
            "pais_sede": "Pa\u00eds Sede", "cobertura": "Cobertura",
            "anos_experiencia": "A\u00f1os de Experiencia",
            "certificaciones": "Certificaciones", "productos_servicios": "Productos / Servicios",
            "rango_precio": "Rango de Precio", "condiciones_comerciales": "Condiciones Comerciales",
            "tiempo_entrega": "Tiempo de Entrega", "clientes_referencia": "Clientes de Referencia",
            "fortalezas": "Fortalezas", "debilidades": "Debilidades",
            "puntaje_precio": "Puntaje Precio", "puntaje_certificaciones": "Puntaje Certificaciones",
            "puntaje_reputacion": "Puntaje Reputaci\u00f3n", "puntaje_cobertura": "Puntaje Cobertura",
            "puntaje_recomendacion": "Puntaje General", "nivel_recomendacion": "Nivel de Recomendaci\u00f3n",
            "justificacion": "Justificaci\u00f3n", "razon_recomendacion": "Raz\u00f3n de Recomendaci\u00f3n",
            "cumple_certificaciones": "Cumple Certificaciones",
            "certificaciones_faltantes": "Certificaciones Faltantes",
            "contacto": "Contacto", "Archivo": "Archivo", "Fuente": "Fuente",
        }

        # Encabezados
        for cn, col in enumerate(df_exp.columns, 1):
            c = ws.cell(row=1, column=cn)
            c.value     = nombres_col_prov.get(col, col.replace("_", " ").title())
            c.font      = Font(bold=True, color="FFFFFF", size=11, name="Calibri")
            c.fill      = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border    = borde
            ws.column_dimensions[c.column_letter].width = anchos.get(col, 20)

        ws.row_dimensions[1].height = 36

        # Detectar columna nivel
        nivel_col_idx = None
        for ci, col in enumerate(df_exp.columns, 1):
            if col in ("nivel_recomendacion", "Nivel_recomendacion"):
                nivel_col_idx = ci
                break

        for rn, (_, row_data) in enumerate(df_exp.iterrows(), 2):
            nivel = str(row_data.get("nivel_recomendacion", ""))
            if "Muy" in nivel:
                fila_fill   = muy_rec_fill
                nivel_color = "1B5E20"
            elif nivel == "Recomendado":
                fila_fill   = rec_fill
                nivel_color = "0D47A1"
            elif "viable" in nivel.lower():
                fila_fill   = viable_fill
                nivel_color = "E65100"
            elif "No" in nivel:
                fila_fill   = norec_fill
                nivel_color = "B71C1C"
            else:
                fila_fill   = par_fill if rn % 2 == 0 else blanco_fill
                nivel_color = "000000"

            for cn in range(1, len(df_exp.columns) + 1):
                c = ws.cell(row=rn, column=cn)
                c.font      = Font(size=10, name="Calibri", color="1a2e1a")
                c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                c.border    = borde
                c.fill      = fila_fill
                if cn == nivel_col_idx:
                    c.font = Font(size=10, name="Calibri", bold=True, color=nivel_color)
                col_name = df_exp.columns[cn-1]
                if "puntaje" in col_name:
                    c.font      = Font(size=11, name="Calibri", bold=True, color="085041")
                    c.alignment = Alignment(horizontal="center", vertical="center")

            ws.row_dimensions[rn].height = 38

        ws.freeze_panes = "A2"

    return output.getvalue()


PURPLE = ["#26215C","#3C3489","#534AB7","#7F77DD","#AFA9EC","#CECBF6"]
VERDE  = ["#04342C","#085041","#0F6E56","#1D9E75","#5DCAA5","#9FE1CB"]
LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f0eeff")

# ══════════════════════════════════════════════════════════════════════════════
# MODULO 1: CVs
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.modulo_activo == "cvs":
    st.markdown("## Modulo de Analisis de CVs")

    uploaded_files = st.file_uploader("Sube los CVs en PDF", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        st.info(f"{len(uploaded_files)} archivo(s) cargado(s) y listo(s) para procesar.")

    if uploaded_files and st.button("Procesar y Clasificar Candidatos", type="primary", use_container_width=True):
        resultados = []
        pb   = st.progress(0)
        stxt = st.empty()
        habilidades_lista = [h.strip().lower() for h in habilidades_req.split("\n") if h.strip()]

        for idx, file in enumerate(uploaded_files):
            stxt.markdown(f"Analizando **{idx+1}/{len(uploaded_files)}**: {file.name}")
            try:
                reader = PdfReader(file)
                texto  = "".join(p.extract_text() or "" for p in reader.pages)
            except Exception as e:
                st.error(f"Error leyendo {file.name}: {e}"); continue

            prompt = (
                f'Eres un reclutador experto. Analiza este CV para el puesto de "{puesto or "No especificado"}".\n'
                f'Responde EXCLUSIVAMENTE con un objeto JSON valido, sin texto adicional ni markdown.\n\n'
                f'Formato JSON requerido:\n'
                f'{{"Nombre":"","Correo":"","Telefono":"","Educacion_Maxima":"","Universidad":"","Carrera":"",'
                f'"Ultimo_Cargo":"","Ultima_Empresa":"","Experiencia_Anos":0,"Habilidades_Tecnicas":"",'
                f'"Habilidades_Blandas":"","Idiomas":"","Certificaciones":"","Puntaje":0,'
                f'"Nivel_Potencial":"","Justificacion":"","Cumple_Requisitos":false,'
                f'"Requisitos_Cumplidos":"","Requisitos_Faltantes":""}}\n\n'
                f'Instrucciones:\n'
                f'- Puntaje 1-10: experiencia ({peso_exp}%), educacion ({peso_edu}%), '
                f'habilidades requeridas: {", ".join(habilidades_lista) or "no especificadas"} ({peso_hab}%), '
                f'idiomas: {idioma_req} ({peso_idi}%)\n'
                f'- Nivel_Potencial: "Alto" si >= 7, "Medio" si >= 4, "Bajo" si < 4\n'
                f'- Cumple_Requisitos: true si experiencia >= {experiencia_min} y puntaje >= 6\n'
                f'- Experiencia_Anos: solo numero entero\n'
                f'- Habilidades_Tecnicas: maximo 6, separadas por coma\n'
                f'- Si un dato no existe: "No especifica"\n\n'
                f'CV:\n{texto[:4000]}'
            )

            try:
                msg   = client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=1200,
                            messages=[{"role": "user", "content": prompt}])
                datos = limpiar_json(msg.content[0].text)
                datos["Archivo"] = file.name
                resultados.append(datos)
            except Exception as e:
                st.error(f"Error procesando {file.name}: {e}")
            pb.progress((idx + 1) / len(uploaded_files))

        if resultados:
            df = pd.DataFrame(resultados)
            df["Experiencia_Anos"] = pd.to_numeric(df["Experiencia_Anos"], errors="coerce").fillna(0).astype(int)
            df["Puntaje"]          = pd.to_numeric(df["Puntaje"],          errors="coerce").fillna(0)
            df = df.sort_values("Puntaje", ascending=False).reset_index(drop=True)
            df["Ranking"] = df.index + 1
            st.session_state.df_candidatos = df
            stxt.success(f"{len(resultados)} CVs procesados correctamente.")

    if st.session_state.df_candidatos is not None:
        df = st.session_state.df_candidatos.copy()
        tab1, tab2, tab3, tab4 = st.tabs(["Ranking", "Dashboards", "Filtros", "Exportar"])

        with tab1:
            st.markdown("## Ranking de Candidatos")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="metric-card"><h2>{len(df)}</h2><p>Total CVs</p></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h2 style="color:#4ade80">{len(df[df["Nivel_Potencial"]=="Alto"])}</h2><p>Alto Potencial</p></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><h2 style="color:#fbbf24">{len(df[df["Nivel_Potencial"]=="Medio"])}</h2><p>Potencial Medio</p></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><h2 style="color:#AFA9EC">{len(df[df["Cumple_Requisitos"]==True])}</h2><p>Cumplen Requisitos</p></div>', unsafe_allow_html=True)
            st.markdown("### Top Candidatos")
            for _, row in df.head(20).iterrows():
                nivel  = row.get("Nivel_Potencial", "Bajo")
                badge  = "badge-alto" if nivel == "Alto" else "badge-medio" if nivel == "Medio" else "badge-bajo"
                cumple = "Cumple requisitos" if row.get("Cumple_Requisitos") else "No cumple"
                st.markdown(f"""<div class="candidate-card">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div><strong style="font-size:16px;color:#f0eeff;">#{row['Ranking']} {row.get('Nombre','N/A')}</strong>
                      &nbsp;<span class="{badge}">{nivel}</span>
                      &nbsp;<small style="color:#AFA9EC;">{cumple}</small></div>
                    <span style="font-size:26px;font-weight:700;color:#7F77DD;">{row.get('Puntaje',0)}/10</span>
                  </div>
                  <div style="margin-top:8px;color:#c4bfee;font-size:13px;">
                    {row.get('Ultimo_Cargo','N/A')} en {row.get('Ultima_Empresa','N/A')}
                    &nbsp;|&nbsp;{row.get('Experiencia_Anos',0)} a\u00f1os
                    &nbsp;|&nbsp;{row.get('Educacion_Maxima','N/A')}
                  </div>
                  <div style="margin-top:6px;color:#9890cc;font-size:12px;font-style:italic;">{row.get('Justificacion','')}</div>
                </div>""", unsafe_allow_html=True)

        with tab2:
            st.markdown("## Dashboards y M\u00e9tricas")
            col_a, col_b = st.columns(2)
            with col_a:
                cnt = df["Nivel_Potencial"].value_counts().reset_index(); cnt.columns = ["Nivel","Cantidad"]
                fig1 = px.pie(cnt, values="Cantidad", names="Nivel", title="Distribucion por Potencial", hole=0.45,
                              color="Nivel", color_discrete_map={"Alto":"#4ade80","Medio":"#fbbf24","Bajo":"#f87171"})
                fig1.update_layout(**LAYOUT); st.plotly_chart(fig1, use_container_width=True)
            with col_b:
                edu = df["Educacion_Maxima"].value_counts().reset_index(); edu.columns = ["Educacion","Cantidad"]
                fig2 = px.bar(edu, x="Cantidad", y="Educacion", orientation="h", title="Nivel Educativo",
                              color="Cantidad", color_continuous_scale=PURPLE)
                fig2.update_layout(**LAYOUT); st.plotly_chart(fig2, use_container_width=True)
            col_c, col_d = st.columns(2)
            with col_c:
                all_hab = []
                for h in df["Habilidades_Tecnicas"].dropna():
                    all_hab.extend([x.strip() for x in str(h).split(",") if x.strip() and x.strip() != "No especifica"])
                if all_hab:
                    df_h = pd.DataFrame(Counter(all_hab).most_common(12), columns=["Habilidad","Frecuencia"])
                    fig3 = px.bar(df_h, x="Frecuencia", y="Habilidad", orientation="h", title="Habilidades Tecnicas",
                                  color="Frecuencia", color_continuous_scale=PURPLE)
                    fig3.update_layout(**LAYOUT); st.plotly_chart(fig3, use_container_width=True)
            with col_d:
                fig4 = px.scatter(df, x="Experiencia_Anos", y="Puntaje", color="Nivel_Potencial",
                                  hover_data=["Nombre","Ultimo_Cargo"], title="Experiencia vs Puntaje",
                                  color_discrete_map={"Alto":"#4ade80","Medio":"#fbbf24","Bajo":"#f87171"})
                fig4.update_layout(**LAYOUT); st.plotly_chart(fig4, use_container_width=True)
            k1, k2, k3, k4 = st.columns(4)
            with k1: st.metric("Experiencia Promedio", f"{df['Experiencia_Anos'].mean():.1f} a\u00f1os")
            with k2: st.metric("Puntaje Promedio",     f"{df['Puntaje'].mean():.1f}/10")
            with k3: st.metric("Cumple Requisitos",    f"{len(df[df['Cumple_Requisitos']==True])/len(df)*100:.0f}%")
            with k4: st.metric("Alto Potencial",       f"{len(df[df['Nivel_Potencial']=='Alto'])/len(df)*100:.0f}%")

        with tab3:
            st.markdown("## Filtros en Tiempo Real")
            f1, f2, f3, f4 = st.columns(4)
            with f1: fp  = st.multiselect("Potencial", ["Alto","Medio","Bajo"], default=["Alto","Medio","Bajo"])
            with f2: fe  = st.slider("Exp. m\u00ednima (a\u00f1os)", 0, 20, 0)
            with f3: fpu = st.slider("Puntaje m\u00ednimo", 0.0, 10.0, 0.0, 0.5)
            with f4: fc  = st.selectbox("Cumple req.", ["Todos","Solo los que cumplen","Solo los que no cumplen"])
            fn = st.text_input("Buscar nombre, cargo o habilidad")
            df_f = df[df["Nivel_Potencial"].isin(fp)]
            df_f = df_f[df_f["Experiencia_Anos"] >= fe]
            df_f = df_f[df_f["Puntaje"] >= fpu]
            if fc == "Solo los que cumplen":     df_f = df_f[df_f["Cumple_Requisitos"] == True]
            elif fc == "Solo los que no cumplen": df_f = df_f[df_f["Cumple_Requisitos"] == False]
            if fn:
                mask = (df_f["Nombre"].str.contains(fn, case=False, na=False) |
                        df_f["Ultimo_Cargo"].str.contains(fn, case=False, na=False) |
                        df_f["Habilidades_Tecnicas"].str.contains(fn, case=False, na=False))
                df_f = df_f[mask]
            st.markdown(f"**{len(df_f)} candidatos encontrados**")
            cols_show = ["Ranking","Nombre","Puntaje","Nivel_Potencial","Ultimo_Cargo",
                         "Experiencia_Anos","Educacion_Maxima","Habilidades_Tecnicas","Idiomas","Correo","Cumple_Requisitos"]
            st.dataframe(df_f[[c for c in cols_show if c in df_f.columns]], use_container_width=True, height=500)

        with tab4:
            st.markdown("## Exportar Resultados")
            op = st.radio("Que candidatos exportar?", ["Todos","Solo Alto Potencial","Solo los que cumplen","Top 10"])
            df_exp = df.copy()
            if op == "Solo Alto Potencial":    df_exp = df[df["Nivel_Potencial"] == "Alto"]
            elif op == "Solo los que cumplen": df_exp = df[df["Cumple_Requisitos"] == True]
            elif op == "Top 10":               df_exp = df.head(10)
            st.info(f"Se exportaran **{len(df_exp)} candidatos**")
            st.download_button("Descargar Excel de CVs", data=exportar_excel_cvs(df_exp),
                file_name="RecrutAI_CVs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODULO 2: PROVEEDORES
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## Modulo de An\u00e1lisis de Proveedores")

    tab_buscar, tab_subir, tab_comparar, tab_dash, tab_export = st.tabs([
        "Buscar en Internet", "Analizar Documentos", "Comparar Proveedores", "Dashboards", "Exportar"
    ])

    with tab_buscar:
        st.markdown("### B\u00fasqueda de Proveedores en Internet")
        st.markdown("<p style='color:#AFA9EC;'>Describe con todo el detalle que necesites. La busqueda sera precisa sin importar que tan larga o especifica sea.</p>", unsafe_allow_html=True)

        col_q1, col_q2 = st.columns([3, 1])
        with col_q1:
            query_usuario = st.text_area(
                "Describe con detalle que proveedor necesitas",
                placeholder="Ej: Necesito proveedores de servicios de nomina y RRHH para una empresa de 200 empleados en Peru, con soporte en espanol, experiencia en retail, certificacion ISO y presupuesto de $20,000 anuales.",
                height=120
            )
        with col_q2:
            num_resultados   = st.selectbox("Cantidad de proveedores", [5, 8, 10, 15], index=1)
            incluir_precios  = st.checkbox("Incluir rango de precios", value=True)
            incluir_contacto = st.checkbox("Incluir contacto/web",    value=True)

        if st.button("Buscar Proveedores", type="primary", use_container_width=True):
            if not query_usuario.strip():
                st.warning("Por favor describe que proveedor necesitas.")
            else:
                contexto = (
                    f"Pais/region: {pais_busqueda or 'no especificado'} | "
                    f"Rubro: {rubro_busqueda or 'no especificado'} | "
                    f"Presupuesto: {presupuesto_ref} | "
                    f"Cobertura requerida: {cobertura_req}"
                )

                st.info("Paso 1/3: Identificando empresas relevantes en internet...")
                prompt_paso1 = (
                    f"Busca en internet empresas reales que ofrezcan lo siguiente: {query_usuario}\n"
                    f"Contexto adicional: {contexto}\n\n"
                    f"Lista exactamente {num_resultados} empresas reales y verificadas.\n"
                    f"Responde SOLO con JSON valido, sin texto adicional:\n"
                    f'{{"empresas": [{{"nombre": "Nombre empresa", "descripcion_breve": "que hace en una linea", "sitio_web": "https://..."}}]}}'
                )

                empresas_encontradas = []
                try:
                    msg1 = client.messages.create(
                        model="claude-sonnet-4-6", max_tokens=2000,
                        tools=[{"type": "web_search_20250305", "name": "web_search"}],
                        messages=[{"role": "user", "content": prompt_paso1}]
                    )
                    texto1 = "".join(b.text for b in msg1.content if hasattr(b, "text"))
                    datos1 = limpiar_json(texto1)
                    empresas_encontradas = datos1.get("empresas", [])
                    st.success(f"Paso 1 completado: {len(empresas_encontradas)} empresas identificadas.")
                except Exception as e:
                    st.error(f"Error en paso 1: {e}")

                if empresas_encontradas:
                    st.info(f"Paso 2/3: Analizando cada empresa en detalle...")
                    proveedores_detallados = []
                    pb = st.progress(0)

                    for i, empresa in enumerate(empresas_encontradas):
                        nombre_emp = empresa.get("nombre", "")
                        desc_emp   = empresa.get("descripcion_breve", "")
                        web_emp    = empresa.get("sitio_web", "")

                        prompt_paso2 = (
                            f'Analiza la empresa "{nombre_emp}" (web: {web_emp}) como proveedor para: {query_usuario}\n'
                            f"Contexto del cliente: {contexto}\n\n"
                            f"Busca informacion real y detallada de esta empresa.\n"
                            f"Responde SOLO con JSON valido, sin texto adicional:\n"
                            f'{{"nombre": "{nombre_emp}", '
                            f'"descripcion": "descripcion completa", '
                            f'"sitio_web": "{web_emp}", '
                            f'"pais_sede": "pais", '
                            f'"cobertura": "Local o Nacional o Regional o Internacional", '
                            f'"anos_experiencia": "numero o rango", '
                            f'"certificaciones": "lista o No especifica", '
                            f'"rango_precio": "rango estimado o No publico", '
                            f'"contacto": "email o telefono real", '
                            f'"fortalezas": "fortaleza1, fortaleza2, fortaleza3", '
                            f'"clientes_referencia": "clientes conocidos o No publico", '
                            f'"puntaje_recomendacion": 8, '
                            f'"nivel_recomendacion": "Muy recomendado", '
                            f'"razon_recomendacion": "razon especifica para este caso"}}'
                        )

                        try:
                            msg2 = client.messages.create(
                                model="claude-sonnet-4-6", max_tokens=1000,
                                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                                messages=[{"role": "user", "content": prompt_paso2}]
                            )
                            texto2 = "".join(b.text for b in msg2.content if hasattr(b, "text"))
                            datos2 = limpiar_json(texto2)
                            proveedores_detallados.append(datos2)
                        except Exception:
                            proveedores_detallados.append({
                                "nombre": nombre_emp, "descripcion": desc_emp,
                                "sitio_web": web_emp, "pais_sede": "No especifica",
                                "cobertura": "No especifica", "anos_experiencia": "No especifica",
                                "certificaciones": "No especifica", "rango_precio": "No especifica",
                                "contacto": "No especifica",
                                "fortalezas": "Ver sitio web para mas detalles",
                                "clientes_referencia": "No publico",
                                "puntaje_recomendacion": 7, "nivel_recomendacion": "Recomendado",
                                "razon_recomendacion": "Empresa identificada como relevante"
                            })
                        pb.progress((i + 1) / len(empresas_encontradas))

                    st.info("Paso 3/3: Generando resumen del mercado...")
                    try:
                        nombres_lista = ", ".join([p.get("nombre","") for p in proveedores_detallados])
                        msg3 = client.messages.create(
                            model="claude-haiku-4-5-20251001", max_tokens=300,
                            messages=[{"role": "user", "content":
                                f"Genera un resumen ejecutivo breve (2-3 oraciones) del mercado de proveedores para: {query_usuario}\n"
                                f"Empresas encontradas: {nombres_lista}\n"
                                f'Responde SOLO con JSON: {{"resumen": "texto del resumen"}}'
                            }]
                        )
                        datos3 = limpiar_json(msg3.content[0].text)
                        resumen = datos3.get("resumen", "")
                        if resumen:
                            st.info(f"Analisis del mercado: {resumen}")
                    except:
                        pass

                    st.session_state.proveedores_web = proveedores_detallados
                    st.success(f"Busqueda completada: {len(proveedores_detallados)} proveedores analizados.")

        if st.session_state.proveedores_web:
            provs = st.session_state.proveedores_web
            provs_sorted = sorted(provs, key=lambda x: safe_float(x.get("puntaje_recomendacion", 0)), reverse=True)
            st.markdown(f"### {len(provs_sorted)} Proveedores Encontrados")

            for i, prov in enumerate(provs_sorted, 1):
                puntaje_num = safe_float(prov.get("puntaje_recomendacion", 0))
                nivel_texto = prov.get("nivel_recomendacion", "Recomendado")
                badge_c = "badge-prov-a" if puntaje_num >= 8 else "badge-prov-b" if puntaje_num >= 6 else "badge-prov-c"
                st.markdown(f"""
                <div class="proveedor-card">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;">
                      <strong style="font-size:16px;color:#f0eeff;">#{i} {prov.get('nombre','N/A')}</strong>
                      &nbsp;<span class="{badge_c}">{nivel_texto}</span>
                      <div style="margin-top:6px;color:#c4bfee;font-size:13px;">{prov.get('descripcion','')}</div>
                    </div>
                    <div style="text-align:right;min-width:70px;">
                      <span style="font-size:26px;font-weight:700;color:#34d399;">{prov.get('puntaje_recomendacion',0)}/10</span>
                    </div>
                  </div>
                  <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:#AFA9EC;">
                    <span>Pa\u00eds: {prov.get('pais_sede','N/A')}</span>
                    <span>Cobertura: {prov.get('cobertura','N/A')}</span>
                    <span>Experiencia: {prov.get('anos_experiencia','N/A')} a\u00f1os</span>
                    <span>Precio: {prov.get('rango_precio','N/A')}</span>
                    <span>Certificaciones: {prov.get('certificaciones','N/A')}</span>
                  </div>
                  <div style="margin-top:8px;font-size:12px;color:#AFA9EC;">
                    Web: <a href="{prov.get('sitio_web','#')}" target="_blank" style="color:#7F77DD;">{prov.get('sitio_web','N/A')}</a>
                    &nbsp;|&nbsp; Contacto: {prov.get('contacto','N/A')}
                  </div>
                  <div style="margin-top:6px;font-size:12px;color:#86efac;">{prov.get('fortalezas','')}</div>
                  <div style="margin-top:4px;font-size:11px;color:#9890cc;font-style:italic;">{prov.get('razon_recomendacion','')}</div>
                </div>""", unsafe_allow_html=True)

            if st.button("Agregar al comparador", use_container_width=True):
                df_web = pd.DataFrame(provs_sorted)
                if st.session_state.df_proveedores is None:
                    st.session_state.df_proveedores = df_web
                else:
                    st.session_state.df_proveedores = pd.concat(
                        [st.session_state.df_proveedores, df_web], ignore_index=True
                    ).drop_duplicates(subset=["nombre"])
                st.success("Proveedores agregados al comparador.")

    with tab_subir:
        st.markdown("### Analizar Documentos de Proveedores")
        st.markdown("<p style='color:#AFA9EC;'>Sube propuestas, RFPs o fichas tecnicas en PDF.</p>", unsafe_allow_html=True)
        docs = st.file_uploader("Sube documentos PDF de proveedores", type=["pdf"],
                                accept_multiple_files=True, key="docs_prov")
        if docs:
            st.info(f"{len(docs)} documento(s) cargado(s).")

        if docs and st.button("Analizar Documentos", type="primary", use_container_width=True):
            resultados_prov = []
            pb2  = st.progress(0)
            stx2 = st.empty()
            cert_lista = [c.strip() for c in cert_requeridas.split("\n") if c.strip()]

            for idx, doc in enumerate(docs):
                stx2.markdown(f"Analizando **{idx+1}/{len(docs)}**: {doc.name}")
                try:
                    reader = PdfReader(doc)
                    texto  = "".join(p.extract_text() or "" for p in reader.pages)
                except Exception as e:
                    st.error(f"Error leyendo {doc.name}: {e}"); continue

                prompt_doc = (
                    f"Eres un experto en procurement. Analiza este documento de proveedor.\n"
                    f"Responde EXCLUSIVAMENTE con JSON valido, sin texto adicional ni markdown.\n\n"
                    f"Contexto: pais={pais_busqueda or 'no especificado'}, "
                    f"presupuesto={presupuesto_ref}, cobertura={cobertura_req}\n"
                    f"Certificaciones requeridas: {', '.join(cert_lista) or 'ninguna'}\n"
                    f"Pesos: Precio {ppeso_precio}%, Certificaciones {ppeso_cert}%, "
                    f"Reputacion {ppeso_rep}%, Cobertura {ppeso_cob}%\n\n"
                    f"Formato JSON requerido:\n"
                    f'{{"nombre":"","descripcion":"","sitio_web":"","pais_sede":"","cobertura":"",'
                    f'"anos_experiencia":"","certificaciones":"","productos_servicios":"",'
                    f'"rango_precio":"","condiciones_comerciales":"","tiempo_entrega":"",'
                    f'"clientes_referencia":"","fortalezas":"","debilidades":"",'
                    f'"puntaje_precio":0,"puntaje_certificaciones":0,"puntaje_reputacion":0,"puntaje_cobertura":0,'
                    f'"puntaje_recomendacion":0,"nivel_recomendacion":"","justificacion":"",'
                    f'"cumple_certificaciones":false,"certificaciones_faltantes":""}}\n\n'
                    f"- Puntajes del 1 al 10\n"
                    f"- puntaje_recomendacion: promedio ponderado segun pesos\n"
                    f'- nivel_recomendacion: "Muy recomendado" >= 8, "Recomendado" >= 6, "Opcion viable" >= 4, "No recomendado" < 4\n'
                    f"- Si un dato no esta en el documento: No especifica\n\n"
                    f"Documento:\n{texto[:4000]}"
                )

                try:
                    msg   = client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=1500,
                                messages=[{"role": "user", "content": prompt_doc}])
                    datos = limpiar_json(msg.content[0].text)
                    datos["Archivo"] = doc.name
                    datos["Fuente"]  = "Documento"
                    resultados_prov.append(datos)
                except Exception as e:
                    st.error(f"Error procesando {doc.name}: {e}")
                pb2.progress((idx + 1) / len(docs))

            if resultados_prov:
                df_new = pd.DataFrame(resultados_prov)
                if st.session_state.df_proveedores is None:
                    st.session_state.df_proveedores = df_new
                else:
                    st.session_state.df_proveedores = pd.concat(
                        [st.session_state.df_proveedores, df_new], ignore_index=True)
                stx2.success(f"{len(resultados_prov)} documentos analizados y agregados al comparador.")

    with tab_comparar:
        st.markdown("### Comparaci\u00f3n de Proveedores")
        if st.session_state.df_proveedores is None or len(st.session_state.df_proveedores) == 0:
            st.info("Primero busca proveedores en internet o analiza documentos.")
        else:
            df_p = st.session_state.df_proveedores.copy()
            if "nombre" not in df_p.columns and "nombre_empresa" in df_p.columns:
                df_p["nombre"] = df_p["nombre_empresa"]
            for col in ["puntaje_recomendacion","puntaje_precio","puntaje_certificaciones","puntaje_reputacion","puntaje_cobertura"]:
                if col in df_p.columns:
                    df_p[col] = pd.to_numeric(df_p[col], errors="coerce").fillna(0)

            todos_nombres = df_p["nombre"].dropna().tolist()
            seleccionados = st.multiselect("Selecciona proveedores a comparar",
                todos_nombres, default=todos_nombres[:min(5, len(todos_nombres))])

            if seleccionados:
                df_sel = df_p[df_p["nombre"].isin(seleccionados)].copy()
                if "puntaje_recomendacion" in df_sel.columns:
                    df_sel = df_sel.sort_values("puntaje_recomendacion", ascending=False).reset_index(drop=True)
                    df_sel["Ranking"] = df_sel.index + 1

                st.markdown("#### Ranking General")
                for _, row in df_sel.iterrows():
                    puntaje = row.get("puntaje_recomendacion", 0)
                    nivel   = row.get("nivel_recomendacion", "Recomendado")
                    badge_c = "badge-prov-a" if puntaje >= 8 else "badge-prov-b" if puntaje >= 6 else "badge-prov-c"
                    desc    = str(row.get("descripcion", row.get("productos_servicios", "")))[:120]
                    just    = row.get("justificacion", row.get("razon_recomendacion", ""))
                    p_precio = row.get("puntaje_precio", "-")
                    p_cert   = row.get("puntaje_certificaciones", "-")
                    p_rep    = row.get("puntaje_reputacion", "-")
                    p_cob    = row.get("puntaje_cobertura", "-")
                    st.markdown(f"""
                    <div class="proveedor-card">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                          <strong style="color:#f0eeff;font-size:15px;">#{row.get('Ranking','?')} {row.get('nombre','N/A')}</strong>
                          &nbsp;<span class="{badge_c}">{nivel}</span>
                          <div style="color:#AFA9EC;font-size:12px;margin-top:4px;">{desc}</div>
                        </div>
                        <span style="font-size:24px;font-weight:700;color:#34d399;">{puntaje}/10</span>
                      </div>
                      <div style="margin-top:10px;display:grid;grid-template-columns:repeat(4,1fr);gap:8px;text-align:center;">
                        <div style="background:#12111a;border-radius:8px;padding:8px;">
                          <div style="color:#fbbf24;font-size:16px;font-weight:700;">{p_precio}</div>
                          <div style="color:#AFA9EC;font-size:11px;">Precio</div>
                        </div>
                        <div style="background:#12111a;border-radius:8px;padding:8px;">
                          <div style="color:#60a5fa;font-size:16px;font-weight:700;">{p_cert}</div>
                          <div style="color:#AFA9EC;font-size:11px;">Certif.</div>
                        </div>
                        <div style="background:#12111a;border-radius:8px;padding:8px;">
                          <div style="color:#f472b6;font-size:16px;font-weight:700;">{p_rep}</div>
                          <div style="color:#AFA9EC;font-size:11px;">Reput.</div>
                        </div>
                        <div style="background:#12111a;border-radius:8px;padding:8px;">
                          <div style="color:#34d399;font-size:16px;font-weight:700;">{p_cob}</div>
                          <div style="color:#AFA9EC;font-size:11px;">Cobert.</div>
                        </div>
                      </div>
                      <div style="margin-top:8px;font-size:12px;color:#9890cc;font-style:italic;">{just}</div>
                    </div>""", unsafe_allow_html=True)

                criterios_all = ["puntaje_precio","puntaje_certificaciones","puntaje_reputacion","puntaje_cobertura"]
                criterios_ok  = [c for c in criterios_all if c in df_sel.columns and df_sel[c].sum() > 0]
                if len(df_sel) > 1 and criterios_ok:
                    st.markdown("#### Radar de Comparacion")
                    labels  = {"puntaje_precio":"Precio","puntaje_certificaciones":"Certif.",
                               "puntaje_reputacion":"Reput.","puntaje_cobertura":"Cobert."}
                    cats    = [labels.get(c, c) for c in criterios_ok]
                    colores = ["#7F77DD","#34d399","#fbbf24","#f87171","#60a5fa"]
                    fig_r   = go.Figure()
                    for i, (_, row) in enumerate(df_sel.iterrows()):
                        vals = [float(row.get(c, 0)) for c in criterios_ok]
                        fig_r.add_trace(go.Scatterpolar(
                            r=vals + [vals[0]], theta=cats + [cats[0]],
                            fill='toself', name=str(row.get("nombre", "Proveedor")),
                            line_color=colores[i % len(colores)],
                            fillcolor=colores[i % len(colores)], opacity=0.3
                        ))
                    fig_r.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0,10], color="#AFA9EC"),
                                   bgcolor="#1e1b2e", angularaxis=dict(color="#AFA9EC")),
                        paper_bgcolor="rgba(0,0,0,0)", font_color="#f0eeff",
                        legend=dict(bgcolor="#1e1b2e", bordercolor="#534AB7", borderwidth=1), height=450
                    )
                    st.plotly_chart(fig_r, use_container_width=True)

                st.markdown("#### Tabla Comparativa Detallada")
                cols_tabla = ["nombre","cobertura","anos_experiencia","certificaciones",
                              "rango_precio","contacto","sitio_web","fortalezas",
                              "puntaje_recomendacion","nivel_recomendacion"]
                cols_ok = [c for c in cols_tabla if c in df_sel.columns]
                rename_map = {
                    "nombre": "Nombre",
                    "cobertura": "Cobertura",
                    "anos_experiencia": "A\u00f1os de Experiencia",
                    "certificaciones": "Certificaciones",
                    "rango_precio": "Rango de Precio",
                    "contacto": "Contacto",
                    "sitio_web": "Sitio Web",
                    "fortalezas": "Fortalezas",
                    "puntaje_recomendacion": "Puntaje",
                    "nivel_recomendacion": "Nivel de Recomendaci\u00f3n",
                }
                df_tabla = df_sel[cols_ok].rename(columns=rename_map)
                st.dataframe(df_tabla, use_container_width=True, height=300)

            if st.button("Limpiar comparador", use_container_width=True):
                st.session_state.df_proveedores  = None
                st.session_state.proveedores_web = []
                st.rerun()

    with tab_dash:
        st.markdown("### Dashboards de Proveedores")
        if st.session_state.df_proveedores is None or len(st.session_state.df_proveedores) == 0:
            st.info("Agrega proveedores desde las pestanas anteriores para ver los dashboards.")
        else:
            df_p = st.session_state.df_proveedores.copy()
            if "nombre" not in df_p.columns and "nombre_empresa" in df_p.columns:
                df_p["nombre"] = df_p["nombre_empresa"]
            for col in ["puntaje_recomendacion","puntaje_precio","puntaje_certificaciones","puntaje_reputacion","puntaje_cobertura"]:
                if col in df_p.columns:
                    df_p[col] = pd.to_numeric(df_p[col], errors="coerce").fillna(0)

            col1, col2 = st.columns(2)
            with col1:
                if "cobertura" in df_p.columns:
                    cob = df_p["cobertura"].value_counts().reset_index(); cob.columns = ["Cobertura","Cantidad"]
                    fig_c = px.pie(cob, values="Cantidad", names="Cobertura",
                                   title="Distribucion por Cobertura", hole=0.4, color_discrete_sequence=VERDE)
                    fig_c.update_layout(**LAYOUT); st.plotly_chart(fig_c, use_container_width=True)
            with col2:
                if "nivel_recomendacion" in df_p.columns:
                    niv = df_p["nivel_recomendacion"].value_counts().reset_index(); niv.columns = ["Nivel","Cantidad"]
                    fig_n = px.bar(niv, x="Nivel", y="Cantidad", title="Proveedores por Nivel",
                                   color="Cantidad", color_continuous_scale=VERDE)
                    fig_n.update_layout(**LAYOUT); st.plotly_chart(fig_n, use_container_width=True)

            if "puntaje_recomendacion" in df_p.columns and "nombre" in df_p.columns:
                df_rank = df_p[["nombre","puntaje_recomendacion"]].copy()
                df_rank = df_rank.sort_values("puntaje_recomendacion", ascending=True).tail(10)
                fig_rank = px.bar(df_rank, x="puntaje_recomendacion", y="nombre", orientation="h",
                                  title="Top Proveedores por Puntaje",
                                  color="puntaje_recomendacion", color_continuous_scale=VERDE)
                fig_rank.update_layout(**LAYOUT); st.plotly_chart(fig_rank, use_container_width=True)

            k1, k2, k3 = st.columns(3)
            with k1: st.metric("Total Proveedores", len(df_p))
            with k2:
                if "puntaje_recomendacion" in df_p.columns:
                    st.metric("Puntaje Promedio", f"{df_p['puntaje_recomendacion'].mean():.1f}/10")
            with k3:
                if "nivel_recomendacion" in df_p.columns:
                    top = len(df_p[df_p["nivel_recomendacion"].str.contains("Muy", na=False)])
                    st.metric("Muy Recomendados", top)

    with tab_export:
        st.markdown("### Exportar An\u00e1lisis de Proveedores")
        if st.session_state.df_proveedores is None or len(st.session_state.df_proveedores) == 0:
            st.info("No hay proveedores para exportar aun.")
        else:
            df_p = st.session_state.df_proveedores.copy()
            if "nombre" not in df_p.columns and "nombre_empresa" in df_p.columns:
                df_p["nombre"] = df_p["nombre_empresa"]
            if "puntaje_recomendacion" in df_p.columns:
                df_p["puntaje_recomendacion"] = pd.to_numeric(df_p["puntaje_recomendacion"], errors="coerce").fillna(0)

            op_p = st.radio("Que exportar?", ["Todos los proveedores","Solo Muy Recomendados","Solo Recomendados","Top 5"])
            df_exp_p = df_p.copy()
            if "nivel_recomendacion" in df_p.columns:
                if op_p == "Solo Muy Recomendados":
                    df_exp_p = df_p[df_p["nivel_recomendacion"].str.contains("Muy", na=False)]
                elif op_p == "Solo Recomendados":
                    df_exp_p = df_p[df_p["nivel_recomendacion"].isin(["Muy recomendado","Recomendado","Muy Recomendado"])]
            if op_p == "Top 5":
                if "puntaje_recomendacion" in df_p.columns:
                    df_exp_p = df_p.sort_values("puntaje_recomendacion", ascending=False).head(5)
                else:
                    df_exp_p = df_p.head(5)

            st.info(f"Se exportaran **{len(df_exp_p)} proveedores**")
            st.download_button("Descargar Excel de Proveedores", data=exportar_excel_proveedores(df_exp_p),
                file_name="RecrutAI_Proveedores.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
