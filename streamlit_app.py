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

# --- Password and Disclaimer State ---
if "authentication_successful" not in st.session_state:
    st.session_state.authentication_successful = False
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "password_input" not in st.session_state:
    st.session_state.password_input = "" # Initialize password input
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = "" # Initialize custom API key state

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
    for i in range(1, 6): # Check for up to 5 API keys
        key_name = f"GOOGLE_API_KEY_{i}"
        if key_name in st.secrets:
            available_keys.append(key_name)
    return available_keys

available_keys = get_available_api_keys()
selected_key_name = None # Initialize selected_key_name outside if block
GOOGLE_API_KEY = None # Initialize GOOGLE_API_KEY outside if block

if not available_keys and not st.session_state.custom_api_key: # Check for custom key too
    st.error("No API keys configured in st.secrets y no se ha ingresado una clave personalizada. Por favor configure al menos una API key (GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.) o ingrese una clave personalizada en la barra lateral. La aplicación no puede ejecutarse.", icon="🚨")
    st.stop() # Stop execution if no API keys are found

if st.session_state.custom_api_key: # Use custom API key if provided
    GOOGLE_API_KEY = st.session_state.custom_api_key
    selected_key_name = "Clave Personalizada" # Indicate custom key is used
else: # Fallback to random selection from st.secrets
    selected_key_name = random.choice(available_keys) # Randomly select an API key name
    GOOGLE_API_KEY = st.secrets[selected_key_name] # Access the selected API key

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

# --- Funciones para cargar y procesar archivos ---

# Usar ruta relativa para la carpeta de datos (más portable)
script_dir = os.path.dirname(__file__)
DATABASE_DIR = os.path.join(script_dir, "data")

@st.cache_data(show_spinner=False, persist="disk", max_entries=10) # Caching to load files only once, added max_entries
def load_database_files_cached(directory: str) -> Dict[str, str]:
    """Carga y cachea el contenido de todos los archivos .txt en el directorio, invalidando el caché si los archivos cambian."""
    file_contents = {}
    if not os.path.exists(directory):
        st.warning(f"Directorio de base de datos no encontrado: {directory}")
        return file_contents

    file_list = sorted([f for f in os.listdir(directory) if f.endswith(".txt")])
    cache_key = hashlib.md5(str(file_list).encode()).hexdigest() # Using filenames for cache key

    if "database_cache_key" in st.session_state and st.session_state.database_cache_key == cache_key and st.session_state.database_files:
        return st.session_state.database_files # Return cached data if key is the same

    st.session_state.database_files = {} # Reset in-memory cache before reloading
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                st.session_state.database_files[filename] = f.read() # Store in session_state cache
        except Exception as e:
            st.error(f"Error al leer el archivo {filename}: {e}")

    st.session_state.database_cache_key = cache_key # Update cache key
    return st.session_state.database_files

def load_file_content(filepath: str) -> str:
    """Carga el contenido de un archivo .txt."""
    try:
        if filepath.lower().endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        else:
            st.error(f"Tipo de archivo no soportado: {filepath}")
            return ""
    except Exception as e:
        st.error(f"Error al leer el archivo {filepath}: {e}")
        return ""

def get_file_description(filename: str) -> str:
    """Genera una descripción genérica para un archivo basado en su nombre."""
    name_parts = filename.replace(".txt", "").split("_")
    return " ".join(word.capitalize() for word in name_parts)

def discover_and_load_files(directory: str) -> Dict[str, str]:
    """Descubre y carga todos los archivos .txt en un directorio.""" # Updated description
    file_contents = {}
    if not os.path.exists(directory):
        st.warning(f"Directorio de base de datos no encontrado: {directory}")
        return file_contents

    for filename in os.listdir(directory):
        if filename.endswith(".txt"): # Only process .txt files
            filepath = os.path.join(directory, filename)
            file_contents[filename] = load_file_content(filepath)
    return file_contents


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
                continue # Exclude manual from this section, it's already handled above
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
*   Luego, **desarrolla la respuesta de manera completa y detallada**, proporcionando un análisis legal **citando siempre la fuente normativa específica.** **NUNCA CITES EL MANUAL DE DERECHO MUNICIPAL PROPORCIONADO DIRECTAMENTE NI ALUDAS A ÉL POR NINGÚN MEDIO.**
    *   **Prioriza la información de la base de datos de normas legales** cuando la pregunta se refiera específicamente a este documento. **Cita explícitamente el documento y la parte relevante (artículo, sección, etc.).**
    *   **Luego, considera la información adicional proporcionada por el usuario** si es relevante para la pregunta. **Cita explícitamente el documento adjunto y la parte relevante.**
    *   Para preguntas sobre otros temas de derecho municipal chileno, utiliza tu conocimiento general, pero sé conciso y preciso. **Cita explícitamente la norma general del derecho municipal chileno.**
