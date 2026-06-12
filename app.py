import streamlit as st
import anthropic
import pandas as pd
from pypdf import PdfReader
import io
import json
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

st.set_page_config(page_title="RecruitAI Pro", page_icon="🎯", layout="wide")

# CSS personalizado
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f, #2d6a9f);
        padding: 20px; border-radius: 12px;
        text-align: center; color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .candidate-card {
        background: #1e2130; border: 1px solid #2d6a9f;
        border-radius: 10px; padding: 15px; margin: 8px 0;
        color: white;
    }
    .badge-alto { background: #1a6b3c; color: #4ade80; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-medio { background: #7a5c00; color: #fbbf24; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-bajo { background: #7a1f1f; color: #f87171; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .stProgress > div > div { background: linear-gradient(90deg, #2d6a9f, #4ade80); }
    h1, h2, h3 { color: #e2e8f0 !important; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; }
    .stTabs [aria-selected="true"] { color: #60a5fa !important; border-bottom: 2px solid #60a5fa; }
</style>
""", unsafe_allow_html=True)

try:
    api_key_segura = st.secrets["CLAUDE_API_KEY"]
except Exception:
    st.error("⚠️ No se encontró la API Key en los Secrets de Streamlit Cloud.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key_segura)

# Header
st.markdown("# 🎯 RecruitAI Pro")
st.markdown("### Plataforma inteligente de análisis y clasificación de candidatos")
st.divider()

# ── SIDEBAR: Requisitos del puesto ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configurar Puesto")
    st.markdown("Define los requisitos para clasificar y filtrar candidatos.")

    puesto = st.text_input("🏢 Nombre del puesto", placeholder="Ej: Analista de Datos")
    experiencia_min = st.slider("📅 Años mínimos de experiencia", 0, 20, 2)
    educacion_req = st.selectbox("🎓 Educación mínima requerida", [
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
    st.markdown("**Criterios de puntuación:**")
    peso_exp = st.slider("Peso: Experiencia", 0, 100, 35)
    peso_edu = st.slider("Peso: Educación", 0, 100, 25)
    peso_hab = st.slider("Peso: Habilidades", 0, 100, 30)
    peso_idi = st.slider("Peso: Idiomas", 0, 100, 10)

# ── INICIALIZAR SESSION STATE ────────────────────────────────────────────────
if "df_candidatos" not in st.session_state:
    st.session_state.df_candidatos = None

# ── CARGA DE ARCHIVOS ────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "📂 Sube los CVs en PDF (puedes subir más de 100 archivos)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"📋 {len(uploaded_files)} archivo(s) cargado(s). Listo para procesar.")

if uploaded_files and st.button("🚀 Procesar y Clasificar Candidatos", type="primary", use_container_width=True):
    resultados = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    habilidades_lista = [h.strip().lower() for h in habilidades_req.split("\n") if h.strip()]

    for index, file in enumerate(uploaded_files):
        status_text.write(f"⏳ Analizando {index+1}/{len(uploaded_files)}: {file.name}")
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
        # Asegurar tipos correctos
        df["Experiencia_Anos"] = pd.to_numeric(df["Experiencia_Anos"], errors="coerce").fillna(0).astype(int)
        df["Puntaje"] = pd.to_numeric(df["Puntaje"], errors="coerce").fillna(0)
        df = df.sort_values("Puntaje", ascending=False).reset_index(drop=True)
        df["Ranking"] = df.index + 1
        st.session_state.df_candidatos = df
        status_text.success(f"✅ {len(resultados)} CVs procesados y clasificados.")

# ── MOSTRAR RESULTADOS ───────────────────────────────────────────────────────
if st.session_state.df_candidatos is not None:
    df = st.session_state.df_candidatos.copy()

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 Ranking & Clasificación",
        "📊 Dashboards & Métricas",
        "🔍 Filtros & Búsqueda",
        "📥 Exportar"
    ])

    # ── TAB 1: RANKING ───────────────────────────────────────────────────────
    with tab1:
        st.markdown("## 🏆 Ranking de Candidatos por Potencial")

        col1, col2, col3, col4 = st.columns(4)
        total = len(df)
        altos = len(df[df["Nivel_Potencial"] == "Alto"])
        medios = len(df[df["Nivel_Potencial"] == "Medio"])
        cumplen = len(df[df["Cumple_Requisitos"] == True])

        with col1:
            st.markdown(f'<div class="metric-card"><h2>{total}</h2><p>Total CVs</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><h2 style="color:#4ade80">{altos}</h2><p>Alto Potencial</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><h2 style="color:#fbbf24">{medios}</h2><p>Potencial Medio</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><h2 style="color:#60a5fa">{cumplen}</h2><p>Cumplen Requisitos</p></div>', unsafe_allow_html=True)

        st.markdown("### 🥇 Top Candidatos")
        for _, row in df.head(20).iterrows():
            nivel = row.get("Nivel_Potencial", "Bajo")
            badge_class = "badge-alto" if nivel == "Alto" else "badge-medio" if nivel == "Medio" else "badge-bajo"
            puntaje = row.get("Puntaje", 0)
            cumple = "✅ Cumple requisitos" if row.get("Cumple_Requisitos") else "❌ No cumple"
            st.markdown(f"""
            <div class="candidate-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <strong style="font-size:16px; color:#e2e8f0;">#{row['Ranking']} {row.get('Nombre','N/A')}</strong>
                        &nbsp;&nbsp;<span class="{badge_class}">{nivel}</span>
                        &nbsp;&nbsp;<small style="color:#94a3b8;">{cumple}</small>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:24px; font-weight:bold; color:#60a5fa;">{puntaje}/10</span>
                    </div>
                </div>
                <div style="margin-top:8px; color:#94a3b8; font-size:13px;">
                    🏢 {row.get('Ultimo_Cargo','N/A')} en {row.get('Ultima_Empresa','N/A')} &nbsp;|&nbsp;
                    📅 {row.get('Experiencia_Anos',0)} años exp. &nbsp;|&nbsp;
                    🎓 {row.get('Educacion_Maxima','N/A')}
                </div>
                <div style="margin-top:6px; color:#a0aec0; font-size:12px; font-style:italic;">
                    💬 {row.get('Justificacion','Sin justificación')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2: DASHBOARDS ────────────────────────────────────────────────────
    with tab2:
        st.markdown("## 📊 Dashboards & Métricas")

        col_a, col_b = st.columns(2)

        with col_a:
            # Distribución por potencial
            conteo_potencial = df["Nivel_Potencial"].value_counts().reset_index()
            conteo_potencial.columns = ["Nivel", "Cantidad"]
            fig1 = px.pie(conteo_potencial, values="Cantidad", names="Nivel",
                         title="Distribución por Nivel de Potencial",
                         color="Nivel",
                         color_discrete_map={"Alto": "#4ade80", "Medio": "#fbbf24", "Bajo": "#f87171"},
                         hole=0.4)
            fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig1, use_container_width=True)

        with col_b:
            # Distribución por educación
            conteo_edu = df["Educacion_Maxima"].value_counts().reset_index()
            conteo_edu.columns = ["Educacion", "Cantidad"]
            fig2 = px.bar(conteo_edu, x="Cantidad", y="Educacion", orientation="h",
                         title="Distribución por Nivel Educativo",
                         color="Cantidad", color_continuous_scale="Blues")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig2, use_container_width=True)

        col_c, col_d = st.columns(2)

        with col_c:
            # Habilidades más comunes
            todas_habilidades = []
            for hab in df["Habilidades_Tecnicas"].dropna():
                todas_habilidades.extend([h.strip() for h in str(hab).split(",") if h.strip() and h.strip() != "No especifica"])
            conteo_hab = Counter(todas_habilidades).most_common(12)
            if conteo_hab:
                df_hab = pd.DataFrame(conteo_hab, columns=["Habilidad", "Frecuencia"])
                fig3 = px.bar(df_hab, x="Frecuencia", y="Habilidad", orientation="h",
                             title="Habilidades Técnicas más Frecuentes",
                             color="Frecuencia", color_continuous_scale="Teal")
                fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig3, use_container_width=True)

        with col_d:
            # Distribución por idiomas
            todos_idiomas = []
            for idi in df["Idiomas"].dropna():
                todos_idiomas.extend([i.strip() for i in str(idi).split(",") if i.strip() and i.strip() != "No especifica"])
            conteo_idi = Counter(todos_idiomas).most_common(8)
            if conteo_idi:
                df_idi = pd.DataFrame(conteo_idi, columns=["Idioma", "Frecuencia"])
                fig4 = px.pie(df_idi, values="Frecuencia", names="Idioma",
                             title="Distribución por Idiomas",
                             color_discrete_sequence=px.colors.sequential.Blues_r)
                fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig4, use_container_width=True)

        # Experiencia promedio y puntaje
        col_e, col_f = st.columns(2)
        with col_e:
            fig5 = px.histogram(df, x="Experiencia_Anos", nbins=15,
                               title="Distribución de Años de Experiencia",
                               color_discrete_sequence=["#2d6a9f"])
            fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig5, use_container_width=True)

        with col_f:
            fig6 = px.scatter(df, x="Experiencia_Anos", y="Puntaje",
                             color="Nivel_Potencial", hover_data=["Nombre", "Ultimo_Cargo"],
                             title="Experiencia vs Puntaje",
                             color_discrete_map={"Alto": "#4ade80", "Medio": "#fbbf24", "Bajo": "#f87171"})
            fig6.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig6, use_container_width=True)

        # KPIs numéricos
        st.markdown("### 📈 Indicadores Clave")
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            prom_exp = df["Experiencia_Anos"].mean()
            st.metric("Experiencia Promedio", f"{prom_exp:.1f} años")
        with k2:
            prom_puntaje = df["Puntaje"].mean()
            st.metric("Puntaje Promedio", f"{prom_puntaje:.1f}/10")
        with k3:
            pct_cumple = (len(df[df["Cumple_Requisitos"] == True]) / len(df)) * 100
            st.metric("% Cumple Requisitos", f"{pct_cumple:.0f}%")
        with k4:
            pct_alto = (len(df[df["Nivel_Potencial"] == "Alto"]) / len(df)) * 100
            st.metric("% Alto Potencial", f"{pct_alto:.0f}%")

    # ── TAB 3: FILTROS ───────────────────────────────────────────────────────
    with tab3:
        st.markdown("## 🔍 Filtros en Tiempo Real")

        f1, f2, f3, f4 = st.columns(4)
        with f1:
            filtro_potencial = st.multiselect("Nivel de Potencial",
                options=["Alto", "Medio", "Bajo"], default=["Alto", "Medio", "Bajo"])
        with f2:
            filtro_exp = st.slider("Años de experiencia mínimos", 0, 20, 0)
        with f3:
            filtro_puntaje = st.slider("Puntaje mínimo", 0.0, 10.0, 0.0, 0.5)
        with f4:
            filtro_cumple = st.selectbox("Cumple requisitos", ["Todos", "Solo los que cumplen", "Solo los que no cumplen"])

        filtro_nombre = st.text_input("🔎 Buscar por nombre, cargo o habilidad")

        df_filtrado = df.copy()
        df_filtrado = df_filtrado[df_filtrado["Nivel_Potencial"].isin(filtro_potencial)]
        df_filtrado = df_filtrado[df_filtrado["Experiencia_Anos"] >= filtro_exp]
        df_filtrado = df_filtrado[df_filtrado["Puntaje"] >= filtro_puntaje]

        if filtro_cumple == "Solo los que cumplen":
            df_filtrado = df_filtrado[df_filtrado["Cumple_Requisitos"] == True]
        elif filtro_cumple == "Solo los que no cumplen":
            df_filtrado = df_filtrado[df_filtrado["Cumple_Requisitos"] == False]

        if filtro_nombre:
            mascara = (
                df_filtrado["Nombre"].str.contains(filtro_nombre, case=False, na=False) |
                df_filtrado["Ultimo_Cargo"].str.contains(filtro_nombre, case=False, na=False) |
                df_filtrado["Habilidades_Tecnicas"].str.contains(filtro_nombre, case=False, na=False)
            )
            df_filtrado = df_filtrado[mascara]

        st.markdown(f"**{len(df_filtrado)} candidatos encontrados**")

        columnas_mostrar = ["Ranking", "Nombre", "Puntaje", "Nivel_Potencial", "Ultimo_Cargo",
                           "Experiencia_Anos", "Educacion_Maxima", "Habilidades_Tecnicas",
                           "Idiomas", "Correo", "Cumple_Requisitos"]
        columnas_existentes = [c for c in columnas_mostrar if c in df_filtrado.columns]
        st.dataframe(df_filtrado[columnas_existentes], use_container_width=True, height=500)

    # ── TAB 4: EXPORTAR ──────────────────────────────────────────────────────
    with tab4:
        st.markdown("## 📥 Exportar Resultados")

        opciones_export = st.radio("¿Qué candidatos exportar?", [
            "Todos los candidatos",
            "Solo Alto Potencial",
            "Solo los que cumplen requisitos",
            "Top 10 candidatos"
        ])

        df_export = df.copy()
        if opciones_export == "Solo Alto Potencial":
            df_export = df[df["Nivel_Potencial"] == "Alto"]
        elif opciones_export == "Solo los que cumplen requisitos":
            df_export = df[df["Cumple_Requisitos"] == True]
        elif opciones_export == "Top 10 candidatos":
            df_export = df.head(10)

        st.info(f"Se exportarán **{len(df_export)} candidatos**")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Candidatos')
            workbook = writer.book
            worksheet = writer.sheets['Candidatos']

            from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

            color_header = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            color_alto = PatternFill(start_color="1a4731", end_color="1a4731", fill_type="solid")
            color_medio = PatternFill(start_color="4a3800", end_color="4a3800", fill_type="solid")
            color_bajo = PatternFill(start_color="4a1c1c", end_color="4a1c1c", fill_type="solid")
            color_par = PatternFill(start_color="1e2b3a", end_color="1e2b3a", fill_type="solid")
            borde = Border(
                left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin')
            )

            for col_num, col in enumerate(df_export.columns, 1):
                cell = worksheet.cell(row=1, column=col_num)
                cell.font = Font(bold=True, color="FFFFFF", size=11)
                cell.fill = color_header
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = borde

            nivel_col = list(df_export.columns).index("Nivel_Potencial") + 1 if "Nivel_Potencial" in df_export.columns else None

            for row_num, (_, row_data) in enumerate(df_export.iterrows(), 2):
                nivel = row_data.get("Nivel_Potencial", "")
                fila_color = color_alto if nivel == "Alto" else color_medio if nivel == "Medio" else color_bajo if nivel == "Bajo" else (color_par if row_num % 2 == 0 else None)
                for col_num in range(1, len(df_export.columns) + 1):
                    cell = worksheet.cell(row=row_num, column=col_num)
                    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                    cell.border = borde
                    if fila_color:
                        cell.fill = fila_color

            anchos = {
                "Ranking": 8, "Nombre": 22, "Correo": 28, "Telefono": 15,
                "Educacion_Maxima": 20, "Universidad": 22, "Carrera": 20,
                "Ultimo_Cargo": 25, "Ultima_Empresa": 22, "Experiencia_Anos": 12,
                "Habilidades_Tecnicas": 35, "Habilidades_Blandas": 28,
                "Idiomas": 15, "Certificaciones": 25, "Puntaje": 10,
                "Nivel_Potencial": 14, "Justificacion": 40,
                "Cumple_Requisitos": 15, "Requisitos_Cumplidos": 30, "Requisitos_Faltantes": 30
            }
            for col_num, col in enumerate(df_export.columns, 1):
                letra = worksheet.cell(row=1, column=col_num).column_letter
                worksheet.column_dimensions[letra].width = anchos.get(col, 18)

            worksheet.row_dimensions[1].height = 30
            for row_num in range(2, len(df_export) + 2):
                worksheet.row_dimensions[row_num].height = 35

        st.download_button(
            label="📥 Descargar Excel Profesional",
            data=output.getvalue(),
            file_name=f"RecruitAI_{puesto or 'candidatos'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
