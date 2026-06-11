import streamlit as st
import anthropic
import pandas as pd
from pypdf import PdfReader
import io
import json

# 1. Configuración de la página (¡Siempre primero!)
st.set_page_config(page_title="Extractor de CVs", page_icon="📄", layout="wide")

# 2. Conexión segura con tu API Key oculta en los Secrets
try:
    api_key_segura = st.secrets["CLAUDE_API_KEY"]
except Exception:
    st.error("⚠️ Error: No se encontró la API Key en los Secrets de Streamlit Cloud.")
    st.stop()

# 3. Interfaz limpia y directa
st.title("📄 Extractor Automatizado de Currículums")
st.subheader("Sube los CVs en PDF y descarga el Excel")

# Iniciamos el cliente de Anthropic con la llave segura
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
            
        prompt = f"Actúa como un reclutador experto. Analiza el siguiente texto de un CV y extrae la información requerida. Debes responder EXCLUSIVAMENTE con un objeto JSON válido, sin textos introductorios ni formato markdown. Si un dato no existe, coloca 'No especifica'.\n\nFormato JSON requerido:\n{{\"Nombre\": \"\", \"Correo\": \"\", \"Telefono\": \"\", \"Educacion_Maxima\": \"\", \"Ultimo_Cargo\": \"\", \"Experiencia_Anos\": \"\", \"Habilidades\": \"\"}}\n\nTexto del CV:\n{texto_cv}"
        
        try:
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            datos_candidato = json.loads(message.content[0].text)
            resultados.append(datos_candidato)
        except Exception as e:
            st.error(f"Error procesando {file.name}: {e}")
        
        progress_bar.progress((index + 1) / len(uploaded_files))
        
    if resultados:
        df = pd.DataFrame(resultados)
        st.success("¡Completado!")
        st.dataframe(df)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Candidatos')
        data_excel = output.getvalue()
        st.download_button(
            label="📥 Descargar Base de Datos en Excel", 
            data=data_excel, 
            file_name="Base_de_Datos_Candidatos.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