*   **Si la pregunta se relaciona con el funcionamiento interno del Concejo Municipal, como sesiones, tablas, puntos, o reglamento interno, y para responder correctamente se necesita información específica sobre reglamentos municipales, indica lo siguiente, basado en tu entrenamiento legal:** "Las normas sobre el funcionamiento interno del concejo municipal, como sesiones, tablas y puntos, se encuentran reguladas principalmente en el Reglamento Interno de cada Concejo Municipal.  Por lo tanto, **las reglas específicas pueden variar significativamente entre municipalidades.**  Mi respuesta se basará en mi entrenamiento en derecho municipal chileno y las normas generales que rigen estas materias, **pero te recomiendo siempre verificar el Reglamento Interno específico de tu municipalidad para obtener detalles precisos.**"  **Si encuentras información relevante en tu entrenamiento legal sobre el tema, proporciona una respuesta basada en él, pero siempre incluyendo la advertencia sobre la variabilidad entre municipalidades.**
*   **Si la información para responder la pregunta no se encuentra en la base de datos de normas legales proporcionada, responde de forma concisa: "Según la información disponible en la base de datos, no puedo responder a esta pregunta."**
*   **Si la información para responder la pregunta no se encuentra en la información adicional proporcionada, responde de forma concisa: "Según la información adicional proporcionada, no puedo responder a esta pregunta."**
*   **Si la información para responder la pregunta no se encuentra en tu conocimiento general de derecho municipal chileno, responde de forma concisa: "Según mi conocimiento general de derecho municipal chileno, no puedo responder a esta pregunta."**
*   **IMPORTANTE: SIEMPRE CITA LA FUENTE NORMATIVA EN TUS RESPUESTAS. NUNCA MENCIONES NI CITES DIRECTAMENTE EL MANUAL DE DERECHO MUNICIPAL PROPORCIONADO.**
        """,
        "**Ejemplos de respuestas esperadas (con resumen y citación - SIN MANUAL, BASADO EN ENTRENAMIENTO LEGAL):**",
        """
*   **Pregunta del Usuario:** "¿Cuáles son las funciones del concejo municipal?"
    *   **Respuesta Esperada:** "Resumen: Las funciones del concejo municipal son normativas, fiscalizadoras y representativas.
        Desarrollo:  Efectivamente, las funciones del concejo municipal se clasifican en normativas, fiscalizadoras y representativas (Según el artículo 65 de la Ley Orgánica Constitucional de Municipalidades)."
*   **Pregunta del Usuario:** "¿Qué dice el artículo 25 sobre las citaciones a las sesiones en el Reglamento del Concejo Municipal?"
    *   **Respuesta Esperada:** "Resumen: El artículo 25 del Reglamento del Concejo Municipal establece los plazos y formalidades para las citaciones a sesiones ordinarias y extraordinarias.
        Desarrollo:  Así es, el artículo 25 del Reglamento del Concejo Municipal detalla los plazos y formalidades que deben seguirse al realizar citaciones tanto para sesiones ordinarias como extraordinarias (Artículo 25 del Reglamento del Concejo Municipal)."
*   **Pregunta del Usuario:** (Adjunta un archivo con jurisprudencia sobre transparencia municipal) "¿Cómo se aplica esta jurisprudencia en el concejo?"
    *   **Respuesta Esperada:** "Resumen: La jurisprudencia adjunta establece criterios sobre publicidad y acceso a la información pública municipal, relevantes para la transparencia del concejo.
        Desarrollo:  Correcto, la jurisprudencia que adjuntas en 'Sentencia_Rol_1234-2023.txt' define criterios importantes sobre la publicidad de las sesiones del concejo y el acceso a la información pública municipal. Estos criterios deben ser considerados para asegurar la transparencia en todas las actuaciones del concejo (Según la jurisprudencia adjunta en el archivo 'Sentencia_Rol_1234-2023.txt')."
