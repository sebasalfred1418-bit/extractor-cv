import streamlit as st
import anthropic
import pandas as pd
from pypdf import PdfReader
import io
import json
import plotly.express as px
from collections import Counter
import streamlit_authenticator as stauth

st.set_page_config(page_title="RecrutAI", page_icon="🟣", layout="wide")

# ── AUTENTICACIÓN ─────────────────────────────────────────────────────────────
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
    credentials,
    "recrutai_cookie",
    "recrutai_secret_key_2024",
    cookie_expiry_days=30
)

# ── CSS GLOBAL (púrpura RecrutAI - alta visibilidad) ──────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Fondo principal: gris muy oscuro (no morado) para que el contenido respire */
  .main { background-color: #12111a; }

  /* ── Textos globales: blanco puro para máxima legibilidad ── */
  label, .stTextInput label, .stSelectbox label, .stTextArea label,
  .stSlider label, .stFileUploader label, .stRadio label,
  .stMultiSelect label, p, span, div {
    color: #f0eeff !important;
  }

  /* Inputs: fondo blanco roto con texto oscuro — se ven claramente */
  .stTextInput input, .stTextArea textarea {
    background: #f5f3ff !important;
    color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important;
    border-radius: 8px !important;
    font-size: 14px !important;
  }
  .stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: #9490b8 !important;
  }
  .stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #AFA9EC !important;
    box-shadow: 0 0 0 2px rgba(127,119,221,0.25) !important;
  }

  /* Selectbox: fondo claro, texto oscuro */
  .stSelectbox > div > div {
    background: #f5f3ff !important;
    color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important;
    border-radius: 8px !important;
  }
  .stSelectbox svg { fill: #534AB7 !important; }

  /* Multiselect */
  .stMultiSelect > div > div {
    background: #f5f3ff !important;
    border: 1.5px solid #7F77DD !important;
    border-radius: 8px !important;
    color: #1a1035 !important;
  }

  /* Radio buttons: texto blanco visible */
  .stRadio > div { gap: 8px; }
  .stRadio label { color: #f0eeff !important; font-size: 14px !important; }

  /* Sliders: track en púrpura, label visible */
  .stSlider > div > div > div { background: #534AB7 !important; }
  .stSlider .st-emotion-cache-1dp5vir { color: #f0eeff !important; }

  /* File uploader */
  [data-testid="stFileUploader"] {
    background: #1e1b2e !important;
    border: 2px dashed #7F77DD !important;
    border-radius: 12px !important;
  }

  /* ── Sidebar: fondo oscuro con buena separación ── */
  [data-testid="stSidebar"] {
    background: #1a1730 !important;
    border-right: 2px solid #534AB7;
  }
  [data-testid="stSidebar"] label {
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 13px !important;
  }
  [data-testid="stSidebar"] .stTextInput input,
  [data-testid="stSidebar"] .stTextArea textarea {
    background: #f5f3ff !important;
    color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important;
  }
  [data-testid="stSidebar"] .stSelectbox > div > div {
    background: #f5f3ff !important;
    color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important;
  }
  /* Valores actuales de slider visibles */
  [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
  [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"],
  [data-testid="stSidebar"] p { color: #e0dbff !important; }

  /* ── Botones ── */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #534AB7, #7F77DD) !important;
    border: none !important; border-radius: 10px !important;
    color: white !important; font-weight: 600 !important;
    font-size: 15px !important; letter-spacing: 0.5px !important;
    padding: 0.6rem 1.2rem !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #6b61cc, #9890e8) !important;
    transform: translateY(-1px);
  }
  .stButton > button {
    border-radius: 8px !important;
    border: 1.5px solid #534AB7 !important;
    color: #e0dbff !important;
    background: transparent !important;
  }
  .stButton > button:hover { background: #26215C !important; }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    background: #1e1b2e; border-radius: 10px; padding: 4px;
    border: 1px solid #3C3489;
  }
  .stTabs [data-baseweb="tab"] { color: #AFA9EC; border-radius: 8px; font-weight: 500; }
  .stTabs [aria-selected="true"] { background: #534AB7 !important; color: white !important; }

  /* ── Login form ── */
  .stForm {
    background: #1e1b2e !important;
    border: 1.5px solid #534AB7 !important;
    border-radius: 16px !important; padding: 2rem !important;
  }
  .stForm label { color: #ffffff !important; font-weight: 500 !important; }
  .stForm input {
    background: #f5f3ff !important;
    color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important;
    border-radius: 8px !important;
  }

  /* ── Progress bar ── */
  .stProgress > div > div { background: linear-gradient(90deg, #534AB7, #AFA9EC); }

  /* ── Metric cards ── */
  .metric-card {
    background: #1e1b2e;
    border: 1.5px solid #534AB7;
    padding: 20px; border-radius: 14px;
    text-align: center; color: white;
  }
  .metric-card h2 { font-size: 2rem; margin: 0; font-weight: 700; color: white !important; }
  .metric-card p  { margin: 4px 0 0; font-size: 13px; color: #AFA9EC !important; }

  /* ── Candidate cards ── */
  .candidate-card {
    background: #1e1b2e;
    border: 1.5px solid #3C3489;
    border-radius: 12px; padding: 16px; margin: 8px 0;
  }
  .badge-alto  { background:#1a4731; color:#4ade80; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-medio { background:#4a3800; color:#fbbf24; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }
  .badge-bajo  { background:#4a1c1c; color:#f87171; padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600; }

  /* ── Dataframe ── */
  [data-testid="stDataFrame"] { border: 1px solid #534AB7 !important; border-radius: 8px; }

  /* ── Dividers & headings ── */
  hr { border-color: #534AB7 !important; }
  h1, h2, h3 { color: #f0eeff !important; }

  /* ── Logo header ── */
  .logo-header { display: flex; align-items: center; gap: 14px; padding: 0 0 1rem 0; }
  .logo-icon {
    width: 48px; height: 48px; border-radius: 12px;
    background: linear-gradient(135deg, #534AB7, #7F77DD);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 800; color: white;
  }

  /* ── Mensajes de éxito / error / info ── */
  .stSuccess { background: #0f2e1a !important; color: #4ade80 !important; border: 1px solid #1a6b3c !important; }
  .stError   { background: #2e0f0f !important; color: #f87171 !important; border: 1px solid #6b1a1a !important; }
  .stInfo    { background: #1a1b2e !important; color: #AFA9EC !important; border: 1px solid #534AB7 !important; }
</style>
""", unsafe_allow_html=True)

# ── PANTALLA DE LOGIN ─────────────────────────────────────────────────────────
def mostrar_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding: 2rem 0 1.5rem;">
          <div style="width:64px;height:64px;border-radius:16px;
               background:linear-gradient(135deg,#534AB7,#7F77DD);
               display:inline-flex;align-items:center;justify-content:center;
               font-size:28px;font-weight:800;color:white;margin-bottom:16px;">RA</div>
          <h2 style="color:#e2e8f0;margin:0;font-size:1.8rem;font-weight:700;">RecrutAI</h2>
          <p style="color:#AFA9EC;margin:4px 0 0;font-size:14px;letter-spacing:2px;">POWERED BY CLAUDE AI</p>
        </div>
        """, unsafe_allow_html=True)

name, authentication_status, username = authenticator.login(
    fields={"Form name": "Iniciar sesión", "Username": "Usuario", "Password": "Contraseña", "Login": "Entrar"}
)

if authentication_status == False:
    mostrar_login()
    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

if authentication_status is None:
    mostrar_login()
    st.info("👆 Ingresa tus credenciales para acceder")
    st.stop()

# ── APP PRINCIPAL (solo si autenticado) ───────────────────────────────────────
try:
    api_key_segura = st.secrets["CLAUDE_API_KEY"]
except Exception:
    st.error("⚠️ No se encontró la API Key en los Secrets de Streamlit Cloud.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key_segura)

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
          <div style="color:#e2e8f0;font-weight:600;font-size:15px;">RecrutAI</div>
          <div style="color:#7F77DD;font-size:11px;letter-spacing:1px;">POWERED BY CLAUDE AI</div>
        </div>
      </div>
      <div style="color:#AFA9EC;font-size:12px;margin-top:8px;">
        👤 {name} &nbsp;|&nbsp; <span style="color:#7F77DD;">{username}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("## ⚙️ Configurar Puesto")

    puesto = st.text_input("🏢 Nombre del puesto", placeholder="Ej: Analista de Datos")
    experiencia_min = st.slider("📅 Años mínimos de experiencia", 0, 20, 2)
    educacion_req = st.selectbox("🎓 Educación mínima", [
        "Cualquiera", "Técnico", "Bachiller", "Licenciatura", "Maestría", "Doctorado"
    ])
    habilidades_req = st.text_area(
        "🛠️ Habilidades requeridas (una por línea)",
        placeholder="Python\nExcel\nSQL\nPower BI"
    )
    idioma_req = st.selectbox("🌐 Idioma requerido", [
        "No requerido", "Inglés", "Inglés avanzado", "Portugués", "Francés"
    ])

    st.divider()
    st.markdown("**Pesos de puntuación**")
    peso_exp = st.slider("Experiencia", 0, 100, 35)
    peso_edu = st.slider("Educación",   0, 100, 25)
    peso_hab = st.slider("Habilidades", 0, 100, 30)
    peso_idi = st.slider("Idiomas",     0, 100, 10)

    st.divider()
    authenticator.logout("🚪 Cerrar sesión", "sidebar")

# ── HEADER PRINCIPAL ──────────────────────────────────────────────────────────
st.markdown("""
<div class="logo-header">
  <div class="logo-icon">RA</div>
  <div>
    <h1 style="margin:0;font-size:1.9rem;font-weight:700;color:#e2e8f0;">RecrutAI</h1>
    <p style="margin:0;color:#AFA9EC;font-size:13px;letter-spacing:2px;">PLATAFORMA INTELIGENTE DE RECLUTAMIENTO</p>
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "df_candidatos" not in st.session_state:
    st.session_state.df_candidatos = None

# ── CARGA DE ARCHIVOS ─────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "📂 Sube los CVs en PDF",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📋 **{len(uploaded_files)}** archivo(s) cargado(s) y listo(s) para procesar.")

if uploaded_files and st.button("🚀 Procesar y Clasificar Candidatos", type="primary", use_container_width=True):
    resultados = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    habilidades_lista = [h.strip().lower() for h in habilidades_req.split("\n") if h.strip()]

    for index, file in enumerate(uploaded_files):
        status_text.markdown(f"⏳ Analizando **{index+1}/{len(uploaded_files)}**: {file.name}")
        try:
            pdf_reader = PdfReader(file)
            texto_cv = "".join(page.extract_text() or "" for page in pdf_reader.pages)
        except Exception as e:
            st.error(f"Error leyendo {file.name}: {e}")
            continue

        prompt = f"""Eres un reclutador experto. Analiza este CV para el puesto de "{puesto or 'No especificado'}".
Responde EXCLUSIVAMENTE con un objeto JSON válido, sin texto adicional ni markdown.

Formato JSON requerido:
{{
  "Nombre": "",
  "Correo": "",
  "Telefono": "",
  "Educacion_Maxima": "",
  "Universidad": "",
  "Carrera": "",
  "Ultimo_Cargo": "",
  "Ultima_Empresa": "",
  "Experiencia_Anos": 0,
  "Habilidades_Tecnicas": "",
  "Habilidades_Blandas": "",
  "Idiomas": "",
  "Certificaciones": "",
  "Puntaje": 0,
  "Nivel_Potencial": "",
  "Justificacion": "",
  "Cumple_Requisitos": false,
  "Requisitos_Cumplidos": "",
  "Requisitos_Faltantes": ""
}}

Instrucciones de puntuación (puntaje del 1 al 10):
- Evalúa experiencia relevante para "{puesto or 'el puesto'}" (peso {peso_exp}%)
- Evalúa nivel educativo (peso {peso_edu}%)
- Evalúa habilidades técnicas requeridas: {', '.join(habilidades_lista) or 'no especificadas'} (peso {peso_hab}%)
- Evalúa idiomas: {idioma_req} (peso {peso_idi}%)
- Nivel_Potencial: "Alto" si puntaje >= 7, "Medio" si >= 4, "Bajo" si < 4
- Cumple_Requisitos: true si experiencia >= {experiencia_min} años y puntaje >= 6
- Justificacion: 1-2 oraciones explicando el puntaje
- Requisitos_Cumplidos y Requisitos_Faltantes: lista separada por comas
- Experiencia_Anos: solo número entero
- Habilidades_Tecnicas: máximo 6, separadas por coma
- Habilidades_Blandas: máximo 4, separadas por coma
- Si un dato no existe: "No especifica"

CV a analizar:
{texto_cv[:4000]}"""

        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}]
            )
            respuesta_texto = message.content[0].text.strip()
            if "```" in respuesta_texto:
                respuesta_texto = respuesta_texto.split("```")[1]
                if respuesta_texto.startswith("json"):
                    respuesta_texto = respuesta_texto[4:]
            inicio = respuesta_texto.find("{")
            fin = respuesta_texto.rfind("}") + 1
            datos = json.loads(respuesta_texto[inicio:fin])
            datos["Archivo"] = file.name
            resultados.append(datos)
        except Exception as e:
            st.error(f"Error procesando {file.name}: {e}")

        progress_bar.progress((index + 1) / len(uploaded_files))

    if resultados:
        df = pd.DataFrame(resultados)
        df["Experiencia_Anos"] = pd.to_numeric(df["Experiencia_Anos"], errors="coerce").fillna(0).astype(int)
        df["Puntaje"] = pd.to_numeric(df["Puntaje"], errors="coerce").fillna(0)
        df = df.sort_values("Puntaje", ascending=False).reset_index(drop=True)
        df["Ranking"] = df.index + 1
        st.session_state.df_candidatos = df
        status_text.success(f"✅ {len(resultados)} CVs procesados y clasificados correctamente.")

# ── RESULTADOS ────────────────────────────────────────────────────────────────
if st.session_state.df_candidatos is not None:
    df = st.session_state.df_candidatos.copy()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 Ranking & Clasificación",
        "📊 Dashboards & Métricas",
        "🔍 Filtros & Búsqueda",
        "📥 Exportar"
    ])

    # ── TAB 1: RANKING ────────────────────────────────────────────────────────
    with tab1:
        st.markdown("## 🏆 Ranking de Candidatos")
        c1, c2, c3, c4 = st.columns(4)
        total   = len(df)
        altos   = len(df[df["Nivel_Potencial"] == "Alto"])
        medios  = len(df[df["Nivel_Potencial"] == "Medio"])
        cumplen = len(df[df["Cumple_Requisitos"] == True])

        with c1:
            st.markdown(f'<div class="metric-card"><h2>{total}</h2><p>Total CVs</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><h2 style="color:#4ade80">{altos}</h2><p>Alto Potencial</p></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><h2 style="color:#fbbf24">{medios}</h2><p>Potencial Medio</p></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-card"><h2 style="color:#AFA9EC">{cumplen}</h2><p>Cumplen Requisitos</p></div>', unsafe_allow_html=True)

        st.markdown("### 🥇 Top Candidatos")
        for _, row in df.head(20).iterrows():
            nivel = row.get("Nivel_Potencial", "Bajo")
            badge = "badge-alto" if nivel == "Alto" else "badge-medio" if nivel == "Medio" else "badge-bajo"
            puntaje = row.get("Puntaje", 0)
            cumple  = "✅ Cumple requisitos" if row.get("Cumple_Requisitos") else "❌ No cumple"
            st.markdown(f"""
            <div class="candidate-card">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <strong style="font-size:16px;color:#e2e8f0;">#{row['Ranking']} {row.get('Nombre','N/A')}</strong>
                  &nbsp;<span class="{badge}">{nivel}</span>
                  &nbsp;<small style="color:#7F77DD;">{cumple}</small>
                </div>
                <div style="text-align:right;">
                  <span style="font-size:26px;font-weight:700;color:#7F77DD;">{puntaje}/10</span>
                </div>
              </div>
              <div style="margin-top:8px;color:#AFA9EC;font-size:13px;">
                🏢 {row.get('Ultimo_Cargo','N/A')} en {row.get('Ultima_Empresa','N/A')}
                &nbsp;|&nbsp; 📅 {row.get('Experiencia_Anos',0)} años
                &nbsp;|&nbsp; 🎓 {row.get('Educacion_Maxima','N/A')}
              </div>
              <div style="margin-top:6px;color:#8b83d0;font-size:12px;font-style:italic;">
                💬 {row.get('Justificacion','Sin justificación')}
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2: DASHBOARDS ─────────────────────────────────────────────────────
    with tab2:
        st.markdown("## 📊 Dashboards & Métricas")

        PURPLE = ["#26215C","#3C3489","#534AB7","#7F77DD","#AFA9EC","#CECBF6"]

        col_a, col_b = st.columns(2)
        with col_a:
            conteo = df["Nivel_Potencial"].value_counts().reset_index()
            conteo.columns = ["Nivel","Cantidad"]
            fig1 = px.pie(conteo, values="Cantidad", names="Nivel",
                         title="Distribución por Nivel de Potencial",
                         color="Nivel",
                         color_discrete_map={"Alto":"#4ade80","Medio":"#fbbf24","Bajo":"#f87171"},
                         hole=0.45)
            fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
            st.plotly_chart(fig1, use_container_width=True)

        with col_b:
            conteo_edu = df["Educacion_Maxima"].value_counts().reset_index()
            conteo_edu.columns = ["Educacion","Cantidad"]
            fig2 = px.bar(conteo_edu, x="Cantidad", y="Educacion", orientation="h",
                         title="Distribución por Nivel Educativo",
                         color="Cantidad", color_continuous_scale=PURPLE)
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
            st.plotly_chart(fig2, use_container_width=True)

        col_c, col_d = st.columns(2)
        with col_c:
            todas_hab = []
            for h in df["Habilidades_Tecnicas"].dropna():
                todas_hab.extend([x.strip() for x in str(h).split(",") if x.strip() and x.strip() != "No especifica"])
            if todas_hab:
                df_hab = pd.DataFrame(Counter(todas_hab).most_common(12), columns=["Habilidad","Frecuencia"])
                fig3 = px.bar(df_hab, x="Frecuencia", y="Habilidad", orientation="h",
                             title="Habilidades Técnicas más Frecuentes",
                             color="Frecuencia", color_continuous_scale=PURPLE)
                fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                st.plotly_chart(fig3, use_container_width=True)

        with col_d:
            todos_idi = []
            for i in df["Idiomas"].dropna():
                todos_idi.extend([x.strip() for x in str(i).split(",") if x.strip() and x.strip() != "No especifica"])
            if todos_idi:
                df_idi = pd.DataFrame(Counter(todos_idi).most_common(8), columns=["Idioma","Frecuencia"])
                fig4 = px.pie(df_idi, values="Frecuencia", names="Idioma",
                             title="Distribución por Idiomas",
                             color_discrete_sequence=PURPLE)
                fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
                st.plotly_chart(fig4, use_container_width=True)

        col_e, col_f = st.columns(2)
        with col_e:
            fig5 = px.histogram(df, x="Experiencia_Anos", nbins=15,
                               title="Distribución de Años de Experiencia",
                               color_discrete_sequence=["#534AB7"])
            fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
            st.plotly_chart(fig5, use_container_width=True)

        with col_f:
            fig6 = px.scatter(df, x="Experiencia_Anos", y="Puntaje",
                             color="Nivel_Potencial",
                             hover_data=["Nombre","Ultimo_Cargo"],
                             title="Experiencia vs Puntaje",
                             color_discrete_map={"Alto":"#4ade80","Medio":"#fbbf24","Bajo":"#f87171"})
            fig6.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
            st.plotly_chart(fig6, use_container_width=True)

        st.markdown("### 📈 Indicadores Clave")
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Experiencia Promedio", f"{df['Experiencia_Anos'].mean():.1f} años")
        with k2:
            st.metric("Puntaje Promedio", f"{df['Puntaje'].mean():.1f}/10")
        with k3:
            pct = (len(df[df["Cumple_Requisitos"] == True]) / len(df)) * 100
            st.metric("% Cumple Requisitos", f"{pct:.0f}%")
        with k4:
            pct2 = (len(df[df["Nivel_Potencial"] == "Alto"]) / len(df)) * 100
            st.metric("% Alto Potencial", f"{pct2:.0f}%")

    # ── TAB 3: FILTROS ────────────────────────────────────────────────────────
    with tab3:
        st.markdown("## 🔍 Filtros en Tiempo Real")
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            filtro_potencial = st.multiselect("Nivel de Potencial",
                ["Alto","Medio","Bajo"], default=["Alto","Medio","Bajo"])
        with f2:
            filtro_exp = st.slider("Experiencia mínima (años)", 0, 20, 0)
        with f3:
            filtro_puntaje = st.slider("Puntaje mínimo", 0.0, 10.0, 0.0, 0.5)
        with f4:
            filtro_cumple = st.selectbox("Cumple requisitos",
                ["Todos","Solo los que cumplen","Solo los que no cumplen"])

        filtro_nombre = st.text_input("🔎 Buscar por nombre, cargo o habilidad")

        df_f = df.copy()
        df_f = df_f[df_f["Nivel_Potencial"].isin(filtro_potencial)]
        df_f = df_f[df_f["Experiencia_Anos"] >= filtro_exp]
        df_f = df_f[df_f["Puntaje"] >= filtro_puntaje]
        if filtro_cumple == "Solo los que cumplen":
            df_f = df_f[df_f["Cumple_Requisitos"] == True]
        elif filtro_cumple == "Solo los que no cumplen":
            df_f = df_f[df_f["Cumple_Requisitos"] == False]
        if filtro_nombre:
            mask = (
                df_f["Nombre"].str.contains(filtro_nombre, case=False, na=False) |
                df_f["Ultimo_Cargo"].str.contains(filtro_nombre, case=False, na=False) |
                df_f["Habilidades_Tecnicas"].str.contains(filtro_nombre, case=False, na=False)
            )
            df_f = df_f[mask]

        st.markdown(f"**{len(df_f)} candidatos encontrados**")
        cols = ["Ranking","Nombre","Puntaje","Nivel_Potencial","Ultimo_Cargo",
                "Experiencia_Anos","Educacion_Maxima","Habilidades_Tecnicas",
                "Idiomas","Correo","Cumple_Requisitos"]
        st.dataframe(df_f[[c for c in cols if c in df_f.columns]],
                     use_container_width=True, height=500)

    # ── TAB 4: EXPORTAR ───────────────────────────────────────────────────────
    with tab4:
        st.markdown("## 📥 Exportar Resultados")
        opcion = st.radio("¿Qué candidatos exportar?", [
            "Todos los candidatos",
            "Solo Alto Potencial",
            "Solo los que cumplen requisitos",
            "Top 10 candidatos"
        ])
        df_exp = df.copy()
        if opcion == "Solo Alto Potencial":
            df_exp = df[df["Nivel_Potencial"] == "Alto"]
        elif opcion == "Solo los que cumplen requisitos":
            df_exp = df[df["Cumple_Requisitos"] == True]
        elif opcion == "Top 10 candidatos":
            df_exp = df.head(10)

        st.info(f"Se exportarán **{len(df_exp)} candidatos**")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_exp.to_excel(writer, index=False, sheet_name='Candidatos')
            ws = writer.sheets['Candidatos']
            from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

            h_fill  = PatternFill(start_color="26215C", end_color="26215C", fill_type="solid")
            alto_f  = PatternFill(start_color="1a4731", end_color="1a4731", fill_type="solid")
            medio_f = PatternFill(start_color="4a3800", end_color="4a3800", fill_type="solid")
            bajo_f  = PatternFill(start_color="4a1c1c", end_color="4a1c1c", fill_type="solid")
            par_f   = PatternFill(start_color="1a1535", end_color="1a1535", fill_type="solid")
            borde   = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'),  bottom=Side(style='thin')
            )

            for col_num, col in enumerate(df_exp.columns, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.font      = Font(bold=True, color="FFFFFF", size=11)
                cell.fill      = h_fill
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border    = borde

            for row_num, (_, row_data) in enumerate(df_exp.iterrows(), 2):
                nivel = row_data.get("Nivel_Potencial","")
                fila_color = (alto_f if nivel=="Alto" else
                              medio_f if nivel=="Medio" else
                              bajo_f  if nivel=="Bajo"  else
                              par_f   if row_num%2==0 else None)
                for col_num in range(1, len(df_exp.columns)+1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                    cell.border    = borde
                    if fila_color:
                        cell.fill = fila_color

            anchos = {
                "Ranking":8,"Nombre":22,"Correo":28,"Telefono":15,
                "Educacion_Maxima":20,"Universidad":22,"Carrera":20,
                "Ultimo_Cargo":25,"Ultima_Empresa":22,"Experiencia_Anos":12,
                "Habilidades_Tecnicas":35,"Habilidades_Blandas":28,
                "Idiomas":15,"Certificaciones":25,"Puntaje":10,
                "Nivel_Potencial":14,"Justificacion":40,
                "Cumple_Requisitos":15,"Requisitos_Cumplidos":30,"Requisitos_Faltantes":30
            }
            for col_num, col in enumerate(df_exp.columns, 1):
                letra = ws.cell(row=1, column=col_num).column_letter
                ws.column_dimensions[letra].width = anchos.get(col, 18)

            ws.row_dimensions[1].height = 30
            for r in range(2, len(df_exp)+2):
                ws.row_dimensions[r].height = 35

        st.download_button(
            label="📥 Descargar Excel Profesional",
            data=output.getvalue(),
            file_name=f"RecrutAI_{puesto or 'candidatos'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
