import streamlit as st
import google.generativeai as genai
import os
import time
import requests
from io import BytesIO
from pathlib import Path
from typing import List, Dict
import hashlib
import random # Import random module

# --- Disclaimer State ---
# Removed password-related session state initialization
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = "" # Initialize custom API key state

# --- Initial Screen (Disclaimer Only) ---
if not st.session_state.disclaimer_accepted:
    initial_screen_placeholder = st.empty()
    with initial_screen_placeholder.container():
        st.title("Acceso al Asesor Legal Municipal IA")
        st.markdown("---") # Separator

        # Disclaimer is now shown directly, not dependent on password
        with st.expander("Descargo de Responsabilidad (Leer antes de usar la IA)", expanded=True): # Expanded by default
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

    st.stop() # Stop execution here if disclaimer not accepted

# --- Configuración de la página ---
st.set_page_config(
    page_title="Asesor Legal Municipal IA - Instituto Libertad",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed" # Changed to "collapsed"
)

# --- Estilos CSS personalizados ---
st.markdown(
    """
    <style>
    /* --- Variables de color para fácil modificación --- */
    :root {
        --primary-color: #004488; /* Dark Blue -  MATCHING WEBSITE HEADER BLUE */
        --primary-hover-color: #005cb3; /* Lighter Blue for hover */
        --secondary-bg: #f9f9f9; /* Very light gray - Website background feel */
        --text-color-primary: #444444; /* Slightly lighter Dark Gray - Body text */
        --text-color-secondary: #777777; /* Medium Gray - Secondary text */
        --accent-color: #CC0000; /* Red Accent - Similar to website red */
        --sidebar-bg: #f0f2f6; /* Light gray for sidebar background */
        --sidebar-button-hover: #e0e0e0; /* Lighter gray for sidebar button hover */
        --sidebar-text: #555555; /* Slightly lighter Sidebar text color - Dark gray */
    }

    body {
        background-color: var(--secondary-bg); /* Use secondary-bg for body background */
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

    /* --- Título Principal con degradado sutil --- */
    .main-title {
        font-size: 2.7em;
        font-weight: bold;
        margin-bottom: 0.1em;
        color: var(--primary-color); /* Use primary-color for main title */
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        transition: transform 0.3s ease-in-out;
    }
    .main-title:hover {
        transform: scale(1.02);
    }

    /* --- Subtítulo con ligera demora en la animación --- */
    .subtitle {
        font-size: 1.2em;
        color: var(--text-color-secondary); /* Use text-color-secondary for subtitle */
        margin-bottom: 1.2em;
        opacity: 0;
        animation: slideUp 0.6s ease-out forwards;
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 0.7; transform: translateY(0); }
    }

    /* --- Barra lateral --- */
    .sidebar .sidebar-content {
        background-color: var(--sidebar-bg); /* Light gray sidebar background */
        padding: 1rem;
    }

    /* --- Contenedor de Mensajes con sombra sutil --- */
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
        animation: fadeInUp 0.3s ease-out forwards;
        overflow-wrap: break-word;
    }

    @keyframes fadeInUp {
        to { opacity: 1; transform: translateY(0); }
        from { opacity: 0; transform: translateY(10px); }
    }


    .user-message {
        background-color: #e6e6e6; /* Lighter gray for user messages */
        color: var(--text-color-primary);
        align-self: flex-end;
        border-left: 4px solid var(--accent-color);
        box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
    }

    .assistant-message {
        background-color: white; /* White for assistant messages */
        color: var(--text-color-primary);
        align-self: flex-start;
        border-left: 4px solid #cccccc; /* Light gray border */
        box-shadow: 1px 1px 3px rgba(0,0,0,0.08);
        transition: box-shadow 0.3s ease;
    }
    .assistant-message:hover {
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }

    .message-content {
        word-wrap: break-word;
    }

    /* --- Campo de Entrada de Texto (Bordes suaves y foco animado) --- */
    .stTextInput > div > div > div > input {
        border: 1.5px solid #cccccc; /* Light gray input border */
        border-radius: 0.5em;
        padding: 0.7em 1em;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput > div > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 5px rgba(var(--primary-color-rgb), 0.5); /* Needs --primary-color-rgb definition if used */
        outline: none;
    }

    /* --- Botones (Efecto de elevación y onda más sutil) --- */
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
        box-shadow: 0 0 0 2px rgba(0, 131, 143, 0.4); /* Original color, adjust if needed */
    }
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

    /* --- Contenedor del Logo en la Barra Lateral (Animación sutil) --- */
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
        border-radius: 50%; /* Make sidebar logo rounded too for consistency */
    }

    /* --- Títulos de la Barra Lateral --- */
    .sidebar .st-bb {
        font-weight: bold;
        margin-bottom: 0.6em;
        color: var(--text-color-primary);
        border-bottom: 1px solid #dddddd; /* Lighter border */
        padding-bottom: 0.4em;
    }

    /* --- Botones de la Barra Lateral (Más sutiles) --- */
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
        background-color: rgba(0, 131, 143, 0.1); /* Original color, adjust if needed */
    }

    /* --- Separadores más ligeros --- */
    hr {
        border-top: 1px solid #dddddd; /* Lighter hr color */
        margin: 1em 0;
    }

    /* --- Enlaces en la Barra Lateral --- */
    .sidebar a {
        color: var(--primary-color);
        text-decoration: none;
        transition: color 0.3s ease;
    }
    .sidebar a:hover {
        color: var(--primary-hover-color);
    }

    /* --- Subtítulos de la Barra Lateral --- */
    .sidebar .st-bb + div {
        margin-top: 0.6em;
        margin-bottom: 0.2em;
        font-size: 0.9em;
        color: var(--text-color-secondary);
    }

    /* --- Contenedor de Conversaciones Guardadas (Hover sutil) --- */
    .sidebar div[data-testid="stVerticalBlock"] > div > div {
        transition: background-color 0.2s ease-in-out;
        border-radius: 0.4em;
        padding: 0.1em 0;
        margin-bottom: 0.05em;
    }
    .sidebar div[data-testid="stVerticalBlock"] > div > div:hover {
        background-color: rgba(0, 0, 0, 0.03);
    }

    /* --- Estilo específico para el botón de "📌" (Más integrado) --- */
    .sidebar .stButton > button:nth-child(3) {
        font-size: 0.7em;
        padding: 0.3em 0.6em;
        border-radius: 0.3em;
        background-color: rgba(0, 131, 143, 0.1); /* Original color, adjust if needed */
        color: var(--primary-color);
    }
    .sidebar .stButton > button:nth-child(3):hover {
        background-color: rgba(0, 131, 143, 0.2); /* Original color, adjust if needed */
    }

    /* --- Rounded Logo in Main Title - More Specific --- */
    .stApp .element-container:nth-child(3) div[data-testid="stImage"] > div > img {
        border-radius: 50%; /* Ensure rounded corners */
        max-width: 100% !important; /* Make sure it respects container width */
        height: auto !important;    /* Maintain aspect ratio */
    }

    /* --- Rounded Avatar in Chat Messages --- */
    .stChatMessage img {
        border-radius: 50%;
    }

    /* --- Assistant Typing Animation --- */
    .assistant-typing {
        display: flex;
        align-items: center;
    }

    .typing-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: var(--text-color-secondary);
        margin-right: 4px;
        animation: typing 1.5s infinite;
    }

    .typing-dot:nth-child(2) {
        animation-delay: 0.5s;
    }

    .typing-dot:nth-child(3) {
        animation-delay: 1s;
    }

    @keyframes typing {
        0% {
            opacity: 0.4;
            transform: translateY(0);
        }
        50% {
            opacity: 1;
            transform: translateY(-2px);
        }
        100% {
            opacity: 0.4;
            transform: translateY(0);
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)

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
col_logo, col_title = st.columns([0.1, 0.9]) # Adjust ratios as needed
with col_logo:
    st.image("https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo", width=80) # Adjust width as needed
with col_title:
    st.markdown('<h1 class="main-title">Asesor Legal Municipal IA</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Instituto Libertad</p>', unsafe_allow_html=True)

# --- API Key Selection Logic ---
def get_available_api_keys() -> List[str]:
    """Checks for configured API keys in st.secrets and returns a list of available key names."""
    available_keys = []
    # print("--- DEBUGGING st.secrets ---")  # Separator for logs
    # print("Contents of st.secrets:", st.secrets)  # Print the entire st.secrets dictionary
    if hasattr(st, 'secrets'): # Check if st.secrets exists
        for i in range(1, 15): # Check for up to 15 API keys
            key_name = f"GOOGLE_API_KEY_{i}"
            if key_name in st.secrets:
                available_keys.append(key_name)
    # print("Available keys found by function:", available_keys) # Print keys found by the function
    # print("--- DEBUGGING st.secrets END ---") # End separator
    return available_keys

available_keys = get_available_api_keys()
selected_key_name = None # Initialize selected_key_name outside if block
GOOGLE_API_KEY = None # Initialize GOOGLE_API_KEY outside if block

if not available_keys and not st.session_state.custom_api_key: # Check for custom key too
    st.error("No API keys configuradas en st.secrets y no se ha ingresado una clave personalizada. Por favor configure al menos una API key (GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.) o ingrese una clave personalizada en la barra lateral. La aplicación no puede ejecutarse.", icon="🚨")
    st.stop() # Stop execution if no API keys are found

if st.session_state.custom_api_key: # Use custom API key if provided
    GOOGLE_API_KEY = st.session_state.custom_api_key
    selected_key_name = "Clave Personalizada" # Indicate custom key is used
elif available_keys: # Fallback to random selection from st.secrets only if available
    selected_key_name = random.choice(available_keys) # Randomly select an API key name
    GOOGLE_API_KEY = st.secrets[selected_key_name] # Access the selected API key
else:
    # This case should theoretically not be reached due to the check above, but added for safety
    st.error("Error crítico: No se pudo determinar una API Key válida.", icon="🚨")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Changed model name

# --- Funciones para cargar y procesar archivos ---

# Usar ruta relativa para la carpeta de datos (más portable)
# Check if running in Streamlit Cloud or locally
if 'STREAMLIT_APP_PATH' in os.environ:
    # Running on Streamlit Cloud, use relative path from app root
    script_dir = os.path.dirname(os.environ['STREAMLIT_APP_PATH'])
else:
    # Running locally, use __file__
    script_dir = os.path.dirname(__file__)

DATABASE_DIR = os.path.join(script_dir, "data")

@st.cache_data(show_spinner=False, persist="disk", max_entries=10) # Caching to load files only once, added max_entries
def load_database_files_cached(directory: str) -> Dict[str, str]:
    """Carga y cachea el contenido de todos los archivos .txt en el directorio, invalidando el caché si los archivos cambian según el hash del contenido."""
    file_contents = {}
    if not os.path.exists(directory):
        st.warning(f"Directorio de base de datos no encontrado: {directory}")
        return file_contents

    file_list = sorted([f for f in os.listdir(directory) if f.endswith(".txt")])
    content_hash = hashlib.sha256()
    current_hash_data = {} # Store hash per file

    # First pass: calculate hashes
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "rb") as f: # Read as bytes for hashing
                file_content_bytes = f.read()
                current_hash_data[filename] = hashlib.sha256(file_content_bytes).hexdigest()
        except Exception as e:
            st.error(f"Error al leer el archivo {filename} para calcular el hash: {e}")
            return {} # Return empty dict on error

    # Check against cached hashes
    if ("database_file_hashes" in st.session_state and
        st.session_state.database_file_hashes == current_hash_data and
        "database_files" in st.session_state and st.session_state.database_files):
        # print("Using cached database files.") # Debug print
        return st.session_state.database_files # Return cached data if hashes match

    # print("Cache invalid or empty, reloading database files.") # Debug print
    # Hashes differ or cache is empty, reload files
    st.session_state.database_files = {} # Reset in-memory cache before reloading
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                st.session_state.database_files[filename] = f.read() # Store in session_state cache
        except Exception as e:
            st.error(f"Error al leer el archivo {filename}: {e}")

    st.session_state.database_file_hashes = current_hash_data # Update cache key with content hash
    return st.session_state.database_files

def load_file_content(uploaded_file) -> str:
    """Carga el contenido de un archivo .txt desde un objeto UploadedFile."""
    try:
        # Check filename extension from the UploadedFile object
        if uploaded_file.name.lower().endswith(".txt"):
            # Use BytesIO to handle the uploaded file object directly
            stringio = BytesIO(uploaded_file.getvalue())
            # Decode assuming UTF-8, handle potential errors
            return stringio.read().decode("utf-8", errors='replace')
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

# --- Prompt mejorado MODIFICADO para enviar TODOS los documentos ---
def create_prompt(database_files_content: Dict[str, str], uploaded_data: str, query: str) -> str:
    """Crea el prompt para el modelo, incluyendo TODA la información de la base de datos y archivos adjuntos."""
    prompt_parts = [
        "Eres un asesor legal virtual altamente especializado en **derecho municipal de Chile**, con un enfoque particular en asistir a alcaldes y concejales. Tu experiencia abarca una amplia gama de temas relacionados con la administración y normativa municipal chilena.",
        "Tu objetivo principal es **responder directamente a las preguntas del usuario de manera precisa y concisa**, siempre **citando la fuente legal o normativa** que respalda tu respuesta. **Prioriza el uso de un lenguaje claro y accesible, evitando jerga legal compleja, para que la información sea fácilmente comprensible para concejales y alcaldes, incluso si no tienen formación legal.**",
        "**MANUAL DE CONCEJALES Y CONCEJALAS (USO EXCLUSIVO COMO CONTEXTO GENERAL):**",
        "Se te proporciona un documento extenso sobre derecho municipal chileno y funciones de concejales. **Utiliza este documento ÚNICAMENTE como contexto general y para entender el marco del derecho municipal chileno y las funciones de los concejales.  NO debes citar este manual en tus respuestas, ni mencionar su nombre en absoluto.  Úsalo para comprender mejor las preguntas y para identificar las leyes o normativas relevantes a las que aludir en tus respuestas, basándote en tu entrenamiento legal.**",
        "**INFORMACIÓN DE LA BASE DE DATOS (NORMAS LEGALES):**" # Modificado el título
    ]

    if database_files_content: # Modificado para usar database_files_content directamente
        for filename, content in database_files_content.items(): # Iterar sobre TODOS los archivos
            if filename == "MANUAL DE CONCEJALES Y CONCEJALAS - 2025 ACHM.txt":
                prompt_parts.append(f"\n**{filename.replace('.txt', '')} (Contexto General):**\n{content}\n") # Add manual content here
                continue # Skip adding it again below
            description = get_file_description(filename)
            # Modified line to remove .txt from filename in prompt
            prompt_parts.append(f"\n**{description} ({filename.replace('.txt', '')}):**\n{content}\n")
    else:
        prompt_parts.append("No se ha cargado información de la base de datos.\n") # Modificado el mensaje

    prompt_parts.append("**INFORMACIÓN ADICIONAL PROPORCIONADA POR EL USUARIO:**")
    prompt_parts.append(uploaded_data if uploaded_data else "No se proporcionó información adicional.\n")

    prompt_parts.extend([ # Usamos extend para añadir múltiples líneas de una vez
        "**IMPORTANTE:** Antes de responder, analiza cuidadosamente la pregunta del usuario para determinar si se relaciona específicamente con la **base de datos de normas legales**, con la **información adicional proporcionada por el usuario**, o con el **derecho municipal general**, **utilizando tu entrenamiento legal en derecho municipal chileno para entender el trasfondo y las figuras jurídicas involucradas en la pregunta.**",
        """
*   **Si la pregunta se relaciona con la base de datos de normas legales:** Utiliza la información de la base de datos como tu principal fuente para responder. **Siempre cita el artículo, sección o norma específica de la base de datos que justifica tu respuesta. Indica claramente en tu respuesta que estás utilizando información de la base de datos y el documento específico.**  Menciona el nombre del documento y la parte pertinente (ej. "Artículo 25 del Reglamento del Concejo Municipal").
*   **Si la pregunta se relaciona con la información adicional proporcionada:** Utiliza esa información como tu principal fuente. **Siempre cita la parte específica de la información adicional que justifica tu respuesta (ej. "Según la jurisprudencia adjunta en el archivo 'Sentencia_Rol_1234-2023.txt'"). Indica claramente en tu respuesta que estás utilizando información proporcionada por el usuario y el documento específico.**
*   **Si la pregunta es sobre otros aspectos del derecho municipal chileno:** Utiliza tu conocimiento general en la materia, basado en tu entrenamiento legal. **Siempre cita la norma legal general del derecho municipal chileno que justifica tu respuesta (ej. "Según el artículo 65 de la Ley Orgánica Constitucional de Municipalidades"). Indica claramente en tu respuesta que estás utilizando tu conocimiento general de derecho municipal chileno y la norma general.**
        """,
        "Esta es una herramienta creada por y para el Instituto Libertad por Aldo Manuel Herrera Hernández.",
        "**Metodología LegalDesign:**",
        """
*   **Claridad y Concisión:** Responde de manera directa y al grano. Evita rodeos innecesarios.
*   **Estructura:** Organiza las respuestas con encabezados, viñetas o listas numeradas para facilitar la lectura y comprensión, especialmente si hay varios puntos en la respuesta.
*   **Visualizaciones (si es posible):** Aunque textual, piensa en cómo la información podría representarse visualmente para mejorar la comprensión (por ejemplo, un flujo de proceso mentalmente).
*   **Ejemplos:**  Si es pertinente, incluye ejemplos prácticos y sencillos para ilustrar los conceptos legales.
*   **Lenguaje sencillo:** Utiliza un lenguaje accesible para personas sin formación legal especializada, pero manteniendo la precisión legal.
        """,
        "**Instrucciones específicas:**",
        """
*   Comienza tus respuestas con un **breve resumen conciso de la respuesta en una frase inicial.**
*   Luego, **desarrolla la respuesta de manera completa y detallada**, proporcionando un análisis legal **citando siempre la fuente normativa específica.** **NUNCA CITES EL MANUAL DE DERECHO MUNICIPAL PROPORCIONADO DIRECTAMENTE NI ALUDAS A ÉL POR NINGÚN MEDIO, EXCEPTO PARA DECIR QUE LO USAS COMO CONTEXTO GENERAL SI ES NECESARIO.**
    *   **Prioriza la información de la base de datos de normas legales** cuando la pregunta se refiera específicamente a este documento. **Cita explícitamente el documento y la parte relevante (artículo, sección, etc.).**
    *   **Luego, considera la información adicional proporcionada por el usuario** si es relevante para la pregunta. **Cita explícitamente el documento adjunto y la parte relevante.**
    *   Para preguntas sobre otros temas de derecho municipal chileno, utiliza tu conocimiento general, basado en tu entrenamiento legal. **Cita explícitamente la norma general del derecho municipal chileno.**
*   **Si la pregunta se relaciona con el funcionamiento interno del Concejo Municipal, como sesiones, tablas, puntos, o reglamento interno, y para responder correctamente se necesita información específica sobre reglamentos municipales, indica lo siguiente, basado en tu entrenamiento legal:** "Las normas sobre el funcionamiento interno del concejo municipal, como sesiones, tablas y puntos, se encuentran reguladas principalmente en el Reglamento Interno de cada Concejo Municipal.  Por lo tanto, **las reglas específicas pueden variar significativamente entre municipalidades.**  Mi respuesta se basará en mi entrenamiento en derecho municipal chileno y las normas generales que rigen estas materias, **pero te recomiendo siempre verificar el Reglamento Interno específico de tu municipalidad para obtener detalles precisos.**"  **Si encuentras información relevante en tu entrenamiento legal sobre el tema, proporciona una respuesta basada en él, pero siempre incluyendo la advertencia sobre la variabilidad entre municipalidades.**
*   **Si la información para responder la pregunta no se encuentra en la base de datos de normas legales proporcionada (excluyendo el manual de contexto), responde de forma concisa:** "Según la información disponible en la base de datos de normas legales, no puedo responder a esta pregunta."
*   **Si la información para responder la pregunta no se encuentra en la información adicional proporcionada, responde de forma concisa:** "Según la información adicional proporcionada, no puedo responder a esta pregunta."
*   **Si la información para responder la pregunta no se encuentra en tu conocimiento general de derecho municipal chileno (ni en el manual de contexto), responde de forma concisa:** "Según mi conocimiento general de derecho municipal chileno, no puedo responder a esta pregunta."
*   **IMPORTANTE: SIEMPRE CITA LA FUENTE NORMATIVA EN TUS RESPUESTAS. NUNCA MENCIONES NI CITES DIRECTAMENTE EL MANUAL DE DERECHO MUNICIPAL PROPORCIONADO, EXCEPTO PARA INDICAR QUE LO USAS COMO CONTEXTO GENERAL SI ES NECESARIO.**
        """,
        "**Ejemplos de respuestas esperadas (con resumen y citación - SIN CITAR MANUAL DIRECTAMENTE, BASADO EN ENTRENAMIENTO LEGAL Y DATOS):**",
        """
*   **Pregunta del Usuario:** "¿Cuáles son las funciones del concejo municipal?"
    *   **Respuesta Esperada:** "Resumen: Las funciones del concejo municipal son normativas, fiscalizadoras y representativas.
        Desarrollo: Efectivamente, las funciones del concejo municipal se clasifican en normativas, fiscalizadoras y representativas. Esta clasificación se basa en mi entrenamiento general sobre derecho municipal chileno y se encuentra detallada en el artículo 79 de la Ley Orgánica Constitucional de Municipalidades (Nº 18.695)."
*   **Pregunta del Usuario:** "¿Qué dice el artículo 25 sobre las citaciones a las sesiones en el Reglamento del Concejo Municipal?"
    *   **Respuesta Esperada:** "Resumen: El artículo 25 del Reglamento del Concejo Municipal establece los plazos y formalidades para las citaciones a sesiones ordinarias y extraordinarias.
        Desarrollo: Así es, el artículo 25 del documento 'Reglamento Concejo Municipal' detalla los plazos y formalidades que deben seguirse al realizar citaciones tanto para sesiones ordinarias como extraordinarias (Artículo 25 del Reglamento Concejo Municipal)."
*   **Pregunta del Usuario:** (Adjunta un archivo con jurisprudencia sobre transparencia municipal) "¿Cómo se aplica esta jurisprudencia en el concejo?"
    *   **Respuesta Esperada:** "Resumen: La jurisprudencia adjunta establece criterios sobre publicidad y acceso a la información pública municipal, relevantes para la transparencia del concejo.
        Desarrollo: Correcto, la jurisprudencia que adjuntas en el archivo proporcionado por el usuario define criterios importantes sobre la publicidad de las sesiones del concejo y el acceso a la información pública municipal. Estos criterios deben ser considerados para asegurar la transparencia en todas las actuaciones del concejo (Según la información adicional proporcionada por el usuario)."
*   **Pregunta del Usuario:** "¿Cómo se define la tabla de una sesión del concejo municipal?"
    *   **Respuesta Esperada:** "Resumen: La tabla de una sesión del concejo municipal es el listado de temas a tratar en la sesión, fijada por el alcalde, aunque los detalles pueden variar según el reglamento interno.
        Desarrollo: Las normas específicas sobre la tabla de sesiones se encuentran en el Reglamento Interno de cada Concejo Municipal, por lo que pueden variar. Basándome en mi entrenamiento en derecho municipal chileno, la tabla de una sesión se define como el listado de los temas específicos que serán tratados en una sesión del concejo, y su fijación es generalmente responsabilidad del alcalde (Artículo 82, Ley Nº 18.695). **Es importante verificar el Reglamento Interno de tu municipalidad, ya que los detalles de este proceso pueden variar entre municipios.**"
        """,
        "**Historial de conversación:**"
    ])

    # Añadir historial de conversación
    for msg in st.session_state.messages[:-1]: # Exclude the latest user message which is the current query
        if msg["role"] == "user":
            prompt_parts.append(f"Usuario: {msg['content']}\n")
        elif msg["role"] == "assistant": # Ensure only assistant messages are added here
            prompt_parts.append(f"Asistente: {msg['content']}\n")

    prompt_parts.append(f"**Pregunta actual del usuario:** {query}")

    return "\n".join(prompt_parts)


# --- Inicializar el estado para los archivos ---
if "database_files" not in st.session_state:
    st.session_state.database_files = {}
if "uploaded_files_content" not in st.session_state:
    st.session_state.uploaded_files_content = ""
if "database_file_hashes" not in st.session_state: # Changed from database_cache_key
    st.session_state.database_file_hashes = {}
if "uploaded_file_names" not in st.session_state: # To store names of uploaded files
    st.session_state.uploaded_file_names = []


# --- Carga inicial de archivos ---
def load_database_files_on_startup():
    """Carga todos los archivos de la base de datos al inicio."""
    # print(f"Attempting to load database from: {DATABASE_DIR}") # Debug print
    st.session_state.database_files = load_database_files_cached(DATABASE_DIR) # Load/refresh database files
    # print(f"Loaded {len(st.session_state.database_files)} files from database.") # Debug print
    return len(st.session_state.database_files)

database_files_loaded_count = load_database_files_on_startup()

# --- Inicializar el estado de la sesión ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! Soy tu asesor legal IA especializado en derecho municipal. Esta es una herramienta del Instituto Libertad diseñada para guiar en las funciones de alcalde y concejales, sirviendo como apoyo, pero NO como reemplazo del asesoramiento de un abogado especializado en derecho público. Estoy listo para analizar tus consultas. ¿En qué puedo ayudarte hoy?"})

if "saved_conversations" not in st.session_state:
    st.session_state.saved_conversations = {}

if "current_conversation_name" not in st.session_state:
    st.session_state.current_conversation_name = "Nueva Conversación"

def save_conversation(name, messages, pinned=False):
    # Ensure messages are serializable (list of dicts)
    serializable_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    st.session_state.saved_conversations[name] = {"messages": serializable_messages, "pinned": pinned}


def delete_conversation(name):
    if name in st.session_state.saved_conversations:
        del st.session_state.saved_conversations[name]

def load_conversation(name):
    if name in st.session_state.saved_conversations:
        # Ensure loaded messages are in the correct format
        loaded_messages = st.session_state.saved_conversations[name]["messages"]
        st.session_state.messages = [{"role": msg["role"], "content": msg["content"]} for msg in loaded_messages]
        st.session_state.current_conversation_name = name


def pin_conversation(name):
    if name in st.session_state.saved_conversations:
        st.session_state.saved_conversations[name]["pinned"] = True

def unpin_conversation(name):
    if name in st.session_state.saved_conversations:
        st.session_state.saved_conversations[name]["pinned"] = False

# --- Barra lateral ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo-container"></div>', unsafe_allow_html=True)
    st.header("Menú Principal") # Changed Header

    disclaimer_status_expander = st.expander("Estado del Disclaimer", expanded=True) # Initially expanded
    with disclaimer_status_expander:
        if st.session_state.disclaimer_accepted:
            st.success("Disclaimer Aceptado", icon="✅")
            if st.button("Revocar Disclaimer"):
                st.session_state.disclaimer_accepted = False
                st.rerun()
        else:
            st.warning("Disclaimer No Aceptado", icon="⚠️")
            st.markdown("Para usar el Asesor Legal, debes aceptar el Disclaimer.")

    st.subheader("Estado API Key") # API Key Status Section
    if selected_key_name:
        st.success(f"Usando API Key: {selected_key_name}", icon="🔑") # Display selected API key
    else:
        st.warning("No se está usando API Key (Error)", icon="⚠️")

    st.subheader("API Key Personalizada (Opcional)") # Custom API Key Input
    custom_api_key_input = st.text_input("Ingresa tu API Key personalizada:", type="password", value=st.session_state.custom_api_key, help="Si deseas usar una API Key diferente a las configuradas en st.secrets, puedes ingresarla aquí. Esto tiene prioridad sobre las API Keys de st.secrets.")
    if custom_api_key_input != st.session_state.custom_api_key:
        st.session_state.custom_api_key = custom_api_key_input
        st.rerun() # Rerun to apply the new API key

    st.subheader("Cargar Datos Adicionales")
    uploaded_files = st.file_uploader("Adjuntar archivos adicionales (.txt)", type=["txt"], help="Puedes adjuntar archivos .txt adicionales para que sean considerados en la respuesta.", accept_multiple_files=True, key="file_uploader") # Added key
    if uploaded_files:
        newly_uploaded_content = ""
        newly_uploaded_names = []
        # Process only new files if some were already processed
        current_uploaded_names = [f.name for f in uploaded_files]
        new_files_to_process = [f for f in uploaded_files if f.name not in st.session_state.uploaded_file_names]

        if new_files_to_process:
            # Reset content only if new files are added
            st.session_state.uploaded_files_content = ""
            st.session_state.uploaded_file_names = []
            for uploaded_file in uploaded_files: # Process all currently selected files
                try:
                    # Pass the UploadedFile object directly
                    content = load_file_content(uploaded_file)
                    if content: # Add content only if successfully loaded
                        st.session_state.uploaded_files_content += f"--- INICIO ARCHIVO: {uploaded_file.name} ---\n{content}\n--- FIN ARCHIVO: {uploaded_file.name} ---\n\n"
                        st.session_state.uploaded_file_names.append(uploaded_file.name)
                except Exception as e:
                    st.error(f"Error al procesar el archivo adjunto {uploaded_file.name}: {e}")
            st.success(f"{len(st.session_state.uploaded_file_names)} archivo(s) adicional(es) cargado(s).")
            # No rerun needed here, state is updated

    # Display currently loaded additional files
    if st.session_state.uploaded_file_names:
        st.markdown("**Archivos adicionales cargados:**")
        for name in st.session_state.uploaded_file_names:
            st.markdown(f"- `{name}`")
        if st.button("Limpiar archivos adicionales"):
            st.session_state.uploaded_files_content = ""
            st.session_state.uploaded_file_names = []
            # Reset the file uploader widget state by changing its key slightly or using experimental_rerun
            st.rerun()


    st.subheader("Gestión de Conversación") # Changed Header
    new_conversation_name = st.text_input("Título conversación:", value=st.session_state.current_conversation_name)
    if new_conversation_name != st.session_state.current_conversation_name:
        st.session_state.current_conversation_name = new_conversation_name

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Guardar", help="Guarda la conversación actual con el título ingresado."): # Added help text
            # Limit saved conversations (optional, implement if needed)
            # if len(st.session_state.saved_conversations) >= 10: # Example limit
            #     # Logic to remove oldest or unpinned conversation
            #     st.warning("Límite de conversaciones guardadas alcanzado.")
            # else:
            save_conversation(st.session_state.current_conversation_name, st.session_state.messages)
            st.success(f"Conversación '{st.session_state.current_conversation_name}' guardada!", icon="💾")
            # No rerun needed, just update state
    with col2:
        if st.button("Borrar Chat", key="clear_chat_sidebar", help="Borra los mensajes de la conversación actual (excepto el saludo inicial)."): # Added help text
            st.session_state.messages = [st.session_state.messages[0]] # Keep initial greeting
            st.session_state.current_conversation_name = "Nueva Conversación" # Reset name for clarity
            st.rerun()
    with col3:
        # Pinning logic only makes sense if the conversation is already saved
        is_saved = st.session_state.current_conversation_name in st.session_state.saved_conversations
        if is_saved:
            is_pinned = st.session_state.saved_conversations[st.session_state.current_conversation_name].get('pinned', False)
            pin_label = "Quitar Pin" if is_pinned else "Fijar"
            pin_icon = "📌"
            if st.button(f"{pin_icon} {pin_label}", key="pin_button", help="Fija o desfija la conversación actual en la lista de guardadas."): # Added help text
                if is_pinned:
                    unpin_conversation(st.session_state.current_conversation_name)
                    st.success(f"Conversación '{st.session_state.current_conversation_name}' desfijada.")
                else:
                    pin_conversation(st.session_state.current_conversation_name)
                    st.success(f"Conversación '{st.session_state.current_conversation_name}' fijada.")
                st.rerun() # Rerun to update the saved list display
        else:
            st.button("Fijar", disabled=True, help="Guarda la conversación primero para poder fijarla.") # Disabled button if not saved


    st.subheader("Conversaciones Guardadas")
    # Sort saved conversations: Pinned first, then alphabetically
    sorted_conversations = sorted(
        st.session_state.saved_conversations.items(),
        key=lambda item: (not item[1]['pinned'], item[0].lower()) # Sort by not pinned (False=0, True=1), then name
    )

    if not sorted_conversations:
        st.caption("No hay conversaciones guardadas.")
    else:
        for name, data in sorted_conversations:
            cols = st.columns([0.7, 0.15, 0.15]) # Adjusted column ratios
            with cols[0]:
                pin_indicator = "📌 " if data['pinned'] else ""
                if st.button(f"{pin_indicator}{name}", key=f"load_{name}", help=f"Cargar conversación '{name}'"): # Added help text
                    load_conversation(name)
                    # st.session_state.current_conversation_name = name # load_conversation already does this
                    st.rerun()
            with cols[1]:
                 # Add Pin/Unpin button directly here for saved items
                is_pinned = data.get('pinned', False)
                pin_label_saved = " ➖ " if is_pinned else " ➕ " # Use different icons maybe?
                pin_help = "Quitar Pin" if is_pinned else "Fijar"
                if st.button(f"📌{pin_label_saved}", key=f"pin_saved_{name}", help=f"{pin_help} conversación '{name}'"):
                    if is_pinned:
                        unpin_conversation(name)
                    else:
                        pin_conversation(name)
                    st.rerun() # Rerun to update list order
            with cols[2]:
                if st.button("🗑️", key=f"delete_{name}", help=f"Borrar conversación '{name}'"): # Added help text
                    delete_conversation(name)
                    # If deleting the current conversation, reset chat
                    if name == st.session_state.current_conversation_name:
                         st.session_state.messages = [st.session_state.messages[0]]
                         st.session_state.current_conversation_name = "Nueva Conversación"
                    st.rerun()

    st.markdown("---")
    st.header("Acerca de")
    st.markdown("Este asesor legal virtual fue creado por Aldo Manuel Herrera Hernández para el **Instituto Libertad** y se especializa en asesoramiento en derecho administrativo y municipal de **Chile**, basándose en la información que le proporciones.")
    st.markdown("Esta herramienta es desarrollada por el **Instituto Libertad**.")
    st.markdown("La información proporcionada aquí se basa en el contenido de los archivos .txt que cargues como base de datos del reglamento y los archivos adicionales que adjuntes, y no reemplaza el asesoramiento legal profesional.") # Updated description to remove PDF
    st.markdown("---")
    st.markdown("**Instituto Libertad**")
    st.markdown("[Sitio Web](https://www.institutolibertad.cl)")
    st.markdown("[Contacto](mailto:contacto@institutolibertad.cl)")

    st.subheader("Datos Cargados")
    if st.session_state.database_files:
        st.markdown(f"**Base de Datos:** Se ha cargado información desde {database_files_loaded_count} archivo(s) automáticamente.")
        # Display loaded database file names
        with st.expander("Ver archivos de base de datos cargados"):
             for db_filename in st.session_state.database_files.keys():
                 st.caption(f"- {db_filename}")
        if st.button("Recargar Base de Datos", key="refresh_db_button", help="Vuelve a cargar los archivos desde la carpeta 'data'."): # Refresh Database Button
            database_files_loaded_count = load_database_files_on_startup()
            st.success(f"Base de datos recargada ({database_files_loaded_count} archivos).", icon="🔄")
            st.rerun() # Rerun to reflect changes immediately in chat if needed
    # Removed redundant display of uploaded files count here, already shown above

    if not st.session_state.database_files and not st.session_state.uploaded_files_content:
        st.warning("No se ha cargado ninguna base de datos del reglamento ni archivos adicionales.")
    elif not st.session_state.database_files:
        st.warning("No se ha encontrado o cargado la base de datos del reglamento automáticamente desde la carpeta 'data'.")


# --- Área de chat ---
if st.session_state.disclaimer_accepted: # Only show chat if disclaimer is accepted
    # Display chat messages
    message_container = st.container() # Use a container to manage chat messages display
    with message_container:
        for message in st.session_state.messages:
            avatar_url = "https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo" if message["role"] == "assistant" else None
            with st.chat_message(message["role"], avatar=avatar_url):
                 st.markdown(message["content"]) # Use markdown for potential formatting in response


    # --- Campo de entrada para el usuario ---
    if prompt := st.chat_input("Escribe tu consulta...", key="chat_input"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message immediately
        with message_container: # Add to the same container
             with st.chat_message("user"):
                 st.markdown(prompt)

        # Prepare and send prompt to the model, display response
        with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
            message_placeholder = st.empty()
            # Display typing indicator
            typing_placeholder = st.empty()
            typing_placeholder.markdown('<div class="assistant-typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>', unsafe_allow_html=True)

            try:
                # Create the full prompt including history and context
                prompt_completo = create_prompt(
                    st.session_state.database_files,
                    st.session_state.uploaded_files_content,
                    prompt
                )

                # Generate response stream
                response = model.generate_content(prompt_completo, stream=True)

                full_response_content = ""
                for chunk in response:
                    # Check for potential errors or empty chunks in the stream
                    try:
                        chunk_text = chunk.text
                        full_response_content += chunk_text
                        message_placeholder.markdown(full_response_content + "▌") # Update placeholder with streaming text
                    except ValueError as ve:
                         # Handle potential content blocking or other issues gracefully
                         st.warning(f"Advertencia: Se encontró un problema en parte de la respuesta ({ve}). Mostrando contenido parcial.", icon="⚠️")
                         # Continue processing other chunks if possible
                         continue
                    except Exception as chunk_error:
                         st.error(f"Error procesando un chunk de la respuesta: {chunk_error}", icon="🚨")
                         full_response_content += "\n\n[Error procesando parte de la respuesta]"
                         break # Stop processing stream on chunk error
                    time.sleep(0.01) # Small delay for streaming effect

                # Clear typing indicator and finalize message
                typing_placeholder.empty()
                message_placeholder.markdown(full_response_content) # Display final complete response

                # Add final assistant response to session state
                st.session_state.messages.append({"role": "assistant", "content": full_response_content})

                # Safety check in case the stream finished but yielded no actual content
                if not full_response_content.strip():
                    st.error("El modelo no generó una respuesta para esta consulta.", icon="❓")
                    st.session_state.messages.append({"role": "assistant", "content": "[El modelo no generó respuesta]"})


            except Exception as e:
                typing_placeholder.empty() # Ensure typing indicator is removed on error
                st.error(f"Ocurrió un error al comunicarse con el modelo IA: {e}. Por favor, revisa tu API Key o intenta de nuevo.", icon="🚨")
                # Add error message to chat history
                error_message = f"Error al generar respuesta: {e}"
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                message_placeholder.markdown(error_message) # Show error in the chat message area

            # Rerun slightly after response generation to ensure layout updates smoothly
            # time.sleep(0.1)
            # st.rerun() # Consider if rerun is truly needed here, might cause flicker

else: # Disclaimer not accepted, show message instead of chat
    st.warning("Para usar el Asesor Legal Municipal IA, debes aceptar el Disclaimer.", icon="⚠️")
    st.info("Por favor, lee y acepta el descargo de responsabilidad en la pantalla inicial para continuar.")