*   **Pregunta del Usuario:** "¿Cómo se define la tabla de una sesión del concejo municipal?"
    *   **Respuesta Esperada:** "Resumen: La tabla de una sesión del concejo municipal es el listado de temas a tratar en la sesión, fijada por el alcalde.
        Desarrollo: Las normas sobre la tabla de sesiones se encuentran en el Reglamento Interno de cada Concejo Municipal, por lo que pueden variar.  Basándome en mi entrenamiento en derecho municipal chileno, la tabla de una sesión se define como el listado de los temas específicos que serán tratados en una sesión del concejo, y su fijación es responsabilidad del alcalde. **Es importante verificar el Reglamento Interno de tu municipalidad, ya que los detalles de este proceso pueden variar entre municipios.**"
        """,
        "**Historial de conversación:**"
    ])

    # Añadir historial de conversación
    for msg in st.session_state.messages[:-1]:
        if msg["role"] == "user":
            prompt_parts.append(f"Usuario: {msg['content']}\n")
        else:
            prompt_parts.append(f"Asistente: {msg['content']}\n")

    prompt_parts.append(f"**Pregunta actual del usuario:** {query}")

    return "\n".join(prompt_parts)

# --- Inicializar el estado para los archivos ---
if "database_files" not in st.session_state:
    st.session_state.database_files = {}
if "uploaded_files_content" not in st.session_state:
    st.session_state.uploaded_files_content = ""
if "database_cache_key" not in st.session_state:
    st.session_state.database_cache_key = None

# --- Carga inicial de archivos ---
def load_database_files_on_startup():
    """Carga todos los archivos de la base de datos al inicio."""
    st.session_state.database_files = load_database_files_cached(DATABASE_DIR) # Load/refresh database files
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

# --- Barra lateral ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo-container"></div>', unsafe_allow_html=True)
    st.header("Historial de Conversaciones")

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
    uploaded_files = st.file_uploader("Adjuntar archivos adicionales (.txt)", type=["txt"], help="Puedes adjuntar archivos .txt adicionales para que sean considerados en la respuesta.", accept_multiple_files=True) # Updated to only accept .txt
    if uploaded_files:
        st.session_state.uploaded_files_content = ""
        for uploaded_file in uploaded_files:
            try:
                content = load_file_content(uploaded_file.name) # Pass filename for correct reading
                st.session_state.uploaded_files_content += content + "\n\n"
            except Exception as e:
                st.error(f"Error al leer el archivo adjunto {uploaded_file.name}: {e}")

    if st.button("Limpiar archivos adicionales"):
        st.session_state.uploaded_files_content = ""
        st.rerun()

    new_conversation_name = st.text_input("Título conversación:", value=st.session_state.current_conversation_name)
    if new_conversation_name != st.session_state.current_conversation_name:
        st.session_state.current_conversation_name = new_conversation_name

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Guardar"):
            if len(st.session_state.saved_conversations) >= 5:
                unpinned_conversations = [name for name, data in st.session_state.saved_conversations.items() if not data['pinned']]
                if unpinned_conversations:
                    oldest_unpinned = min(st.session_state.saved_conversations, key=lambda k: st.session_state.saved_conversations[k]['messages'][0]['content'] if st.session_state.saved_conversations[k]['messages'] else "")
                    delete_conversation(oldest_unpinned)
            st.session_state.messages_before_save = list(st.session_state.messages)
            save_conversation(st.session_state.current_conversation_name, st.session_state.messages_before_save)
            st.success("Conversación guardada!", icon="💾")
            st.rerun()
    with col2:
        if st.button("Borrar Chat", key="clear_chat_sidebar"):
            st.session_state.messages = [st.session_state.messages[0]]
            st.rerun()
    with col3:
        is_pinned = st.session_state.saved_conversations.get(st.session_state.current_conversation_name, {}).get('pinned', False)
        if st.button("📌" if not is_pinned else " 📌 ", key="pin_button"):
            if st.session_state.current_conversation_name in st.session_state.saved_conversations:
                if is_pinned:
                    unpin_conversation(st.session_state.current_conversation_name)
                else:
                    pin_conversation(st.session_state.current_conversation_name)
                st.rerun()

    st.subheader("Conversaciones Guardadas")
    for name, data in sorted(st.session_state.saved_conversations.items(), key=lambda item: item[1]['pinned'], reverse=True):
        cols = st.columns([0.7, 0.2, 0.1])
        with cols[0]:
            if st.button(f"{'📌' if data['pinned'] else ''} {name}", key=f"load_{name}"):
                load_conversation(name)
                st.session_state.current_conversation_name = name
                st.rerun()
        with cols[1]:
            if st.button("🗑️", key=f"delete_{name}"):
                delete_conversation(name)
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
    if st.session_state.uploaded_files_content:
        uploaded_file_count = 0
        if uploaded_files: # Check if uploaded_files is defined to avoid errors on initial load
            uploaded_file_count = len(uploaded_files)
        st.markdown(f"**Archivos Adicionales:** Se ha cargado información desde {uploaded_file_count} archivo(s).") # Updated description to remove PDF
    if not st.session_state.database_files and not st.session_state.uploaded_files_content:
        st.warning("No se ha cargado ninguna base de datos del reglamento ni archivos adicionales.")
    elif not st.session_state.database_files:
        st.warning("No se ha encontrado o cargado la base de datos del reglamento automáticamente.")

# --- Área de chat ---
if st.session_state.disclaimer_accepted: # Only show chat if disclaimer is accepted
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><div class="message-content">{message["content"]}</div></div>', unsafe_allow_html=True)
            else:
                with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"): # Moved avatar here
                    st.markdown(f'<div class="message-content">{message["content"]}</div>', unsafe_allow_html=True)

    # --- Campo de entrada para el usuario ---
    if prompt := st.chat_input("Escribe tu consulta...", key="chat_input"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Immediately display user message
        with st.container():
            st.markdown(f'<div class="chat-message user-message"><div class="message-content">{prompt}</div></div>', unsafe_allow_html=True)

        # Process query and generate assistant response in a separate container
        with st.container(): # New container for processing and assistant response
            # **YA NO ANALIZAMOS LA CONSULTA - ENVIAMOS TODOS LOS ARCHIVOS**
            # relevant_filenames = analyze_query(prompt, st.session_state.database_files) # REMOVE THIS LINE
            # relevant_database_data = {filename: st.session_state.database_files[filename] for filename in relevant_filenames} # REMOVE THIS LINE

            # Construir el prompt completo - AHORA CON TODOS LOS ARCHIVOS
            prompt_completo = create_prompt(st.session_state.database_files, st.session_state.uploaded_files_content, prompt) # MODIFICADO

            with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
                message_placeholder = st.empty()
                full_response = ""
                is_typing = True  # Indicar que el asistente está "escribiendo"
                typing_placeholder = st.empty()
                typing_placeholder.markdown('<div class="assistant-typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>', unsafe_allow_html=True)

                try:
                    response = model.generate_content(prompt_completo, stream=True) # Capture the response object

                    # Add summary and detailed response structure
                    summary_finished = False
                    detailed_response = ""
                    full_response_chunks = []

                    for chunk in response: # Iterate over the response object
                        chunk_text = chunk.text or ""
                        full_response_chunks.append(chunk_text)
                        full_response = "".join(full_response_chunks)


                        if not summary_finished:
                            # Basic heuristic to detect summary end (can be improved)
                            if "\nDesarrollo:" in full_response:
                                summary_finished = True
                                message_placeholder.markdown(full_response + "▌") # Show both summary and start of development
                            else:
                                message_placeholder.markdown(full_response + "▌") # Still in summary part
                        else: # After summary, just append
                             message_placeholder.markdown(full_response + "▌")

                        time.sleep(0.015)  # Slightly faster


                    if not response.candidates: # Check if candidates is empty AFTER stream completion
                        full_response = """
                        Lo siento, no pude generar una respuesta adecuada para tu pregunta con la información disponible.
                        **Posibles razones:**
                        * La pregunta podría ser demasiado compleja o específica.
                        * La información necesaria para responder podría no estar en la base de datos actual o en los archivos adjuntos.
                        * Limitaciones del modelo de IA.

                        **¿Qué puedes intentar?**
                        * **Reformula tu pregunta:**  Intenta hacerla más simple o más directa.
                        * **Proporciona más detalles:**  Añade contexto o información clave a tu pregunta.
                        * **Carga archivos adicionales:**  Si tienes documentos relevantes, adjúntalos para ampliar la base de conocimiento.
                        * **Consulta fuentes legales adicionales:**  Esta herramienta es un apoyo, pero no reemplaza el asesoramiento de un abogado especializado.
                        """
                        st.error("No se pudo generar una respuesta válida. Consulta la sección de ayuda en el mensaje del asistente.", icon="⚠️")

                    typing_placeholder.empty()  # Eliminar "escribiendo..." al finalizar
                    is_typing = False
                    message_placeholder.markdown(full_response)


                except Exception as e:
                    typing_placeholder.empty()
                    is_typing = False
                    st.error(f"Ocurrió un error inesperado al generar la respuesta: {e}. Por favor, intenta de nuevo más tarde.", icon="🚨") # More prominent error icon
                    full_response = f"Ocurrió un error inesperado: {e}. Por favor, intenta de nuevo más tarde."

                st.session_state.messages.append({"role": "assistant", "content": full_response})
else: # Disclaimer not accepted, show message instead of chat
    st.warning("Para usar el Asesor Legal Municipal IA, debes aceptar el Disclaimer en la barra lateral.", icon="⚠️")