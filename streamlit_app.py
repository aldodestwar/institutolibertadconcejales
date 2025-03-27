import streamlit as st
import google.generativeai as genai
import os
import time
import requests
from io import BytesIO
from pathlib import Path
from typing import List, Dict
import hashlib

# --- Password and Disclaimer State ---
if "authentication_successful" not in st.session_state:
    st.session_state.authentication_successful = False
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "password_input" not in st.session_state:
    st.session_state.password_input = "" # Initialize password input

# --- Initial Screen (Password and Disclaimer - Single Step) ---
if not st.session_state.disclaimer_accepted:
    initial_screen_placeholder = st.empty()
    with initial_screen_placeholder.container():
        st.title("Acceso al Asesor Legal Municipal IA")
        password = st.text_input("Ingrese la clave de usuario", type="password", value=st.session_state.password_input) # Persist input

        if st.button("Verificar Clave"): # Button for verification
            if password.lower() == "ilconcejales":
                st.session_state.authentication_successful = True
            else:
                st.session_state.authentication_successful = False
                st.error("Clave incorrecta. Intente nuevamente.")

        if st.session_state.authentication_successful: # Show disclaimer only after correct password
            st.markdown("---") # Separator
            with st.expander("Descargo de Responsabilidad (Leer antes de usar la IA)", expanded=False):
                st.markdown("""
                **Descargo de Responsabilidad Completo:**

                Este Asesor Legal Municipal IA es una herramienta de inteligencia artificial en fase de desarrollo beta. Como tal, es fundamental comprender y aceptar las siguientes condiciones antes de continuar:

                1.  **Naturaleza Beta y Posibles Errores:** La herramienta se encuentra en etapa de prueba y aprendizaje. Aunque se ha diseñado para proporcionar información útil y relevante sobre derecho municipal chileno, **puede cometer errores o entregar información incompleta o inexacta.** No debe considerarse infalible ni sustituir el juicio profesional de un abogado especializado.

                2.  **Uso Complementario, No Sustitutivo:**  Este Asesor Legal Virtual está concebido como una **herramienta complementaria a sus propios conocimientos y experiencia como concejal o alcalde.** Su propósito es brindar apoyo y orientación rápida, pero **nunca debe ser la base exclusiva para la toma de decisiones críticas o con consecuencias legales.**

                3.  **Limitación de Responsabilidad:** El **Instituto Libertad no asume ninguna responsabilidad por las decisiones o acciones que usted tome basándose en la información proporcionada por esta herramienta.**  El uso de este Asesor Legal Virtual es bajo su propia responsabilidad y criterio.

                4.  **Asesoría Profesional Especializada:**  Si requiere asesoramiento legal específico y detallado en derecho municipal, **le recomendamos encarecidamente contactar directamente al Instituto Libertad o consultar con un abogado especializado en derecho público y municipal.**  Esta herramienta no reemplaza la necesidad de una asesoría legal profesional cuando sea necesaria.

                5.  **Finalidad de Ayuda y Apoyo:**  Esta herramienta se ofrece como un **recurso de ayuda y apoyo para facilitar su labor en el ámbito municipal**, proporcionando acceso rápido a información y análisis preliminar.

                **En resumen, utilice esta herramienta con precaución, comprendiendo sus limitaciones y siempre validando la información con fuentes confiables y, cuando sea necesario, con asesoramiento legal profesional.**
                """)
            disclaimer_accepted = st.checkbox("Acepto los términos y condiciones y comprendo las limitaciones de esta herramienta.", key="disclaimer_checkbox")
            if disclaimer_accepted:
                st.session_state.disclaimer_accepted = True
                initial_screen_placeholder.empty() # Clear initial screen
                st.rerun() # Re-run to show main app

        st.session_state.password_input = password # Update password input for persistence
    st.stop() # Stop execution here if disclaimer not accepted

