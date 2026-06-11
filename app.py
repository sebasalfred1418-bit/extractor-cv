import streamlit as st
import anthropic
import pandas as pd
from pypdf import PdfReader
import io
import json

st.set_page_config(page_title="Extractor de CVs", page_icon="📄", layout="wide")

try:
    api_key_segura = st.secrets["CLAUDE_API_KEY"]
except Exception:
    st.error("⚠️ Error: No se encontró la API Key en los Secrets de Streamlit Cloud.")
    st.stop()

st.title("📄 Extractor Automatizado de Currículums")
st.subheader("Sube los CVs en PDF y descarga el Excel")

client = anthropic.Anthropic(api_key=api_key_segura)

uploaded_files = st.file_uploader("Suelte aquí los archivos PDF de los CVs", type=["pdf"], accept_multiple_files=True)

if uploaded_files and st.button("Procesar Currículums 🚀"):
    resultados = []
    progress_bar = st.progress(0)

    for index, file in enumerate(uploaded_files):
        st.write(f"Analizando: {file.name}...")
        try:
            pdf_reader = PdfReader(file)
            texto_cv = ""
            for page in pdf_reader.pages:
                texto_cv += page.extract_text()
        except Exception as e:
            st.error(f"Error al leer el archivo {file.name}: {e}")
            continue

        prompt = f"""Actúa como un reclutador experto. Analiza el siguiente CV y extrae la información. 
Responde EXCLUSIVAMENTE con un objeto JSON válido, sin texto adicional ni markdown.

Formato JSON requerido:
{{
  "Nombre": "",
  "Correo": "",
  "Telefono": "",
  "Educacion_Maxima": "",
  "Universidad": "",
  "Ultimo_Cargo": "",
  "Ultima_Empresa": "",
  "Experiencia_Anos": "",
  "Habilidades_Tecnicas": "",
  "Habilidades_Blandas": "",
  "Idiomas": "",
  "Certificaciones": ""
}}

Instrucciones:
- Habilidades_Tecnicas: solo software, herramientas y conocimientos técnicos (máximo 5, separados por coma)
- Habilidades_Blandas: solo habilidades interpersonales (máximo 4, separados por coma)
- Experiencia_Anos: solo el número
- Si un dato no existe escribe: No especifica

Texto del CV:
{texto_cv}"""

        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            respuesta_texto = message.content[0].text
            respuesta_texto = respuesta_texto.strip()
            if "```" in respuesta_texto:
                respuesta_texto = respuesta_texto.split("```")[1]
                if respuesta_texto.startswith("json"):
                    respuesta_texto = respuesta_texto[4:]
            inicio = respuesta_texto.find("{")
            fin = respuesta_texto.rfind("}") + 1
            respuesta_texto = respuesta_texto[inicio:fin]
            datos_candidato = json.loads(respuesta_texto)
            resultados.append(datos_candidato)
        except Exception as e:
            st.error(f"Error procesando {file.name}: {e}")

        progress_bar.progress((index + 1) / len(uploaded_files))

    if resultados:
        df = pd.DataFrame(resultados)
        st.success(f"✅ ¡Completado! {len(resultados)} CVs procesados.")
        st.dataframe(df, use_container_width=True)

        # Generar Excel con formato profesional
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Candidatos')

            workbook = writer.book
            worksheet = writer.sheets['Candidatos']

            from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

            # Colores
            color_encabezado = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            color_fila_par = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
            borde = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # Formato encabezados
            for col_num, col in enumerate(df.columns, 1):
                cell = worksheet.cell(row=1, column=col_num)
                cell.font = Font(bold=True, color="FFFFFF", size=11)
                cell.fill = color_encabezado
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = borde

            # Formato filas de datos
            for row_num in range(2, len(df) + 2):
                for col_num in range(1, len(df.columns) + 1):
                    cell = worksheet.cell(row=row_num, column=col_num)
                    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                    cell.border = borde
                    if row_num % 2 == 0:
                        cell.fill = color_fila_par

            # Ancho de columnas
            anchos = {
                "Nombre": 20, "Correo": 28, "Telefono": 15,
                "Educacion_Maxima": 25, "Universidad": 25,
                "Ultimo_Cargo": 25, "Ultima_Empresa": 22,
                "Experiencia_Anos": 12, "Habilidades_Tecnicas": 30,
                "Habilidades_Blandas": 28, "Idiomas": 15, "Certificaciones": 25
            }
            for col_num, col in enumerate(df.columns, 1):
                letra = worksheet.cell(row=1, column=col_num).column_letter
                worksheet.column_dimensions[letra].width = anchos.get(col, 20)

            # Alto de filas
            worksheet.row_dimensions[1].height = 30
            for row_num in range(2, len(df) + 2):
                worksheet.row_dimensions[row_num].height = 40

        data_excel = output.getvalue()
        st.download_button(
            label="📥 Descargar Base de Datos en Excel",
            data=data_excel,
            file_name="Base_de_Datos_Candidatos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
