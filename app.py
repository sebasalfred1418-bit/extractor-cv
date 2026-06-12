import streamlit as st
import anthropic
import pandas as pd
from pypdf import PdfReader
import io
import json
import plotly.express as px
from collections import Counter
import streamlit_authenticator as stauth

st.set_page_config(page_title="RecrutAI Pro", page_icon="🟣", layout="wide")

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
    background-color: #1a1730 !important;
    border-right: 2px solid #534AB7 !important;
  }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] span { color: #ffffff !important; font-weight: 500 !important; }

  input[type="text"], input[type="password"], .stTextInput input, .stTextArea textarea {
    background-color: #ffffff !important; color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important; border-radius: 8px !important; font-size: 14px !important;
  }
  input::placeholder, textarea::placeholder { color: #9490b8 !important; }

  .stSelectbox > div > div, .stSelectbox [data-baseweb="select"] > div {
    background-color: #ffffff !important; color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important; border-radius: 8px !important;
  }
  .stSelectbox [data-baseweb="select"] span,
  .stSelectbox [data-baseweb="select"] div { color: #1a1035 !important; }
  [data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"] {
    background-color: #ffffff !important; color: #1a1035 !important;
  }
  [data-baseweb="option"]:hover { background-color: #ede9ff !important; }

  .stMultiSelect > div > div {
    background-color: #ffffff !important; border: 1.5px solid #7F77DD !important;
    border-radius: 8px !important; color: #1a1035 !important;
  }
  .stTextArea textarea {
    background-color: #ffffff !important; color: #1a1035 !important;
    border: 1.5px solid #7F77DD !important; border-radius: 8px !important;
  }

  /* Nav principal entre módulos */
  .module-nav {
    display: flex; gap: 12px; margin-bottom: 24px;
  }
  .module-btn {
    flex: 1; padding: 16px 20px; border-radius: 12px; text-align: center;
    cursor: pointer; border: 2px solid #3C3489; background: #1e1b2e;
    transition: all 0.2s;
  }
  .module-btn:hover { border-color: #7F77DD; background: #26215C; }
  .module-btn.active { border-color: #7F77DD; background: linear-gradient(135deg,#26215C,#3C3489); }
  .module-btn h3 { margin: 0 0 4px; font-size: 16px; color: #f0eeff !important; }
  .module-btn p  { margin: 0; font-size: 12px; color: #AFA9EC !important; }

  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #534AB7, #7F77DD) !important;
    border: none !important; border-radius: 10px !important;
    color: white !important; font-weight: 600 !important; font-size: 15px !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #6b61cc, #9890e8) !important; transform: translateY(-1px);
  }
  .stButton > button {
    border-radius: 8px !important; border: 1.5px solid #534AB7 !important;
    color: #e0dbff !important; background: transparent !important;
  }
  .stButton > button:hover { background: #26215C !important; }

  [data-testid="stFileUploader"] {
    background: #1e1b2e !important; border: 2px dashed #7F77DD !important; border-radius: 12px !important;
  }
  [data-testid="stFileUploader"] label,
  [data-testid="stFileUploader"] span,
  [data-testid="stFileUploader"] p { color: #f0eeff !important; }

  .stTabs [data-baseweb="tab-list"] {
    background: #1e1b2e !important; border-radius: 10px !important;
    padding: 4px !important; border: 1px solid #3C3489 !important;
  }
  .stTabs [data-baseweb="tab"] { color: #AFA9EC !important; border-radius: 8px !important; font-weight: 500 !important; }
  .stTabs [aria-selected="true"] { background: #534AB7 !important; color: white !important; }

  .stForm { background: #1e1b2e !important; border: 1.5px solid #534AB7 !important; border-radius: 16px !important; padding: 2rem !important; }
  .stForm label { color: #ffffff !important; font-weight: 600 !important; font-size: 14px !important; }
  .stForm input { background: #f5f3ff !important; color: #1a1035 !important; border: 1.5px solid #7F77DD !important; border-radius: 8px !important; }

  .stProgress > div > div { background: linear-gradient(90deg, #534AB7, #AFA9EC) !important; }

  .metric-card {
    background: #1e1b2e; border: 1.5px solid #534AB7;
    padding: 20px; border-radius: 14px; text-align: center;
  }
  .metric-card h2 { font-size: 2rem; margin: 0; font-weight: 700; color: white !important; }
  .metric-card p  { margin: 4px 0 0; font-size: 13px; color: #AFA9EC !important; }

  .candidate-card, .proveedor-card {
    background: #1e1b2e; border: 1.5px solid #3C3489;
    border-radius: 12px; padding: 16px; margin: 8px 0;
  }
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
  .logo-icon {
    width: 48px; height: 48px; border-radius: 12px;
    background: linear-gradient(135deg, #534AB7, #7F77DD);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 800; color: white;
  }

  .search-result-card {
    background: #1a2e20; border: 1.5px solid #0F6E56;
    border-radius: 10px; padding: 14px; margin: 6px 0;
  }
  .source-chip {
    display: inline-block; background: #26215C; color: #AFA9EC;
    padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 6px;
  }
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
    fields={"Form name":"Iniciar sesión","Username":"Usuario","Password":"Contraseña","Login":"Entrar"}
)
if authentication_status == False:
    mostrar_login(); st.error("❌ Usuario o contraseña incorrectos"); st.stop()
if authentication_status is None:
    mostrar_login(); st.info("👆 Ingresa tus credenciales para acceder"); st.stop()

# ── API ───────────────────────────────────────────────────────────────────────
try:
    api_key_segura = st.secrets["CLAUDE_API_KEY"]
except Exception:
    st.error("⚠️ No se encontró la API Key en los Secrets de Streamlit Cloud."); st.stop()
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
        👤 <strong style="color:white;">{name}</strong>
        &nbsp;|&nbsp;<span style="color:#AFA9EC;">{username}</span>
      </div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    modulo = st.radio("📌 Módulo activo", ["📄 Análisis de CVs", "🏢 Análisis de Proveedores"],
                      index=0 if st.session_state.modulo_activo == "cvs" else 1)
    st.session_state.modulo_activo = "cvs" if "CVs" in modulo else "proveedores"

    st.divider()

    if st.session_state.modulo_activo == "cvs":
        st.markdown("<p style='color:#ffffff;font-size:15px;font-weight:700;margin-bottom:12px;'>⚙️ Configurar Puesto</p>", unsafe_allow_html=True)
        puesto         = st.text_input("🏢 Nombre del puesto", placeholder="Ej: Analista de Datos")
        experiencia_min = st.slider("📅 Años mínimos de experiencia", 0, 20, 2)
        educacion_req  = st.selectbox("🎓 Educación mínima", ["Cualquiera","Técnico","Bachiller","Licenciatura","Maestría","Doctorado"])
        habilidades_req = st.text_area("🛠️ Habilidades requeridas (una por línea)", placeholder="Python\nExcel\nSQL")
        idioma_req     = st.selectbox("🌐 Idioma requerido", ["No requerido","Inglés","Inglés avanzado","Portugués","Francés"])
        st.divider()
        st.markdown("<p style='color:#ffffff;font-weight:700;margin-bottom:4px;'>📊 Pesos de puntuación</p>", unsafe_allow_html=True)
        peso_exp = st.slider("Experiencia", 0, 100, 35)
        peso_edu = st.slider("Educación",   0, 100, 25)
        peso_hab = st.slider("Habilidades", 0, 100, 30)
        peso_idi = st.slider("Idiomas",     0, 100, 10)
    else:
        st.markdown("<p style='color:#ffffff;font-size:15px;font-weight:700;margin-bottom:12px;'>⚙️ Configurar Búsqueda</p>", unsafe_allow_html=True)
        pais_busqueda    = st.text_input("🌍 País o región", placeholder="Ej: Perú, LATAM, España")
        rubro_busqueda   = st.text_input("🏭 Rubro o industria", placeholder="Ej: Software, Logística")
        presupuesto_ref  = st.selectbox("💰 Presupuesto referencial", ["No especificado","< $10,000","$10,000 - $50,000","$50,000 - $200,000","> $200,000"])
        cert_requeridas  = st.text_area("📋 Certificaciones requeridas (una por línea)", placeholder="ISO 9001\nSAP Partner\nAWS Certified")
        cobertura_req    = st.selectbox("📍 Cobertura geográfica mínima", ["Local","Nacional","Regional LATAM","Internacional"])
        st.divider()
        st.markdown("<p style='color:#ffffff;font-weight:700;margin-bottom:4px;'>📊 Pesos de evaluación</p>", unsafe_allow_html=True)
        ppeso_precio = st.slider("Precio/Condiciones", 0, 100, 30)
        ppeso_cert   = st.slider("Certificaciones",    0, 100, 25)
        ppeso_rep    = st.slider("Reputación",         0, 100, 25)
        ppeso_cob    = st.slider("Cobertura",          0, 100, 20)

    st.divider()
    authenticator.logout("🚪 Cerrar sesión", "sidebar")

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

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 1: ANÁLISIS DE CVs
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.modulo_activo == "cvs":
    st.markdown("## 📄 Módulo de Análisis de CVs")

    uploaded_files = st.file_uploader("📂 Sube los CVs en PDF", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        st.info(f"📋 **{len(uploaded_files)}** archivo(s) cargado(s).")

    if uploaded_files and st.button("🚀 Procesar y Clasificar Candidatos", type="primary", use_container_width=True):
        resultados = []
        progress_bar = st.progress(0)
        status_text  = st.empty()
        habilidades_lista = [h.strip().lower() for h in habilidades_req.split("\n") if h.strip()]

        for index, file in enumerate(uploaded_files):
            status_text.markdown(f"⏳ Analizando **{index+1}/{len(uploaded_files)}**: {file.name}")
            try:
                pdf_reader = PdfReader(file)
                texto_cv   = "".join(page.extract_text() or "" for page in pdf_reader.pages)
            except Exception as e:
                st.error(f"Error leyendo {file.name}: {e}"); continue

            prompt = f"""Eres un reclutador experto. Analiza este CV para el puesto de "{puesto or 'No especificado'}".
Responde EXCLUSIVAMENTE con un objeto JSON válido, sin texto adicional ni markdown.

Formato JSON:
{{"Nombre":"","Correo":"","Telefono":"","Educacion_Maxima":"","Universidad":"","Carrera":"",
"Ultimo_Cargo":"","Ultima_Empresa":"","Experiencia_Anos":0,"Habilidades_Tecnicas":"",
"Habilidades_Blandas":"","Idiomas":"","Certificaciones":"","Puntaje":0,
"Nivel_Potencial":"","Justificacion":"","Cumple_Requisitos":false,
"Requisitos_Cumplidos":"","Requisitos_Faltantes":""}}

Instrucciones:
- Puntaje 1-10 considerando: experiencia para "{puesto or 'el puesto'}" ({peso_exp}%), educación ({peso_edu}%), habilidades requeridas: {', '.join(habilidades_lista) or 'no especificadas'} ({peso_hab}%), idiomas: {idioma_req} ({peso_idi}%)
- Nivel_Potencial: "Alto" si >= 7, "Medio" si >= 4, "Bajo" si < 4
- Cumple_Requisitos: true si experiencia >= {experiencia_min} años y puntaje >= 6
- Experiencia_Anos: solo número entero
- Habilidades_Tecnicas: máximo 6, separadas por coma
- Habilidades_Blandas: máximo 4, separadas por coma
- Si un dato no existe: "No especifica"

CV:
{texto_cv[:4000]}"""

            try:
                message = client.messages.create(
                    model="claude-haiku-4-5-20251001", max_tokens=1200,
                    messages=[{"role":"user","content":prompt}]
                )
                r = message.content[0].text.strip()
                if "```" in r:
                    r = r.split("```")[1]
                    if r.startswith("json"): r = r[4:]
                datos = json.loads(r[r.find("{"):r.rfind("}")+1])
                datos["Archivo"] = file.name
                resultados.append(datos)
            except Exception as e:
                st.error(f"Error procesando {file.name}: {e}")
            progress_bar.progress((index+1)/len(uploaded_files))

        if resultados:
            df = pd.DataFrame(resultados)
            df["Experiencia_Anos"] = pd.to_numeric(df["Experiencia_Anos"], errors="coerce").fillna(0).astype(int)
            df["Puntaje"]          = pd.to_numeric(df["Puntaje"], errors="coerce").fillna(0)
            df = df.sort_values("Puntaje", ascending=False).reset_index(drop=True)
            df["Ranking"] = df.index + 1
            st.session_state.df_candidatos = df
            status_text.success(f"✅ {len(resultados)} CVs procesados correctamente.")

    if st.session_state.df_candidatos is not None:
        df = st.session_state.df_candidatos.copy()
        tab1, tab2, tab3, tab4 = st.tabs(["🏆 Ranking","📊 Dashboards","🔍 Filtros","📥 Exportar"])

        with tab1:
            st.markdown("## 🏆 Ranking de Candidatos")
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.markdown(f'<div class="metric-card"><h2>{len(df)}</h2><p>Total CVs</p></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><h2 style="color:#4ade80">{len(df[df["Nivel_Potencial"]=="Alto"])}</h2><p>Alto Potencial</p></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><h2 style="color:#fbbf24">{len(df[df["Nivel_Potencial"]=="Medio"])}</h2><p>Potencial Medio</p></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><h2 style="color:#AFA9EC">{len(df[df["Cumple_Requisitos"]==True])}</h2><p>Cumplen Requisitos</p></div>', unsafe_allow_html=True)
            st.markdown("### 🥇 Top Candidatos")
            for _, row in df.head(20).iterrows():
                nivel  = row.get("Nivel_Potencial","Bajo")
                badge  = "badge-alto" if nivel=="Alto" else "badge-medio" if nivel=="Medio" else "badge-bajo"
                cumple = "✅ Cumple" if row.get("Cumple_Requisitos") else "❌ No cumple"
                st.markdown(f"""<div class="candidate-card">
                  <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div><strong style="font-size:16px;color:#f0eeff;">#{row['Ranking']} {row.get('Nombre','N/A')}</strong>
                      &nbsp;<span class="{badge}">{nivel}</span>&nbsp;<small style="color:#AFA9EC;">{cumple}</small></div>
                    <span style="font-size:26px;font-weight:700;color:#7F77DD;">{row.get('Puntaje',0)}/10</span>
                  </div>
                  <div style="margin-top:8px;color:#c4bfee;font-size:13px;">
                    🏢 {row.get('Ultimo_Cargo','N/A')} en {row.get('Ultima_Empresa','N/A')}
                    &nbsp;|&nbsp;📅 {row.get('Experiencia_Anos',0)} años
                    &nbsp;|&nbsp;🎓 {row.get('Educacion_Maxima','N/A')}
                  </div>
                  <div style="margin-top:6px;color:#9890cc;font-size:12px;font-style:italic;">💬 {row.get('Justificacion','')}</div>
                </div>""", unsafe_allow_html=True)

        with tab2:
            PURPLE = ["#26215C","#3C3489","#534AB7","#7F77DD","#AFA9EC","#CECBF6"]
            col_a,col_b = st.columns(2)
            with col_a:
                conteo = df["Nivel_Potencial"].value_counts().reset_index(); conteo.columns=["Nivel","Cantidad"]
                fig1 = px.pie(conteo,values="Cantidad",names="Nivel",title="Distribución por Potencial",hole=0.45,
                              color="Nivel",color_discrete_map={"Alto":"#4ade80","Medio":"#fbbf24","Bajo":"#f87171"})
                fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#f0eeff")
                st.plotly_chart(fig1,use_container_width=True)
            with col_b:
                edu = df["Educacion_Maxima"].value_counts().reset_index(); edu.columns=["Educacion","Cantidad"]
                fig2 = px.bar(edu,x="Cantidad",y="Educacion",orientation="h",title="Nivel Educativo",
                              color="Cantidad",color_continuous_scale=PURPLE)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#f0eeff")
                st.plotly_chart(fig2,use_container_width=True)
            col_c,col_d = st.columns(2)
            with col_c:
                all_hab = []
                for h in df["Habilidades_Tecnicas"].dropna():
                    all_hab.extend([x.strip() for x in str(h).split(",") if x.strip() and x.strip()!="No especifica"])
                if all_hab:
                    df_h = pd.DataFrame(Counter(all_hab).most_common(12),columns=["Habilidad","Frecuencia"])
                    fig3 = px.bar(df_h,x="Frecuencia",y="Habilidad",orientation="h",title="Habilidades Frecuentes",
                                  color="Frecuencia",color_continuous_scale=PURPLE)
                    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#f0eeff")
                    st.plotly_chart(fig3,use_container_width=True)
            with col_d:
                fig5 = px.scatter(df,x="Experiencia_Anos",y="Puntaje",color="Nivel_Potencial",
                                  hover_data=["Nombre","Ultimo_Cargo"],title="Experiencia vs Puntaje",
                                  color_discrete_map={"Alto":"#4ade80","Medio":"#fbbf24","Bajo":"#f87171"})
                fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#f0eeff")
                st.plotly_chart(fig5,use_container_width=True)
            k1,k2,k3,k4 = st.columns(4)
            with k1: st.metric("Experiencia Promedio",f"{df['Experiencia_Anos'].mean():.1f} años")
            with k2: st.metric("Puntaje Promedio",f"{df['Puntaje'].mean():.1f}/10")
            with k3: st.metric("% Cumple Requisitos",f"{len(df[df['Cumple_Requisitos']==True])/len(df)*100:.0f}%")
            with k4: st.metric("% Alto Potencial",f"{len(df[df['Nivel_Potencial']=='Alto'])/len(df)*100:.0f}%")

        with tab3:
            f1,f2,f3,f4 = st.columns(4)
            with f1: fp = st.multiselect("Potencial",["Alto","Medio","Bajo"],default=["Alto","Medio","Bajo"])
            with f2: fe = st.slider("Exp. mínima",0,20,0)
            with f3: fpu = st.slider("Puntaje mínimo",0.0,10.0,0.0,0.5)
            with f4: fc = st.selectbox("Cumple req.",["Todos","Solo los que cumplen","Solo los que no cumplen"])
            fn = st.text_input("🔎 Buscar nombre, cargo o habilidad")
            df_f = df[df["Nivel_Potencial"].isin(fp)]
            df_f = df_f[df_f["Experiencia_Anos"]>=fe]
            df_f = df_f[df_f["Puntaje"]>=fpu]
            if fc=="Solo los que cumplen":    df_f = df_f[df_f["Cumple_Requisitos"]==True]
            elif fc=="Solo los que no cumplen": df_f = df_f[df_f["Cumple_Requisitos"]==False]
            if fn:
                m = (df_f["Nombre"].str.contains(fn,case=False,na=False)|
                     df_f["Ultimo_Cargo"].str.contains(fn,case=False,na=False)|
                     df_f["Habilidades_Tecnicas"].str.contains(fn,case=False,na=False))
                df_f = df_f[m]
            st.markdown(f"**{len(df_f)} candidatos encontrados**")
            cols = ["Ranking","Nombre","Puntaje","Nivel_Potencial","Ultimo_Cargo","Experiencia_Anos","Educacion_Maxima","Habilidades_Tecnicas","Idiomas","Correo","Cumple_Requisitos"]
            st.dataframe(df_f[[c for c in cols if c in df_f.columns]],use_container_width=True,height=500)

        with tab4:
            op = st.radio("¿Qué exportar?",["Todos","Solo Alto Potencial","Solo los que cumplen","Top 10"])
            df_exp = df.copy()
            if op=="Solo Alto Potencial":     df_exp = df[df["Nivel_Potencial"]=="Alto"]
            elif op=="Solo los que cumplen":  df_exp = df[df["Cumple_Requisitos"]==True]
            elif op=="Top 10":                df_exp = df.head(10)
            st.info(f"Se exportarán **{len(df_exp)} candidatos**")
            output = io.BytesIO()
            with pd.ExcelWriter(output,engine='openpyxl') as writer:
                df_exp.to_excel(writer,index=False,sheet_name='Candidatos')
                ws = writer.sheets['Candidatos']
                from openpyxl.styles import PatternFill,Font,Alignment,Border,Side
                hf = PatternFill(start_color="26215C",end_color="26215C",fill_type="solid")
                af = PatternFill(start_color="1a4731",end_color="1a4731",fill_type="solid")
                mf = PatternFill(start_color="4a3800",end_color="4a3800",fill_type="solid")
                bf = PatternFill(start_color="4a1c1c",end_color="4a1c1c",fill_type="solid")
                pf = PatternFill(start_color="1a1535",end_color="1a1535",fill_type="solid")
                bo = Border(left=Side(style='thin'),right=Side(style='thin'),top=Side(style='thin'),bottom=Side(style='thin'))
                for cn,col in enumerate(df_exp.columns,1):
                    c=ws.cell(row=1,column=cn); c.font=Font(bold=True,color="FFFFFF",size=11)
                    c.fill=hf; c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True); c.border=bo
                for rn,(_, rd) in enumerate(df_exp.iterrows(),2):
                    nv=rd.get("Nivel_Potencial","")
                    fc2=(af if nv=="Alto" else mf if nv=="Medio" else bf if nv=="Bajo" else pf if rn%2==0 else None)
                    for cn in range(1,len(df_exp.columns)+1):
                        c=ws.cell(row=rn,column=cn)
                        c.alignment=Alignment(horizontal="left",vertical="center",wrap_text=True); c.border=bo
                        if fc2: c.fill=fc2
                anchos={"Ranking":8,"Nombre":22,"Correo":28,"Telefono":15,"Educacion_Maxima":20,"Universidad":22,
                        "Carrera":20,"Ultimo_Cargo":25,"Ultima_Empresa":22,"Experiencia_Anos":12,
                        "Habilidades_Tecnicas":35,"Habilidades_Blandas":28,"Idiomas":15,"Certificaciones":25,
                        "Puntaje":10,"Nivel_Potencial":14,"Justificacion":40,"Cumple_Requisitos":15,
                        "Requisitos_Cumplidos":30,"Requisitos_Faltantes":30}
                for cn,col in enumerate(df_exp.columns,1):
                    ws.column_dimensions[ws.cell(row=1,column=cn).column_letter].width=anchos.get(col,18)
                ws.row_dimensions[1].height=30
                for r in range(2,len(df_exp)+2): ws.row_dimensions[r].height=35
            st.download_button("📥 Descargar Excel",data=output.getvalue(),
                file_name=f"RecrutAI_CVs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 2: ANÁLISIS DE PROVEEDORES
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 🏢 Módulo de Análisis de Proveedores")

    tab_buscar, tab_subir, tab_comparar, tab_dash, tab_export = st.tabs([
        "🌐 Buscar en Internet",
        "📄 Analizar Documentos",
        "⚖️ Comparar Proveedores",
        "📊 Dashboards",
        "📥 Exportar"
    ])

    # ── TAB: BUSCAR EN INTERNET ───────────────────────────────────────────────
    with tab_buscar:
        st.markdown("### 🌐 Búsqueda de Proveedores en Internet")
        st.markdown("<p style='color:#AFA9EC;'>Describe qué tipo de proveedor necesitas y la app buscará empresas reales verificadas.</p>", unsafe_allow_html=True)

        col_q1, col_q2 = st.columns([3,1])
        with col_q1:
            query_usuario = st.text_area(
                "📝 Describe qué proveedor necesitas",
                placeholder="Ej: Necesito proveedores de servicios de nómina y RRHH para una empresa de 200 empleados en Perú, con soporte en español y experiencia en el sector retail.",
                height=100
            )
        with col_q2:
            num_resultados = st.selectbox("Cantidad de proveedores", [5, 8, 10, 15], index=1)
            incluir_precios = st.checkbox("Incluir rango de precios", value=True)
            incluir_contacto = st.checkbox("Incluir contacto/web", value=True)

        if st.button("🔍 Buscar Proveedores", type="primary", use_container_width=True):
            if not query_usuario.strip():
                st.warning("Por favor describe qué proveedor necesitas.")
            else:
                with st.spinner("🔎 Buscando proveedores reales en internet..."):
                    contexto_busqueda = f"""
País/región: {pais_busqueda or 'no especificado'}
Rubro: {rubro_busqueda or 'no especificado'}
Presupuesto: {presupuesto_ref}
Cobertura requerida: {cobertura_req}
Certificaciones requeridas: {cert_requeridas or 'ninguna'}
"""
                    prompt_busqueda = f"""Eres un consultor especialista en procurement y selección de proveedores.
El usuario necesita: {query_usuario}

Contexto adicional:
{contexto_busqueda}

Usa tu herramienta de búsqueda web para encontrar {num_resultados} proveedores REALES y VERIFICADOS que cumplan con estos requisitos.

IMPORTANTE:
- Solo incluye empresas que realmente existan y sean legales
- Verifica que tengan presencia web real
- Prioriza empresas con buena reputación y trayectoria
- Incluye solo información que puedas verificar

Responde EXCLUSIVAMENTE con un JSON válido con esta estructura (sin texto adicional):
{{
  "proveedores": [
    {{
      "nombre": "Nombre real de la empresa",
      "descripcion": "Qué hace la empresa en 1-2 oraciones",
      "sitio_web": "URL real del sitio",
      "pais_sede": "País principal",
      "cobertura": "Local/Nacional/Regional/Internacional",
      "años_experiencia": "Número aproximado o rango",
      "certificaciones": "Certificaciones verificadas o No especifica",
      "rango_precio": "{'Rango estimado o No público' if incluir_precios else 'No solicitado'}",
      "contacto": "{'Email o teléfono de contacto' if incluir_contacto else 'No solicitado'}",
      "fortalezas": "3 fortalezas principales separadas por coma",
      "clientes_referencia": "Empresas conocidas que usan este proveedor o No público",
      "puntaje_recomendacion": 0,
      "razon_recomendacion": "Por qué se recomienda para este caso específico"
    }}
  ],
  "resumen_busqueda": "Breve análisis del mercado de proveedores encontrado"
}}

Puntaje_recomendacion del 1 al 10 según qué tan bien se ajusta al requerimiento del usuario."""

                    try:
                        message = client.messages.create(
                            model="claude-sonnet-4-6",
                            max_tokens=4000,
                            tools=[{"type": "web_search_20250305", "name": "web_search"}],
                            messages=[{"role": "user", "content": prompt_busqueda}]
                        )
                        # Extraer texto de la respuesta (puede tener bloques de tool_use)
                        texto_respuesta = ""
                        for block in message.content:
                            if hasattr(block, "text"):
                                texto_respuesta += block.text

                        # Limpiar y parsear JSON
                        if "```" in texto_respuesta:
                            texto_respuesta = texto_respuesta.split("```")[1]
                            if texto_respuesta.startswith("json"):
                                texto_respuesta = texto_respuesta[4:]
                        inicio = texto_respuesta.find("{")
                        fin    = texto_respuesta.rfind("}") + 1
                        datos_prov = json.loads(texto_respuesta[inicio:fin])

                        st.session_state.proveedores_web = datos_prov.get("proveedores", [])
                        resumen = datos_prov.get("resumen_busqueda", "")

                        if resumen:
                            st.info(f"📊 **Análisis del mercado:** {resumen}")

                    except Exception as e:
                        st.error(f"Error en búsqueda: {e}")
                        # Fallback: Claude sin web search
                        try:
                            msg2 = client.messages.create(
                                model="claude-haiku-4-5-20251001", max_tokens=3000,
                                messages=[{"role":"user","content": prompt_busqueda + "\n\nNota: Usa tu conocimiento entrenado para identificar proveedores reales conocidos."}]
                            )
                            r2 = msg2.content[0].text.strip()
                            if "```" in r2:
                                r2 = r2.split("```")[1]
                                if r2.startswith("json"): r2 = r2[4:]
                            datos_prov2 = json.loads(r2[r2.find("{"):r2.rfind("}")+1])
                            st.session_state.proveedores_web = datos_prov2.get("proveedores", [])
                            st.warning("⚠️ Resultados basados en conocimiento del modelo (sin búsqueda en vivo). Verifica la información antes de contactar.")
                        except Exception as e2:
                            st.error(f"Error en fallback: {e2}")

        # Mostrar resultados de búsqueda
        if st.session_state.proveedores_web:
            provs = st.session_state.proveedores_web
            st.markdown(f"### ✅ {len(provs)} Proveedores Encontrados")

            # Ordenar por puntaje
            provs_sorted = sorted(provs, key=lambda x: float(str(x.get("puntaje_recomendacion",0)).replace(",",".")) if str(x.get("puntaje_recomendacion",0)).replace(".","").replace(",","").isdigit() else 0, reverse=True)

            for i, prov in enumerate(provs_sorted, 1):
                puntaje = prov.get("puntaje_recomendacion", 0)
                try: puntaje_num = float(str(puntaje))
                except: puntaje_num = 0
                badge_clase = "badge-prov-a" if puntaje_num >= 8 else "badge-prov-b" if puntaje_num >= 6 else "badge-prov-c"
                nivel_texto = "Muy recomendado" if puntaje_num >= 8 else "Recomendado" if puntaje_num >= 6 else "Opción viable"

                st.markdown(f"""
                <div class="proveedor-card">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div style="flex:1;">
                      <strong style="font-size:16px;color:#f0eeff;">#{i} {prov.get('nombre','N/A')}</strong>
                      &nbsp;<span class="{badge_clase}">{nivel_texto}</span>
                      <div style="margin-top:6px;color:#c4bfee;font-size:13px;">{prov.get('descripcion','')}</div>
                    </div>
                    <div style="text-align:right;min-width:70px;">
                      <span style="font-size:26px;font-weight:700;color:#34d399;">{puntaje}/10</span>
                    </div>
                  </div>
                  <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:8px;font-size:12px;color:#AFA9EC;">
                    <span>🌍 {prov.get('pais_sede','N/A')}</span>
                    <span>📍 {prov.get('cobertura','N/A')}</span>
                    <span>📅 {prov.get('años_experiencia','N/A')} años</span>
                    <span>💰 {prov.get('rango_precio','N/A')}</span>
                    <span>📋 {prov.get('certificaciones','N/A')}</span>
                  </div>
                  <div style="margin-top:8px;font-size:12px;color:#AFA9EC;">
                    🌐 <a href="{prov.get('sitio_web','#')}" target="_blank" style="color:#7F77DD;">{prov.get('sitio_web','N/A')}</a>
                    &nbsp;|&nbsp;📞 {prov.get('contacto','N/A')}
                  </div>
                  <div style="margin-top:6px;font-size:12px;color:#86efac;">✨ {prov.get('fortalezas','')}</div>
                  <div style="margin-top:4px;font-size:11px;color:#9890cc;font-style:italic;">💬 {prov.get('razon_recomendacion','')}</div>
                </div>
                """, unsafe_allow_html=True)

            # Guardar en df para comparación
            if st.button("➕ Agregar estos proveedores al comparador", use_container_width=True):
                df_web = pd.DataFrame(provs_sorted)
                if st.session_state.df_proveedores is None:
                    st.session_state.df_proveedores = df_web
                else:
                    st.session_state.df_proveedores = pd.concat([st.session_state.df_proveedores, df_web], ignore_index=True).drop_duplicates(subset=["nombre"])
                st.success("✅ Proveedores agregados al comparador.")

    # ── TAB: ANALIZAR DOCUMENTOS ──────────────────────────────────────────────
    with tab_subir:
        st.markdown("### 📄 Analizar Documentos de Proveedores")
        st.markdown("<p style='color:#AFA9EC;'>Sube propuestas, RFPs, fichas técnicas o presentaciones de proveedores en PDF para analizarlas y compararlas.</p>", unsafe_allow_html=True)

        docs_proveedores = st.file_uploader(
            "📂 Sube documentos de proveedores (PDF)",
            type=["pdf"], accept_multiple_files=True,
            key="docs_prov"
        )
        if docs_proveedores:
            st.info(f"📋 **{len(docs_proveedores)}** documento(s) cargado(s).")

        if docs_proveedores and st.button("🔍 Analizar Documentos de Proveedores", type="primary", use_container_width=True):
            resultados_prov = []
            pb = st.progress(0)
            st_txt = st.empty()
            cert_lista = [c.strip() for c in cert_requeridas.split("\n") if c.strip()]

            for idx, doc in enumerate(docs_proveedores):
                st_txt.markdown(f"⏳ Analizando **{idx+1}/{len(docs_proveedores)}**: {doc.name}")
                try:
                    reader = PdfReader(doc)
                    texto  = "".join(p.extract_text() or "" for p in reader.pages)
                except Exception as e:
                    st.error(f"Error leyendo {doc.name}: {e}"); continue

                prompt_prov = f"""Eres un experto en procurement y evaluación de proveedores.
Analiza este documento de proveedor y extrae información estructurada.
Responde EXCLUSIVAMENTE con JSON válido, sin texto adicional.

Contexto de evaluación:
- País/región buscado: {pais_busqueda or 'no especificado'}
- Presupuesto: {presupuesto_ref}
- Certificaciones requeridas: {', '.join(cert_lista) or 'ninguna'}
- Cobertura requerida: {cobertura_req}
- Pesos: Precio {ppeso_precio}%, Certificaciones {ppeso_cert}%, Reputación {ppeso_rep}%, Cobertura {ppeso_cob}%

Formato JSON:
{{"nombre_empresa":"","descripcion":"","sitio_web":"","pais_sede":"","cobertura":"",
"años_experiencia":"","certificaciones":"","productos_servicios":"",
"rango_precio":"","condiciones_comerciales":"","tiempo_entrega":"",
"clientes_referencia":"","fortalezas":"","debilidades":"",
"puntaje_precio":0,"puntaje_certificaciones":0,"puntaje_reputacion":0,"puntaje_cobertura":0,
"puntaje_recomendacion":0,"nivel_recomendacion":"","justificacion":"",
"cumple_certificaciones":false,"certificaciones_faltantes":""}}

Instrucciones:
- Puntajes del 1 al 10 según los criterios indicados
- puntaje_recomendacion: promedio ponderado según los pesos dados
- nivel_recomendacion: "Muy recomendado" si >= 8, "Recomendado" si >= 6, "Opción viable" si >= 4, "No recomendado" si < 4
- cumple_certificaciones: true si tiene todas las certificaciones requeridas
- Si un dato no está en el documento: "No especifica"

Documento:
{texto[:4000]}"""

                try:
                    msg = client.messages.create(
                        model="claude-haiku-4-5-20251001", max_tokens=1500,
                        messages=[{"role":"user","content":prompt_prov}]
                    )
                    r = msg.content[0].text.strip()
                    if "```" in r:
                        r = r.split("```")[1]
                        if r.startswith("json"): r = r[4:]
                    datos = json.loads(r[r.find("{"):r.rfind("}")+1])
                    datos["Archivo"] = doc.name
                    datos["Fuente"]  = "Documento"
                    resultados_prov.append(datos)
                except Exception as e:
                    st.error(f"Error procesando {doc.name}: {e}")
                pb.progress((idx+1)/len(docs_proveedores))

            if resultados_prov:
                df_new = pd.DataFrame(resultados_prov)
                if st.session_state.df_proveedores is None:
                    st.session_state.df_proveedores = df_new
                else:
                    st.session_state.df_proveedores = pd.concat(
                        [st.session_state.df_proveedores, df_new], ignore_index=True
                    ).drop_duplicates(subset=["nombre_empresa"] if "nombre_empresa" in df_new.columns else None)
                st_txt.success(f"✅ {len(resultados_prov)} documentos analizados y agregados al comparador.")

    # ── TAB: COMPARAR ─────────────────────────────────────────────────────────
    with tab_comparar:
        st.markdown("### ⚖️ Comparación de Proveedores")
        if st.session_state.df_proveedores is None or len(st.session_state.df_proveedores) == 0:
            st.info("👆 Primero busca proveedores en internet o analiza documentos para poder compararlos.")
        else:
            df_p = st.session_state.df_proveedores.copy()
            nombre_col = "nombre" if "nombre" in df_p.columns else "nombre_empresa" if "nombre_empresa" in df_p.columns else df_p.columns[0]

            # Normalizar columna de nombre
            if "nombre" not in df_p.columns and "nombre_empresa" in df_p.columns:
                df_p["nombre"] = df_p["nombre_empresa"]

            st.markdown(f"**{len(df_p)} proveedores en el comparador**")

            # Seleccionar proveedores a comparar
            todos_nombres = df_p["nombre"].tolist()
            seleccionados = st.multiselect("Selecciona proveedores a comparar", todos_nombres, default=todos_nombres[:min(5,len(todos_nombres))])

            if seleccionados:
                df_sel = df_p[df_p["nombre"].isin(seleccionados)].copy()

                # Normalizar puntaje
                for col in ["puntaje_recomendacion","puntaje_precio","puntaje_certificaciones","puntaje_reputacion","puntaje_cobertura"]:
                    if col in df_sel.columns:
                        df_sel[col] = pd.to_numeric(df_sel[col], errors="coerce").fillna(0)

                if "puntaje_recomendacion" in df_sel.columns:
                    df_sel = df_sel.sort_values("puntaje_recomendacion", ascending=False).reset_index(drop=True)
                    df_sel["Ranking"] = df_sel.index + 1

                # Tabla comparativa visual
                st.markdown("#### 🏆 Ranking General")
                for _, row in df_sel.iterrows():
                    puntaje = row.get("puntaje_recomendacion", 0)
                    nivel   = row.get("nivel_recomendacion", "Opción viable")
                    badge_c = "badge-prov-a" if puntaje >= 8 else "badge-prov-b" if puntaje >= 6 else "badge-prov-c"
                    st.markdown(f"""
                    <div class="proveedor-card">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                          <strong style="color:#f0eeff;font-size:15px;">#{row.get('Ranking','?')} {row.get('nombre','N/A')}</strong>
                          &nbsp;<span class="{badge_c}">{nivel}</span>
                          <div style="color:#AFA9EC;font-size:12px;margin-top:4px;">{row.get('descripcion',row.get('productos_servicios',''))[:120]}...</div>
                        </div>
                        <div style="text-align:right;">
                          <span style="font-size:24px;font-weight:700;color:#34d399;">{puntaje}/10</span>
                        </div>
                      </div>
                      <div style="margin-top:10px;display:grid;grid-template-columns:repeat(4,1fr);gap:8px;text-align:center;">
                        <div style="background:#12111a;border-radius:8px;padding:8px;">
                          <div style="color:#fbbf24;font-size:16px;font-weight:700;">{row.get('puntaje_precio','-')}</div>
                          <div style="color:#AFA9EC;font-size:11px;">💰 Precio</div>
                        </div>
                        <div style="background:#12111a;border-radius:8px;padding:8px;">
                          <div style="color:#60a5fa;font-size:16px;font-weight:700;">{row.get('puntaje_certificaciones','-')}</div>
                          <div style="color:#AFA9EC;font-size:11px;">📋 Certif.</div>
                        </div>
                        <div style="background:#12111a;border-radius:8px;padding:8px;">
                          <div style="color:#f472b6;font-size:16px;font-weight:700;">{row.get('puntaje_reputacion','-')}</div>
                          <div style="color:#AFA9EC;font-size:11px;">⭐ Reput.</div>
                        </div>
                        <div style="background:#12111a;border-radius:8px;padding:8px;">
                          <div style="color:#34d399;font-size:16px;font-weight:700;">{row.get('puntaje_cobertura','-')}</div>
                          <div style="color:#AFA9EC;font-size:11px;">📍 Cobert.</div>
                        </div>
                      </div>
                      <div style="margin-top:8px;font-size:12px;color:#9890cc;font-style:italic;">💬 {row.get('justificacion','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Radar chart comparativo
                if len(df_sel) > 1:
                    st.markdown("#### 📡 Radar de Comparación")
                    criterios = ["puntaje_precio","puntaje_certificaciones","puntaje_reputacion","puntaje_cobertura"]
                    criterios_existentes = [c for c in criterios if c in df_sel.columns]
                    if criterios_existentes:
                        import plotly.graph_objects as go
                        fig_radar = go.Figure()
                        colores_radar = ["#7F77DD","#34d399","#fbbf24","#f87171","#60a5fa"]
                        labels_cortos = {"puntaje_precio":"Precio","puntaje_certificaciones":"Certif.","puntaje_reputacion":"Reput.","puntaje_cobertura":"Cobert."}
                        cats = [labels_cortos.get(c,c) for c in criterios_existentes]
                        for i, (_, row) in enumerate(df_sel.iterrows()):
                            vals = [float(row.get(c,0)) for c in criterios_existentes]
                            fig_radar.add_trace(go.Scatterpolar(
                                r=vals+[vals[0]], theta=cats+[cats[0]],
                                fill='toself', name=row.get("nombre","Proveedor"),
                                line_color=colores_radar[i % len(colores_radar)],
                                fillcolor=colores_radar[i % len(colores_radar)],
                                opacity=0.3
                            ))
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True,range=[0,10],color="#AFA9EC"),
                                       bgcolor="#1e1b2e", angularaxis=dict(color="#AFA9EC")),
                            paper_bgcolor="rgba(0,0,0,0)", font_color="#f0eeff",
                            legend=dict(bgcolor="#1e1b2e",bordercolor="#534AB7",borderwidth=1),
                            height=450
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)

                # Tabla detallada
                st.markdown("#### 📋 Tabla Comparativa Detallada")
                cols_mostrar = ["nombre","cobertura","años_experiencia","certificaciones",
                                "rango_precio","condiciones_comerciales","puntaje_recomendacion","nivel_recomendacion"]
                cols_ok = [c for c in cols_mostrar if c in df_sel.columns]
                st.dataframe(df_sel[cols_ok], use_container_width=True, height=300)

                if st.button("🗑️ Limpiar comparador", use_container_width=True):
                    st.session_state.df_proveedores = None
                    st.session_state.proveedores_web = []
                    st.rerun()

    # ── TAB: DASHBOARDS PROVEEDORES ───────────────────────────────────────────
    with tab_dash:
        st.markdown("### 📊 Dashboards de Proveedores")
        if st.session_state.df_proveedores is None or len(st.session_state.df_proveedores) == 0:
            st.info("Agrega proveedores desde las pestañas anteriores para ver los dashboards.")
        else:
            df_p = st.session_state.df_proveedores.copy()
            if "nombre" not in df_p.columns and "nombre_empresa" in df_p.columns:
                df_p["nombre"] = df_p["nombre_empresa"]
            for col in ["puntaje_recomendacion","puntaje_precio","puntaje_certificaciones","puntaje_reputacion","puntaje_cobertura"]:
                if col in df_p.columns:
                    df_p[col] = pd.to_numeric(df_p[col], errors="coerce").fillna(0)

            VERDE = ["#04342C","#085041","#0F6E56","#1D9E75","#5DCAA5","#9FE1CB"]
            col1, col2 = st.columns(2)

            with col1:
                if "cobertura" in df_p.columns:
                    cob = df_p["cobertura"].value_counts().reset_index(); cob.columns=["Cobertura","Cantidad"]
                    fig_c = px.pie(cob,values="Cantidad",names="Cobertura",title="Distribución por Cobertura",
                                   hole=0.4,color_discrete_sequence=VERDE)
                    fig_c.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#f0eeff")
                    st.plotly_chart(fig_c,use_container_width=True)

            with col2:
                if "nivel_recomendacion" in df_p.columns:
                    niv = df_p["nivel_recomendacion"].value_counts().reset_index(); niv.columns=["Nivel","Cantidad"]
                    fig_n = px.bar(niv,x="Nivel",y="Cantidad",title="Proveedores por Nivel de Recomendación",
                                   color="Cantidad",color_continuous_scale=VERDE)
                    fig_n.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#f0eeff")
                    st.plotly_chart(fig_n,use_container_width=True)

            # Ranking visual
            if "puntaje_recomendacion" in df_p.columns and "nombre" in df_p.columns:
                df_rank = df_p[["nombre","puntaje_recomendacion","puntaje_precio","puntaje_certificaciones","puntaje_reputacion","puntaje_cobertura"]].copy()
                df_rank = df_rank.sort_values("puntaje_recomendacion",ascending=True).tail(10)
                fig_rank = px.bar(df_rank,x="puntaje_recomendacion",y="nombre",orientation="h",
                                  title="Top Proveedores por Puntaje",
                                  color="puntaje_recomendacion",color_continuous_scale=VERDE)
                fig_rank.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#f0eeff")
                st.plotly_chart(fig_rank,use_container_width=True)

            k1,k2,k3 = st.columns(3)
            with k1: st.metric("Total Proveedores", len(df_p))
            with k2:
                if "puntaje_recomendacion" in df_p.columns:
                    st.metric("Puntaje Promedio", f"{df_p['puntaje_recomendacion'].mean():.1f}/10")
            with k3:
                if "nivel_recomendacion" in df_p.columns:
                    top = len(df_p[df_p["nivel_recomendacion"]=="Muy recomendado"])
                    st.metric("Muy Recomendados", top)

    # ── TAB: EXPORTAR PROVEEDORES ─────────────────────────────────────────────
    with tab_export:
        st.markdown("### 📥 Exportar Análisis de Proveedores")
        if st.session_state.df_proveedores is None or len(st.session_state.df_proveedores) == 0:
            st.info("No hay proveedores para exportar aún.")
        else:
            df_p = st.session_state.df_proveedores.copy()
            if "nombre" not in df_p.columns and "nombre_empresa" in df_p.columns:
                df_p["nombre"] = df_p["nombre_empresa"]

            op_p = st.radio("¿Qué exportar?",["Todos los proveedores","Solo Muy Recomendados","Solo Recomendados","Top 5"])
            df_exp_p = df_p.copy()
            if "nivel_recomendacion" in df_p.columns:
                if op_p=="Solo Muy Recomendados":   df_exp_p = df_p[df_p["nivel_recomendacion"]=="Muy recomendado"]
                elif op_p=="Solo Recomendados":      df_exp_p = df_p[df_p["nivel_recomendacion"].isin(["Muy recomendado","Recomendado"])]
            if op_p=="Top 5":
                if "puntaje_recomendacion" in df_p.columns:
                    df_exp_p = df_p.sort_values("puntaje_recomendacion",ascending=False).head(5)
                else:
                    df_exp_p = df_p.head(5)

            st.info(f"Se exportarán **{len(df_exp_p)} proveedores**")
            out_p = io.BytesIO()
            with pd.ExcelWriter(out_p,engine='openpyxl') as writer:
                df_exp_p.to_excel(writer,index=False,sheet_name='Proveedores')
                ws2 = writer.sheets['Proveedores']
                from openpyxl.styles import PatternFill,Font,Alignment,Border,Side
                hf2 = PatternFill(start_color="085041",end_color="085041",fill_type="solid")
                af2 = PatternFill(start_color="0a2e1f",end_color="0a2e1f",fill_type="solid")
                pf2 = PatternFill(start_color="0d1f15",end_color="0d1f15",fill_type="solid")
                bo2 = Border(left=Side(style='thin'),right=Side(style='thin'),top=Side(style='thin'),bottom=Side(style='thin'))
                for cn,col in enumerate(df_exp_p.columns,1):
                    c=ws2.cell(row=1,column=cn)
                    c.font=Font(bold=True,color="FFFFFF",size=11)
                    c.fill=hf2; c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True); c.border=bo2
                for rn,(_, rd) in enumerate(df_exp_p.iterrows(),2):
                    fc3=(af2 if rn%2==0 else pf2)
                    for cn in range(1,len(df_exp_p.columns)+1):
                        c=ws2.cell(row=rn,column=cn)
                        c.alignment=Alignment(horizontal="left",vertical="center",wrap_text=True)
                        c.border=bo2; c.fill=fc3
                for cn,col in enumerate(df_exp_p.columns,1):
                    ws2.column_dimensions[ws2.cell(row=1,column=cn).column_letter].width=25
                ws2.row_dimensions[1].height=30
                for r in range(2,len(df_exp_p)+2): ws2.row_dimensions[r].height=35

            st.download_button("📥 Descargar Excel de Proveedores",data=out_p.getvalue(),
                file_name="RecrutAI_Proveedores.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