# --- Configuración de la página ---
st.set_page_config(
    page_title="Asesor Legal Municipal IA - Instituto Libertad",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Estilos CSS personalizados (INICIO - CSS MODIFICADO) ---
# (CSS styles remain unchanged from the previous version)
st.markdown(
    """
    <style>
    /* --- Variables de color --- */
    :root {
        --primary-color: #004488;
        --primary-hover-color: #005cb3;
        --secondary-bg: #f9f9f9;
        --text-color-primary: #444444;
        --text-color-secondary: #777777;
        --accent-color: #CC0000;
        --sidebar-bg: #f0f2f6;
        --sidebar-button-hover: #e0e0e0;
        --sidebar-text: #555555;
        --typing-dot-color: #aaaaaa; /* Color for typing dots */
    }

    body {
        background-color: var(--secondary-bg);
        color: var(--text-color-primary);
        font-family: sans-serif;
        overflow-y: scroll;
        opacity: 0;
        animation: fadeIn 0.5s ease-in-out forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    .main-title {
        font-size: 2.7em;
        font-weight: bold;
        margin-bottom: 0.1em;
        color: var(--primary-color);
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        transition: transform 0.3s ease-in-out;
    }
    .main-title:hover {
        transform: scale(1.02);
    }

    .subtitle {
        font-size: 1.2em;
        color: var(--text-color-secondary);
        margin-bottom: 1.2em;
        opacity: 0;
        animation: slideUp 0.6s ease-out forwards;
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 0.7; transform: translateY(0); }
    }

    .sidebar .sidebar-content {
        background-color: var(--sidebar-bg);
        padding: 1rem;
    }

    .stChatContainer {
        border-radius: 0.7em;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        transition: box-shadow 0.3s ease;
    }
    .stChatContainer:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.07);
    }

    /* --- Mensajes del Chat (Animación de entrada mejorada) --- */
    .chat-message {
        padding: 0.8em 1.2em;
        border-radius: 1em;
        margin-bottom: 1.2rem;
        font-size: 1rem;
        line-height: 1.5;
        width: fit-content;
        max-width: 80%;
        display: flex;
        flex-direction: column;
        transform: translateY(10px);
        opacity: 0;
        animation: fadeInUp 0.4s ease-out forwards; /* Slightly slower animation */
        overflow-wrap: break-word;
    }

    @keyframes fadeInUp {
        to { opacity: 1; transform: translateY(0); }
        from { opacity: 0; transform: translateY(10px); }
    }

    .user-message {
        background-color: #e6e6e6;
        color: var(--text-color-primary);
        align-self: flex-end;
        border-left: 4px solid var(--accent-color);
        box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
    }

    .assistant-message-container .stChatMessage { /* Target container for animation */
        align-self: flex-start;
        width: fit-content; /* Fit content */
        max-width: 80%; /* Max width */
        transform: translateY(10px);
        opacity: 0;
        animation: fadeInUp 0.4s ease-out forwards;
    }

    .assistant-message-container .stChatMessage > div:first-child { /* Inner content div */
        background-color: white; /* White for assistant messages */
        color: var(--text-color-primary);
        border-radius: 1em; /* Rounded corners */
        padding: 0.8em 1.2em; /* Padding */
        border-left: 4px solid #cccccc; /* Light gray border */
        box-shadow: 1px 1px 3px rgba(0,0,0,0.08);
        transition: box-shadow 0.3s ease;
        overflow-wrap: break-word; /* Ensure text wraps */
        word-wrap: break-word; /* Ensure text wraps */
        line-height: 1.5;
    }
    .assistant-message-container .stChatMessage:hover > div:first-child {
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }


    .message-content {
        word-wrap: break-word;
    }

    /* --- Campo de Entrada de Texto --- */
    .stTextInput > div > div > div > input {
        border: 1.5px solid #cccccc;
        border-radius: 0.5em;
        padding: 0.7em 1em;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput > div > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 5px rgba(0, 68, 136, 0.5); /* Use RGB of primary color */
        outline: none;
    }

    /* --- Botones --- */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 0.5em;
        padding: 0.7em 1.5em;
        font-weight: 500;
        text-transform: none;
        letter-spacing: 0.03em;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stButton > button:hover {
        background-color: var(--primary-hover-color);
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
    }
    .stButton > button:focus {
        outline: none;
        box-shadow: 0 0 0 2px rgba(0, 68, 136, 0.4); /* Use RGB of primary color */
    }
    /* Ripple effect (optional, kept from original) */
    .stButton > button::before {
        content: '';
        position: absolute;
        top: var(--mouse-y);
        left: var(--mouse-x);
        transform: translate(-50%, -50%);
        background: rgba(255, 255, 255, 0.2);
        width: 100%;
        height: 100%;
        border-radius: 50%;
        opacity: 0;
        transition: opacity 0.4s ease, width 0.6s ease, height: 0.6s ease;
    }
    .stButton > button:active::before {
        opacity: 1;
        width: 0%;
        height: 0%;
    }

    /* --- Contenedor del Logo en la Barra Lateral --- */
    .sidebar-logo-container {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        overflow: hidden;
        background-image: url('https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo');
        background-size: cover;
        background-position: center;
        margin-bottom: 1.2em;
        transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
    }
    .sidebar-logo-container:hover {
        transform: rotate(5deg) scale(1.05);
        border-radius: 50%;
    }

    .sidebar .st-bb {
        font-weight: bold;
        margin-bottom: 0.6em;
        color: var(--text-color-primary);
        border-bottom: 1px solid #dddddd;
        padding-bottom: 0.4em;
    }

    .sidebar .stButton > button {
        background-color: transparent;
        color: var(--text-color-primary);
        border-radius: 0.4em;
        padding: 0.4em 0.8em;
        font-size: 0.9em;
        font-weight: 400;
        box-shadow: none;
        transition: background-color 0.3s ease-in-out, transform 0.2s ease-out;
    }
    .sidebar .stButton > button:hover {
        background-color: var(--sidebar-button-hover);
        transform: translateX(1px);
    }
    .sidebar .stButton > button:focus {
        background-color: rgba(0, 68, 136, 0.1); /* Use RGB of primary color */
    }

    hr {
        border-top: 1px solid #dddddd;
        margin: 1em 0;
    }

    .sidebar a {
        color: var(--primary-color);
        text-decoration: none;
        transition: color 0.3s ease;
    }
    .sidebar a:hover {
        color: var(--primary-hover-color);
    }

    .sidebar .st-bb + div {
        margin-top: 0.6em;
        margin-bottom: 0.2em;
        font-size: 0.9em;
        color: var(--text-color-secondary);
    }

    .sidebar div[data-testid="stVerticalBlock"] > div > div {
        transition: background-color 0.2s ease-in-out;
        border-radius: 0.4em;
        padding: 0.1em 0;
        margin-bottom: 0.05em;
    }
    .sidebar div[data-testid="stVerticalBlock"] > div > div:hover {
        background-color: rgba(0, 0, 0, 0.03);
    }

    .sidebar .stButton > button:nth-child(3) {
        font-size: 0.7em;
        padding: 0.3em 0.6em;
        border-radius: 0.3em;
        background-color: rgba(0, 68, 136, 0.1); /* Use RGB of primary color */
        color: var(--primary-color);
    }
    .sidebar .stButton > button:nth-child(3):hover {
        background-color: rgba(0, 68, 136, 0.2); /* Use RGB of primary color */
    }

    .stApp .element-container:nth-child(3) div[data-testid="stImage"] > div > img {
        border-radius: 50%;
        max-width: 100% !important;
        height: auto !important;
    }

    .stChatMessage img {
        border-radius: 50%;
    }

    /* --- Typing Indicator Animation --- */
    .assistant-typing {
        display: flex;
        align-items: center;
        padding: 0.5em 0.8em; /* Reduced padding */
        margin-left: 2.5rem; /* Align with avatar */
        margin-bottom: 1.2rem; /* Match message margin */
    }
    .typing-dot {
        background-color: var(--typing-dot-color);
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin: 0 3px;
        animation: typing-bounce 1.4s infinite ease-in-out both;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }

    @keyframes typing-bounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1.0); }
    }

    </style>
    """,
    unsafe_allow_html=True,
)
# --- (FIN - CSS MODIFICADO) ---

# --- Disclaimer Status Display in Main Chat Area ---
if st.session_state.disclaimer_accepted:
    disclaimer_status_main_expander = st.expander("Disclaimer Aceptado - Clic para revisar o revocar", expanded=False)
    with disclaimer_status_main_expander:
        st.success("Disclaimer Aceptado. Puede usar el Asesor Legal Municipal IA.", icon="✅")
        st.markdown("""
                **Descargo de Responsabilidad Completo:**

                Este Asesor Legal Municipal IA es una herramienta de inteligencia artificial en fase de desarrollo beta. Como tal, es fundamental comprender y aceptar las siguientes condiciones antes de continuar:

                1.  **Naturaleza Beta y Posibles Errores:** La herramienta se encuentra en etapa de prueba y aprendizaje. Aunque se ha diseñado para proporcionar información útil y relevante sobre derecho municipal chileno, **puede cometer errores o entregar información incompleta o inexacta.** No debe considerarse infalible ni sustituir el juicio profesional de un abogado especializado.

                2.  **Uso Complementario, No Sustitutivo:**  Este Asesor Legal Virtual está concebido como una **herramienta complementaria a sus propios conocimientos y experiencia como concejal o alcalde.** Su propósito es brindar apoyo y orientación rápida, pero **nunca debe ser la base exclusiva para la toma de decisiones críticas o con consecuencias legales.**

                3.  **Limitación de Responsabilidad:** El **Instituto Libertad no asume ninguna responsabilidad por las decisiones o acciones que usted tome basándose en la información proporcionada por esta herramienta.**  El uso de este Asesor Legal Virtual es bajo su propia responsabilidad y criterio.

                4.  **Asesoría Profesional Especializada:**  Si requiere asesoramiento legal específico y detallado en derecho municipal, **le recomendamos encarecidamente contactar directamente al Instituto Libertad o consultar con un abogado especializado en derecho público y municipal.**  Esta herramienta no reemplaza la necesidad de una asesoría legal profesional cuando sea necesaria.

                5.  **Finalidad de Ayuda y Apoyo:**  Esta herramienta se ofrece como un **recurso de ayuda y apoyo para facilitar su labor en el ámbito municipal**, proporcionando acceso rápido a información y análisis preliminar.

                **En resumen, utilice esta herramienta con precaución, comprendiendo sus limitaciones y siempre validando la información con fuentes confiables y, cuando sea necesario, con asesoramiento legal profesional.**
                """)
        if st.button("Revocar Disclaimer", key="revocar_disclaimer_main"): # Unique key
            st.session_state.disclaimer_accepted = False
            st.rerun()

# --- Título principal y Subtítulo con Logo ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo", width=80)
with col_title:
    st.markdown('<h1 class="main-title">Asesor Legal Municipal IA</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Instituto Libertad</p>', unsafe_allow_html=True)

# --- API Key ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Adjusted model name based on availability

# --- Funciones para cargar y procesar archivos ---

# Usar ruta relativa para la carpeta de datos
script_dir = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd() # Handle interactive environments
DATABASE_DIR = os.path.join(script_dir, "data")

# Manual caching logic based on file modification times
def load_and_cache_database_files(directory: str) -> Dict[str, str]:
    """
    Loads content of all .txt files in the directory.
    Uses session_state for caching and reloads if files change (based on mtime).
    """
    current_signature = ""
    file_details = [] # Store (filename, mtime) tuples

    if not os.path.exists(directory):
        st.warning(f"Directorio de base de datos no encontrado: {directory}")
        return {} # Return empty if dir doesn't exist

    try:
        file_list = sorted([f for f in os.listdir(directory) if f.endswith(".txt")])
        for filename in file_list:
            filepath = os.path.join(directory, filename)
            mtime = os.path.getmtime(filepath)
            file_details.append((filename, mtime))

        # Create a signature based on filenames and modification times
        current_signature = hashlib.md5(str(file_details).encode()).hexdigest()

    except Exception as e:
        st.error(f"Error al verificar los archivos en '{directory}': {e}")
        # If we can't check files, assume cache is invalid
        current_signature = f"error_{time.time()}" # Unique signature on error

    # Check if signature matches and data exists in session state
    if ("database_signature" in st.session_state and
            st.session_state.database_signature == current_signature and
            "database_files" in st.session_state):
        return st.session_state.database_files # Return cached data

    # If signature mismatch or no data, reload
    st.session_state.database_files = {} # Reset cache
    loaded_files_count = 0
    for filename in file_list: # Use the list from earlier check
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                st.session_state.database_files[filename] = f.read()
                loaded_files_count += 1
        except Exception as e:
            st.error(f"Error al leer el archivo {filename}: {e}")

    st.session_state.database_signature = current_signature # Update signature
    # Optionally show a message on reload
    if loaded_files_count > 0:
        pass # Avoid showing toast too often
    return st.session_state.database_files

# --- Helper functions ---
def load_file_content(uploaded_file) -> str:
    """Loads the content of an uploaded file (.txt)."""
    try:
        if uploaded_file.name.lower().endswith(".txt"):
            stringio = BytesIO(uploaded_file.getvalue())
            string_data = stringio.read().decode('utf-8', errors='replace')
            return string_data
        else:
            st.error(f"Tipo de archivo no soportado: {uploaded_file.name}")
            return ""
    except Exception as e:
        st.error(f"Error al leer el archivo adjunto {uploaded_file.name}: {e}")
        return ""

def get_file_description(filename: str) -> str:
    """Genera una descripción genérica para un archivo basado en su nombre."""
    name_parts = filename.replace(".txt", "").split("_")
    return " ".join(word.capitalize() for word in name_parts)

# --- Prompt Modificado ---
def create_prompt(database_files_content: Dict[str, str], uploaded_data: str, query: str) -> str:
    """Crea el prompt para el modelo, incluyendo información de la base de datos y archivos adjuntos, con reglas estrictas sobre el Manual de Concejales."""
    prompt_parts = [
        "Eres un asesor legal virtual altamente especializado en **derecho municipal de Chile**, con un enfoque particular en asistir a alcaldes y concejales. Tu experiencia abarca una amplia gama de temas relacionados con la administración y normativa municipal chilena.",
        "Tu objetivo principal es **responder directamente a las preguntas del usuario de manera precisa y concisa**, siempre **citando la fuente legal o normativa** que respalda tu respuesta. **Prioriza el uso de un lenguaje claro y accesible, evitando jerga legal compleja, para que la información sea fácilmente comprensible para concejales y alcaldes, incluso si no tienen formación legal.**",
        "**MANUAL DE CONCEJALES Y CONCEJALAS (USO EXCLUSIVO COMO CONTEXTO GENERAL Y CONOCIMIENTO BASE - PROHIBIDO CITARLO):**",
        "Se te proporciona un documento extenso llamado 'MANUAL DE CONCEJALES Y CONCEJALAS - 2025 ACHM'. **Utiliza este documento ÚNICAMENTE como contexto general y para integrar su contenido a tu conocimiento base sobre el marco del derecho municipal chileno y las funciones de los concejales.** Considera la información de este manual como parte de tu 'entrenamiento' o 'conocimiento general'.",
        "**REGLA ABSOLUTA: ESTÁ ESTRICTAMENTE PROHIBIDO CITAR este manual en tus respuestas. NO DEBES MENCIONAR su nombre ('MANUAL DE CONCEJALES Y CONCEJALAS - 2025 ACHM') ni hacer referencia explícita a ninguna de sus partes o puntos. Cuando uses el conocimiento derivado de este manual, debes presentarlo como parte de tu conocimiento general de derecho municipal chileno y citar la ley o norma general pertinente (ej. Ley Orgánica Constitucional de Municipalidades), NUNCA el manual.**",
        "**INFORMACIÓN DE LA BASE DE DATOS (NORMAS LEGALES ESPECÍFICAS):**"
    ]

    # Include the content of the manual if it exists, clearly labeling it for context only
    manual_filename = "MANUAL DE CONCEJALES Y CONCEJALAS - 2025 ACHM.txt"
    manual_content = database_files_content.get(manual_filename, "")
    if manual_content:
        prompt_parts.insert(5, f"\n**Contenido del Manual (SOLO PARA TU CONTEXTO INTERNO Y CONOCIMIENTO BASE, NO CITAR NI MENCIONAR):**\n{manual_content}\n---") # Insert manual content after strict rule

    # Include content from other database files (excluding the manual)
    if database_files_content:
        prompt_parts.append("\n**Documentos Específicos de la Base de Datos (Puedes citar estos por nombre y artículo/sección):**")
        found_other_db_files = False
        for filename, content in database_files_content.items():
            # Skip the manual here as it's handled separately and forbidden to cite
            if filename == manual_filename:
                continue
            found_other_db_files = True
            description = get_file_description(filename)
            prompt_parts.append(f"\n**{description} ({filename.replace('.txt', '')}):**\n{content}\n")
        if not found_other_db_files:
            prompt_parts.append("No se encontraron otros documentos específicos en la base de datos.\n")

    else:
        prompt_parts.append("No se ha cargado información de la base de datos de normas legales.\n")

    # Include uploaded data
    prompt_parts.append("**INFORMACIÓN ADICIONAL PROPORCIONADA POR EL USUARIO (Puedes citar estos archivos por nombre):**")
    prompt_parts.append(uploaded_data if uploaded_data else "No se proporcionó información adicional.\n")

    prompt_parts.extend([
        "**IMPORTANTE:** Antes de responder, analiza cuidadosamente la pregunta del usuario para determinar si se relaciona específicamente con:",
        "    a) **Documentos específicos de la base de datos** (excluyendo el manual prohibido).",
        "    b) **Información adicional proporcionada por el usuario**.",
        "    c) **Derecho municipal general** (donde usarás tu conocimiento base, incluyendo el contexto del manual prohibido, pero citando la ley general).",

        """
*   **Si la pregunta se relaciona con Documentos Específicos de la Base de Datos (excluyendo el manual):** Utiliza la información de esos documentos como tu principal fuente. **Siempre cita el nombre del documento específico de la base de datos y el artículo, sección o norma pertinente que justifica tu respuesta (ej. "Artículo 25 del Reglamento del Concejo Municipal").** Indica claramente en tu respuesta que estás utilizando información de ese documento específico.
*   **Si la pregunta se relaciona con la información adicional proporcionada por el usuario:** Utiliza esa información como tu principal fuente. **Siempre cita la parte específica de la información adicional que justifica tu respuesta, mencionando el nombre del archivo adjunto (ej. "Según la jurisprudencia adjunta en el archivo 'Sentencia_Rol_1234-2023.txt'").** Indica claramente en tu respuesta que estás utilizando información proporcionada por el usuario y el documento específico.
*   **Si la pregunta es sobre otros aspectos del derecho municipal chileno:** Utiliza tu conocimiento general en la materia, basado en tu entrenamiento legal **(el cual incluye la comprensión del contexto proporcionado por el manual prohibido, pero SIN mencionarlo)**. **Siempre cita la norma legal general del derecho municipal chileno que justifica tu respuesta (ej. "Según el artículo 65 de la Ley Orgánica Constitucional de Municipalidades").** Indica claramente en tu respuesta que estás utilizando tu conocimiento general de derecho municipal chileno y la norma general. **NUNCA digas 'Según el manual...' o algo similar.**
        """,
        "Esta es una herramienta creada por y para el Instituto Libertad por Aldo Manuel Herrera Hernández.",
        "**Metodología LegalDesign:**",
        """
*   **Claridad y Concisión:** Responde de manera directa y al grano. Evita rodeos innecesarios.
*   **Estructura:** Organiza las respuestas con encabezados, viñetas o listas numeradas.
*   **Lenguaje sencillo:** Usa lenguaje accesible, manteniendo precisión legal.
        """,
        "**Instrucciones específicas:**",
        """
*   Comienza tus respuestas con un **breve resumen conciso en una frase inicial.**
*   Luego, **desarrolla la respuesta completa y detallada**, proporcionando análisis legal y **citando SIEMPRE la fuente normativa específica APROPIADA (ley general, documento específico de la base de datos (NO EL MANUAL), o archivo adjunto).**
*   **RECUERDA LA REGLA ABSOLUTA: NUNCA CITAR NI MENCIONAR EL 'MANUAL DE CONCEJALES Y CONCEJALAS - 2025 ACHM'. Trata su contenido como conocimiento base y cita la ley general correspondiente cuando uses esa información.**
*   **Si la pregunta se relaciona con el funcionamiento interno del Concejo (sesiones, tablas, reglamento, etc.):** Indica que las reglas específicas varían y se encuentran en el Reglamento Interno de cada municipalidad. Basa tu respuesta en tu conocimiento general (leyes generales, contexto del manual prohibido), pero **advierte SIEMPRE sobre la necesidad de consultar el Reglamento Interno específico.** Cita la ley general aplicable (ej. LOCM), no el manual.
*   **Manejo de Información Faltante:**
    *   Si la información NO está en los **documentos específicos de la base de datos (excluyendo el manual)**: "Según los documentos específicos disponibles en la base de datos, no puedo responder a esta pregunta."
    *   Si la información NO está en la **información adicional proporcionada**: "Según la información adicional proporcionada, no puedo responder a esta pregunta."
    *   Si la información NO está en tu **conocimiento general de derecho municipal chileno (incluyendo el contexto del manual prohibido)**: "Según mi conocimiento general de derecho municipal chileno, no puedo responder a esta pregunta."
*   **REITERACIÓN CRÍTICA: SIEMPRE CITA LA FUENTE NORMATIVA ADECUADA. NUNCA, BAJO NINGUNA CIRCUNSTANCIA, MENCIONES O CITES DIRECTAMENTE EL MANUAL DE CONCEJALES.**
        """,
        "**Ejemplos de respuestas esperadas (con resumen y citación - SIN CITAR EL MANUAL, usando conocimiento base para citar leyes generales o documentos específicos):**",
        """
*   **Pregunta del Usuario:** "¿Cuáles son las funciones del concejo municipal?"
    *   **Respuesta Esperada:** "Resumen: Las funciones principales del concejo municipal son normativas, fiscalizadoras y resolutivas.
        Desarrollo: Efectivamente, el concejo municipal tiene asignadas funciones de carácter normativo, fiscalizador y resolutivo, entre otras. Estas se encuentran detalladas principalmente en la Ley Orgánica Constitucional de Municipalidades (Por ejemplo, ver artículo 79 de la Ley N° 18.695, Orgánica Constitucional de Municipalidades)." *(Nota: Aquí usaste tu conocimiento base, informado por el manual, para encontrar y citar la LOCM)*.
*   **Pregunta del Usuario:** "¿Qué dice el artículo 25 sobre las citaciones a las sesiones en el Reglamento del Concejo Municipal?"
    *   **Respuesta Esperada:** "Resumen: El artículo 25 del Reglamento del Concejo Municipal establece los plazos y formalidades para las citaciones a sesiones.
        Desarrollo: Así es, consultando la base de datos, el artículo 25 del documento 'Reglamento del Concejo Municipal' detalla los plazos y formalidades que deben seguirse al realizar citaciones tanto para sesiones ordinarias como extraordinarias (Artículo 25 del Reglamento del Concejo Municipal)." *(Nota: Cita directa del documento específico permitido)*.
*   **Pregunta del Usuario:** (Adjunta un archivo con jurisprudencia sobre transparencia municipal) "¿Cómo se aplica esta jurisprudencia en el concejo?"
    *   **Respuesta Esperada:** "Resumen: La jurisprudencia adjunta establece criterios sobre publicidad y acceso a la información, relevantes para la transparencia del concejo.
        Desarrollo: Correcto, la jurisprudencia que adjuntas en el archivo 'Sentencia_Rol_1234-2023.txt' define criterios importantes sobre la publicidad de las actuaciones del concejo y el acceso a la información pública municipal. Estos criterios deben ser considerados para asegurar la transparencia (Según la jurisprudencia adjunta en el archivo 'Sentencia_Rol_1234-2023.txt')." *(Nota: Cita directa del archivo adjunto)*.
*   **Pregunta del Usuario:** "¿Cómo se define la tabla de una sesión del concejo municipal?"
    *   **Respuesta Esperada:** "Resumen: La tabla de una sesión es el listado de materias a tratar, generalmente fijada por el alcalde según las normas del reglamento interno.
        Desarrollo: La definición y procedimiento exacto para la tabla de sesiones se encuentran regulados en el Reglamento Interno de cada Concejo Municipal, por lo que los detalles pueden variar entre municipalidades. Basándome en mi conocimiento general del derecho municipal chileno, la tabla es el listado de temas a tratar en una sesión, cuya fijación suele corresponder al alcalde, siguiendo las pautas de la ley y el reglamento. La Ley Orgánica de Municipalidades establece principios generales sobre las sesiones (Ver artículos 81 y siguientes de la Ley N° 18.695). **Es fundamental verificar el Reglamento Interno específico de tu municipalidad para conocer las reglas precisas.**" *(Nota: Usa conocimiento general, cita la LOCM, advierte sobre el reglamento interno, NO cita el manual)*.
        """,
        "**Historial de conversación:**"
    ])

    # Añadir historial de conversación
    for msg in st.session_state.messages[:-1]: # Exclude the latest user message which is the current query
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        prompt_parts.append(f"{role}: {msg['content']}\n")

    prompt_parts.append(f"**Pregunta actual del usuario:** {query}")

    return "\n".join(prompt_parts)
# --- (FIN - Prompt Modificado) ---


# --- Inicializar el estado para los archivos ---
if "database_files" not in st.session_state:
    st.session_state.database_files = {}
if "database_signature" not in st.session_state:
    st.session_state.database_signature = None
if "uploaded_files_content" not in st.session_state:
    st.session_state.uploaded_files_content = ""

# --- Carga inicial de archivos ---
def load_database_files_on_startup():
    """Carga/verifica los archivos de la base de datos al inicio."""
    files_data = load_and_cache_database_files(DATABASE_DIR)
    st.session_state.database_files = files_data
    # Count files excluding the manual if present
    manual_filename = "MANUAL DE CONCEJALES Y CONCEJALAS - 2025 ACHM.txt"
    db_file_count = len([f for f in files_data if f != manual_filename])
    context_file_present = 1 if manual_filename in files_data else 0
    return db_file_count, context_file_present

# Call the loading function
database_files_loaded_count, context_file_loaded = load_database_files_on_startup()


# --- Inicializar el estado de la sesión ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Modified initial message slightly to reflect the tool's nature
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! Soy tu asesor legal IA del Instituto Libertad, especializado en derecho municipal chileno. Mi objetivo es asistirte con información basada en normativas y documentos proporcionados, usando mi conocimiento general para contextualizar. Recuerda que soy una herramienta de apoyo y no reemplazo a un abogado. ¿En qué puedo ayudarte hoy?"})

if "saved_conversations" not in st.session_state:
    st.session_state.saved_conversations = {}

if "current_conversation_name" not in st.session_state:
    st.session_state.current_conversation_name = "Nueva Conversación"

# --- Funciones de conversación (unchanged) ---
def save_conversation(name, messages, pinned=False):
    st.session_state.saved_conversations[name] = {"messages": messages, "pinned": pinned}

def delete_conversation(name):
    if name in st.session_state.saved_conversations:
        del st.session_state.saved_conversations[name]

def load_conversation(name):
    if name in st.session_state.saved_conversations:
        st.session_state.messages = st.session_state.saved_conversations[name]["messages"]
        st.session_state.current_conversation_name = name

def pin_conversation(name):
    if name in st.session_state.saved_conversations:
        st.session_state.saved_conversations[name]["pinned"] = True

def unpin_conversation(name):
    if name in st.session_state.saved_conversations:
        st.session_state.saved_conversations[name]["pinned"] = False


# --- Barra lateral (INICIO - MODIFICADO File Uploader and Status) ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo-container"></div>', unsafe_allow_html=True)
    st.header("Gestión y Contexto")

    # --- Disclaimer Status ---
    disclaimer_status_expander = st.expander("Estado del Disclaimer", expanded=True)
    with disclaimer_status_expander:
        if st.session_state.disclaimer_accepted:
            st.success("Disclaimer Aceptado", icon="✅")
            if st.button("Revocar Disclaimer"):
                st.session_state.disclaimer_accepted = False
                st.rerun()
        else:
            st.warning("Disclaimer No Aceptado", icon="⚠️")
            st.markdown("Acepta el Disclaimer para usar el Asesor.")

    # --- Database Status ---
    db_status_expander = st.expander("Estado Base de Datos", expanded=True)
    with db_status_expander:
        # Display status based on the counts returned by the loading function
        if database_files_loaded_count > 0:
            st.success(f"Base de Datos ({database_files_loaded_count} archivos específicos) cargada.", icon="📚")
        else:
            st.warning("Archivos específicos de Base de Datos no cargados o vacíos.", icon="⚠️")

        if context_file_loaded > 0:
            st.info("Archivo de contexto general (Manual) cargado.", icon="🧠")
        else:
             st.warning("Archivo de contexto general (Manual) no encontrado.", icon="⚠️")

        st.caption(f"Buscando en: `{DATABASE_DIR}`")

        # Add a button to manually trigger a refresh check
        if st.button("Refrescar Base de Datos", key="refresh_db"):
            load_database_files_on_startup() # Re-run the loading/checking function
            st.rerun() # Rerun the app to reflect potential changes

    # --- File Uploader ---
    upload_expander = st.expander("Cargar Datos Adicionales", expanded=False)
    with upload_expander:
        uploaded_files = st.file_uploader(
            "Adjuntar archivos .txt",
            type=["txt"],
            help="Adjunta archivos .txt con información adicional (jurisprudencia, dictámenes, etc.).",
            accept_multiple_files=True,
            key="file_uploader" # Add a key for stability
        )
        if uploaded_files:
            st.session_state.uploaded_files_content = ""
            loaded_count = 0
            st.markdown("**Archivos adjuntados:**")
            for uploaded_file in uploaded_files:
                try:
                    content = load_file_content(uploaded_file)
                    if content:
                        st.session_state.uploaded_files_content += f"--- INICIO ARCHIVO: {uploaded_file.name} ---\n{content}\n--- FIN ARCHIVO: {uploaded_file.name} ---\n\n"
                        st.success(f"`{uploaded_file.name}` ✓", icon="📄")
                        loaded_count += 1
                    else:
                         st.error(f"`{uploaded_file.name}` ✗ (Error lectura)", icon="⚠️")
                except Exception as e:
                    st.error(f"Error procesando {uploaded_file.name}: {e}")
            if loaded_count > 0:
                 st.caption(f"{loaded_count} archivo(s) procesado(s).")

        if st.session_state.uploaded_files_content:
             if st.button("Limpiar archivos adjuntos", key="clear_uploads"):
                st.session_state.uploaded_files_content = ""
                st.rerun()

    st.markdown("---")
    st.header("Historial de Conversaciones")

    new_conversation_name = st.text_input("Título conversación:", value=st.session_state.current_conversation_name)
    if new_conversation_name != st.session_state.current_conversation_name:
        st.session_state.current_conversation_name = new_conversation_name

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Guardar", help="Guardar la conversación actual"):
            # Limit saved conversations logic (unchanged)
            if len(st.session_state.saved_conversations) >= 5:
                unpinned_conversations = [name for name, data in st.session_state.saved_conversations.items() if not data.get('pinned', False)]
                if unpinned_conversations:
                    oldest_unpinned = unpinned_conversations[0] # Simplistic removal
                    delete_conversation(oldest_unpinned)
                    st.toast(f"Límite alcanzado. Se eliminó '{oldest_unpinned}'.", icon="🗑️")

            messages_to_save = list(st.session_state.messages)
            save_conversation(st.session_state.current_conversation_name, messages_to_save, st.session_state.saved_conversations.get(st.session_state.current_conversation_name, {}).get('pinned', False))
            st.success("Conversación guardada!", icon="💾")
            time.sleep(1)
            st.rerun()

    with col2:
        if st.button("Borrar Chat", key="clear_chat_sidebar", help="Limpiar la conversación actual"):
            if st.session_state.messages:
                 initial_message = st.session_state.messages[0]
                 st.session_state.messages = [initial_message]
            else: # Re-initialize if empty
                 st.session_state.messages = [{"role": "assistant", "content": "¡Hola! Soy tu asesor legal IA del Instituto Libertad..."}]
            st.session_state.current_conversation_name = "Nueva Conversación"
            st.rerun()

    with col3:
        is_pinned = st.session_state.saved_conversations.get(st.session_state.current_conversation_name, {}).get('pinned', False)
        pin_icon = "📌" if is_pinned else "➖"
        pin_tooltip = "Desfijar conversación" if is_pinned else "Fijar conversación"
        if st.button(pin_icon, key="pin_button", help=pin_tooltip):
            if st.session_state.current_conversation_name in st.session_state.saved_conversations:
                if is_pinned:
                    unpin_conversation(st.session_state.current_conversation_name)
                    st.toast("Conversación desfijada.", icon=pin_icon)
                else:
                    pin_conversation(st.session_state.current_conversation_name)
                    st.toast("Conversación fijada.", icon="📌")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Guarda la conversación antes de fijarla.")

    st.subheader("Conversaciones Guardadas")
    sorted_conversations = sorted(
        st.session_state.saved_conversations.items(),
        key=lambda item: (not item[1].get('pinned', False), item[0])
    )

    if not sorted_conversations:
        st.caption("No hay conversaciones guardadas.")

    for name, data in sorted_conversations:
        pinned_icon = "📌" if data.get('pinned', False) else ""
        cols = st.columns([0.75, 0.25])
        with cols[0]:
            if st.button(f"{pinned_icon} {name}", key=f"load_{name}", help=f"Cargar '{name}'"):
                load_conversation(name)
                st.rerun()
        with cols[1]:
            if st.button("🗑️", key=f"delete_{name}", help=f"Eliminar '{name}'"):
                delete_conversation(name)
                if st.session_state.current_conversation_name == name:
                    st.session_state.current_conversation_name = "Nueva Conversación"
                    if st.session_state.messages:
                         st.session_state.messages = [st.session_state.messages[0]]
                st.rerun()

    st.markdown("---")
    st.header("Acerca de")
    st.markdown("Este asesor legal virtual fue creado por Aldo Manuel Herrera Hernández para el **Instituto Libertad** y se especializa en asesoramiento en derecho administrativo y municipal de **Chile**.")
    st.markdown("Se basa en la información de la base de datos (excluyendo el manual para citas directas), archivos adjuntos y su conocimiento general entrenado.")
    st.markdown("La información proporcionada aquí NO reemplaza el asesoramiento legal profesional.")
    st.markdown("---")
    st.markdown("**Instituto Libertad**")
    st.markdown("[Sitio Web](https://www.institutolibertad.cl)")
    st.markdown("[Contacto](mailto:contacto@institutolibertad.cl)")

    # Updated Data Summary
    st.subheader("Resumen Datos Cargados")
    if database_files_loaded_count > 0 :
        st.markdown(f"**Base de Datos Específica:** {database_files_loaded_count} archivo(s) OK.")
    else:
         st.markdown("**Base de Datos Específica:** No cargada.")

    if context_file_loaded > 0:
        st.markdown("**Contexto General (Manual):** 1 archivo OK (no citable).")
    else:
        st.markdown("**Contexto General (Manual):** No cargado.")


    if st.session_state.uploaded_files_content:
        uploaded_file_count = st.session_state.uploaded_files_content.count("--- INICIO ARCHIVO:")
        st.markdown(f"**Archivos Adicionales:** {uploaded_file_count} archivo(s) OK.")
    else:
        st.markdown("**Archivos Adicionales:** Ninguno.")

# --- (FIN - Barra lateral Modificada) ---


# --- Área de chat (MODIFICADO para streaming y animación) ---
if st.session_state.disclaimer_accepted:
    # Display existing messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><div class="message-content">{message["content"]}</div></div>', unsafe_allow_html=True)
        else: # Assistant
             # Use markdown within st.chat_message for better control and avatar
            with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
                # Wrap the content in the styled div for consistency, animation applies to container
                st.markdown(f'<div class="message-content">{message["content"]}</div>', unsafe_allow_html=True)


    # --- Input field ---
    if prompt := st.chat_input("Escribe tu consulta...", key="chat_input"):
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message immediately with animation
        st.markdown(f'<div class="chat-message user-message"><div class="message-content">{prompt}</div></div>', unsafe_allow_html=True)

        # --- Generate and display assistant response ---
        # Use a container for the typing indicator and the final response
        response_area = st.container() # Container to hold typing and response
        with response_area:
            # 1. Display Typing Indicator within chat_message structure
            typing_placeholder = st.empty()
            with typing_placeholder.container():
                 with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
                     st.markdown('<div class="assistant-typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>', unsafe_allow_html=True)


            # 2. Prepare and Send Prompt
            current_db_files = load_and_cache_database_files(DATABASE_DIR) # Ensure current data
            prompt_completo = create_prompt(
                current_db_files,
                st.session_state.uploaded_files_content,
                prompt
            )

            # 3. Stream Response
            full_response = ""
            # Placeholder for the streaming response content *within* a chat_message
            stream_placeholder = st.empty()

            try:
                # Start generation stream
                response_stream = model.generate_content(prompt_completo, stream=True)

                # Iterate through chunks and update placeholder
                for chunk in response_stream:
                    # Handle potential empty chunks or safety blocks
                    try:
                        chunk_text = chunk.text
                        full_response += chunk_text
                        # Display intermediate response within the assistant message structure
                        with stream_placeholder.container():
                             with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
                                st.markdown(f'<div class="message-content">{full_response}▌</div>', unsafe_allow_html=True) # Blinking cursor
                        time.sleep(0.01) # Small delay for visual streaming effect

                    except (ValueError, AttributeError) as e:
                         # Handle cases where chunk.text might be inaccessible (e.g., safety filters)
                         # Log the issue if needed: print(f"Skipping chunk due to error: {e}, Chunk: {chunk}")
                         pass # Continue to the next chunk


                # Check for empty response *after* iterating through the stream
                if not full_response.strip():
                     # Handle case where the stream completed but produced no usable text
                    error_message = """
                    Lo siento, no pude generar una respuesta adecuada. Esto podría deberse a filtros de seguridad o a la naturaleza de la pregunta.

                    **Intenta:**
                    * Reformular tu pregunta.
                    * Asegurarte de que la pregunta sea clara y específica.
                    """
                    full_response = error_message
                    # Display error message in the final spot
                    with stream_placeholder.container():
                        with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
                            st.error(f'<div class="message-content">{full_response}</div>', icon="⚠️") # Use st.error for visual distinction

            except Exception as e:
                st.error(f"Ocurrió un error al contactar la IA: {e}", icon="🚨")
                full_response = f"Error: No se pudo obtener respuesta. ({e})"
                # Display error message in the final spot
                with stream_placeholder.container():
                    with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
                        st.error(f'<div class="message-content">{full_response}</div>', icon="🚨")

            finally:
                 # 4. Clear Typing Indicator
                typing_placeholder.empty()

                # 5. Finalize Response Display (remove cursor, ensure container shows final state)
                # This replaces the streaming content with the final, static message.
                with stream_placeholder.container():
                    with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
                        st.markdown(f'<div class="message-content">{full_response}</div>', unsafe_allow_html=True) # Final content

                # 6. Add final response to session state only if it's not just an error placeholder
                if full_response and not full_response.startswith("Error:"):
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                # If it was an error generated by our code (not the model), don't save it as a valid assistant turn.

else: # Disclaimer not accepted
    st.warning("Para usar el Asesor Legal Municipal IA, debes aceptar el Disclaimer (ver barra lateral o mensaje inicial).", icon="⚠️")
# --- (FIN - Área de Chat Modificada) ---