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
# Bypassing password for this version
if "authentication_successful" not in st.session_state:
    st.session_state.authentication_successful = True
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "password_input" not in st.session_state:
    st.session_state.password_input = "" # Initialize password input
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = "" # Initialize custom API key state

# --- Session state for the assigned API key name ---
if "session_api_key_name" not in st.session_state:
    st.session_state.session_api_key_name = None

# --- Function to get available API keys ---
def get_available_api_keys() -> List[str]:
    """Checks for configured API keys in st.secrets and returns a list of available key names."""
    available_keys = []
    for i in range(1, 15): # Check for up to 15 API keys
        key_name = f"GOOGLE_API_KEY_{i}"
        try:
            secret_value = getattr(st.secrets, key_name, None) or st.secrets.get(key_name, None)
            if secret_value:
                 available_keys.append(key_name)
        except Exception:
             pass
    return available_keys

# --- Initial Screen (Disclaimer Only) ---
if not st.session_state.disclaimer_accepted:
    initial_screen_placeholder = st.empty()
    with initial_screen_placeholder.container():
        st.title("Acceso a Municip.IA")
        st.markdown("---")
        with st.expander("Descargo de Responsabilidad (Leer antes de usar la IA)", expanded=False): # Expanded by default
            st.markdown("""
            **Descargo de Responsabilidad Completo:**

            Este Municip.IA es una herramienta de inteligencia artificial en fase de desarrollo beta. Como tal, es fundamental comprender y aceptar las siguientes condiciones antes de continuar:

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

            # --- API KEY ASSIGNMENT LOGIC ---
            if st.session_state.session_api_key_name is None:
                available_keys = get_available_api_keys()
                if available_keys:
                    st.session_state.session_api_key_name = random.choice(available_keys)
                    print(f"--- SESSION KEY ASSIGNED (Randomly Chosen): {st.session_state.session_api_key_name} ---")
                else:
                    st.session_state.session_api_key_name = None
                    print("--- WARNING: No available API keys in st.secrets to assign to session. ---")

            initial_screen_placeholder.empty()
            st.rerun()

    st.stop()

# --- Configuración de la página ---
st.set_page_config(
    page_title="Municip.IA - Instituto Libertad",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Estilos CSS personalizados (con mejoras visuales y de animación) ---
st.markdown(
    """
    <style>
    /* --- Variables de color --- */
    :root {
        --primary-color: #004488; /* Dark Blue */
        --primary-hover-color: #005cb3; /* Lighter Blue */
        --secondary-bg: #f0f2f6; /* Lighter Gray Background */
        --text-color-primary: #333333; /* Darker Gray Text */
        --text-color-secondary: #666666; /* Medium Gray */
        --accent-color: #CC0000; /* Red Accent */
        --sidebar-bg: #ffffff; /* White Sidebar */
        --sidebar-button-hover: #e9e9f0; /* Light Gray Hover */
        --sidebar-text: #444444; /* Dark Gray Sidebar Text */
        --user-message-bg: #e3f2fd; /* Light Blue User Message */
        --assistant-message-bg: #ffffff; /* White Assistant Message */
        --border-color: #d1d5db; /* Light Gray Border */
        --shadow-light: rgba(0, 0, 0, 0.05);
        --shadow-medium: rgba(0, 0, 0, 0.08);
    }

    body {
        background-color: var(--secondary-bg);
        color: var(--text-color-primary);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; /* Nicer Font */
        overflow-y: scroll;
        opacity: 0;
        animation: fadeIn 0.6s ease-in-out forwards;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* --- Título Principal --- */
    .main-title {
        font-size: 2.9em; /* Slightly larger */
        font-weight: 700; /* Bolder */
        margin-bottom: 0.05em;
        color: var(--primary-color);
        text-shadow: 1px 1px 3px var(--shadow-light);
        transition: transform 0.3s ease-out;
    }
    .main-title:hover {
        transform: scale(1.01); /* Subtle hover scale */
    }

    /* --- Subtítulo --- */
    .subtitle {
        font-size: 1.3em;
        color: var(--text-color-secondary);
        margin-bottom: 1.5em;
        opacity: 0;
        animation: slideUp 0.7s ease-out 0.2s forwards; /* Delayed slide up */
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(25px); }
        to { opacity: 0.8; transform: translateY(0); }
    }

    /* --- Barra lateral --- */
    .sidebar .sidebar-content {
        background-color: var(--sidebar-bg);
        padding: 1.5rem;
        border-right: 1px solid var(--border-color); /* Subtle border */
    }

    /* --- Contenedor de Mensajes --- */
    .stChatContainer {
        border-radius: 10px; /* Slightly rounder */
        overflow: hidden;
        box-shadow: 0 5px 15px var(--shadow-medium); /* Enhanced shadow */
        transition: box-shadow 0.35s ease;
        background-color: #ffffff; /* Ensure white background */
        padding: 10px; /* Add padding inside container */
    }
    .stChatContainer:hover {
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }

    /* --- Mensajes del Chat --- */
    .chat-message {
        padding: 0.9em 1.3em;
        border-radius: 18px; /* More rounded */
        margin-bottom: 1.3rem;
        font-size: 1.05rem; /* Slightly larger text */
        line-height: 1.6;
        width: fit-content;
        max-width: 85%; /* Allow slightly wider */
        display: flex;
        flex-direction: column;
        transform: translateY(15px);
        opacity: 0;
        animation: fadeInUp 0.4s ease-out forwards;
        overflow-wrap: break-word;
        box-shadow: 0 2px 5px var(--shadow-light); /* Subtle shadow on messages */
        border: 1px solid transparent; /* Base border */
    }

    @keyframes fadeInUp {
        to { opacity: 1; transform: translateY(0); }
        from { opacity: 0; transform: translateY(15px); }
    }

    .user-message {
        background-color: var(--user-message-bg); /* Light blue */
        color: #191970; /* Darker blue text for contrast */
        align-self: flex-end;
        border-left: 5px solid var(--primary-color); /* Thicker accent border */
        margin-left: auto; /* Ensure alignment */
    }

    .assistant-message {
        background-color: var(--assistant-message-bg);
        color: var(--text-color-primary);
        align-self: flex-start;
        border-left: 5px solid var(--border-color);
        transition: box-shadow 0.3s ease, border-color 0.3s ease;
        margin-right: auto; /* Ensure alignment */
    }
    .assistant-message:hover {
        box-shadow: 0 4px 8px var(--shadow-medium);
        border-left-color: var(--primary-hover-color); /* Highlight border on hover */
    }

    .message-content {
        word-wrap: break-word;
    }

    /* --- Campo de Entrada de Texto --- */
    .stTextInput > div > div > div > input {
        border: 2px solid var(--border-color); /* Thicker border */
        border-radius: 8px; /* Rounder */
        padding: 0.8em 1.1em;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
        font-size: 1rem;
    }
    .stTextInput > div > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 8px rgba(0, 68, 136, 0.3); /* Softer focus shadow */
        outline: none;
    }

    /* --- Botones Principales --- */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 8px; /* Rounder */
        padding: 0.8em 1.6em;
        font-weight: 600; /* Bolder */
        text-transform: none;
        letter-spacing: 0.04em;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.12);
    }
    .stButton > button:hover {
        background-color: var(--primary-hover-color);
        transform: translateY(-2px); /* More lift */
        box-shadow: 0 5px 10px rgba(0, 0, 0, 0.18);
    }
    .stButton > button:focus {
        outline: none;
        box-shadow: 0 0 0 3px rgba(0, 131, 143, 0.3); /* Slightly thicker focus ring */
    }
    /* Remove ripple effect for cleaner look */
    .stButton > button::before {
        content: none;
    }

    /* --- Contenedor del Logo en la Barra Lateral --- */
    .sidebar-logo-container {
        width: 100px; /* Adjusted size */
        height: 100px;
        border-radius: 50%;
        overflow: hidden;
        background-image: url('https://i.postimg.cc/RZpJb6rq/IMG-20250407-WA0009-1.png');
        background-size: cover;
        background-position: center;
        margin: 0 auto 1.5em auto; /* Center horizontally */
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease; /* Added bounce */
        box-shadow: 0 4px 8px var(--shadow-medium);
    }
    .sidebar-logo-container:hover {
        transform: rotate(8deg) scale(1.1); /* More playful hover */
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }

    /* --- Títulos de la Barra Lateral --- */
    .sidebar .st-emotion-cache-10trblm { /* Target sidebar headers more specifically */
        font-weight: 600; /* Bolder */
        margin-bottom: 0.7em;
        color: var(--primary-color); /* Use primary color */
        border-bottom: 2px solid var(--primary-color); /* Thicker border */
        padding-bottom: 0.5em;
        font-size: 1.1em;
    }

    /* --- Botones de la Barra Lateral --- */
    .sidebar .stButton > button {
        background-color: transparent;
        color: var(--sidebar-text);
        border-radius: 6px;
        padding: 0.5em 0.9em;
        font-size: 0.95em;
        font-weight: 500; /* Slightly bolder */
        box-shadow: none;
        width: 100%; /* Make buttons full width */
        text-align: left; /* Align text left */
        transition: background-color 0.25s ease-in-out, transform 0.2s ease-out, color 0.2s ease;
        border: 1px solid transparent;
    }
    .sidebar .stButton > button:hover {
        background-color: var(--sidebar-button-hover);
        transform: translateX(2px);
        color: var(--primary-color); /* Change text color on hover */
        border-color: #d1d5db; /* Add subtle border on hover */
    }
    .sidebar .stButton > button:focus {
        background-color: rgba(0, 68, 136, 0.1); /* Lighter primary focus */
        border-color: var(--primary-color);
    }

    /* --- Separadores --- */
    hr {
        border-top: 1px solid var(--border-color);
        margin: 1.5em 0; /* More spacing */
    }

    /* --- Enlaces en la Barra Lateral --- */
    .sidebar a {
        color: var(--primary-color);
        text-decoration: none;
        font-weight: 500;
        transition: color 0.3s ease, text-decoration 0.3s ease;
    }
    .sidebar a:hover {
        color: var(--primary-hover-color);
        text-decoration: underline;
    }

    /* --- Subtítulos/Labels en la Barra Lateral --- */
     .sidebar .st-emotion-cache-16idsys p { /* Target labels like 'API Key Personalizada' */
        margin-top: 0.8em;
        margin-bottom: 0.3em;
        font-size: 0.9em;
        color: var(--text-color-secondary);
        font-weight: 500;
    }

    /* --- Contenedor de Conversaciones Guardadas --- */
    .sidebar div[data-testid="stVerticalBlock"] > div > div[data-testid="stButton"] { /* Target saved convo buttons */
        transition: background-color 0.2s ease-in-out;
        border-radius: 6px;
        padding: 0.1em 0;
        margin-bottom: 0.1em;
    }
    .sidebar div[data-testid="stVerticalBlock"] > div > div[data-testid="stButton"]:hover {
        background-color: rgba(0, 0, 0, 0.04); /* Slightly darker hover */
    }

    /* --- Icon Buttons (Pin, Delete) --- */
    .sidebar .stButton > button:contains("📌"),
    .sidebar .stButton > button:contains("🗑️") {
        padding: 0.4em 0.6em; /* Adjust padding */
        font-size: 1.1em; /* Make icons slightly larger */
        min-width: auto; /* Allow smaller button size */
        line-height: 1;
    }
    .sidebar .stButton > button:contains("📌"):hover,
    .sidebar .stButton > button:contains("🗑️"):hover {
        background-color: rgba(204, 0, 0, 0.1); /* Reddish hover for delete/pin */
        color: var(--accent-color);
    }


    /* --- Rounded Logo in Main Title --- */
    .stApp > header { display: none; } /* Hide default Streamlit header */
    .main-title-container {
        display: flex;
        align-items: center;
        margin-bottom: 0.5em; /* Adjust spacing */
    }
    .main-logo {
        width: 70px; /* Adjust size */
        height: 70px;
        border-radius: 50%;
        margin-right: 15px; /* Space between logo and title */
        box-shadow: 0 3px 7px var(--shadow-medium);
        transition: transform 0.3s ease;
    }
    .main-logo:hover {
        transform: scale(1.08);
    }

    /* --- Rounded Avatar in Chat Messages --- */
    .stChatMessage img {
        border-radius: 50%;
        width: 40px; /* Standard avatar size */
        height: 40px;
        box-shadow: 0 1px 3px var(--shadow-light);
    }

    /* --- Enhanced Assistant Typing Animation --- */
    .assistant-typing {
        display: flex;
        align-items: center;
        padding: 10px 0; /* Add some padding */
    }
    .typing-dot {
        width: 8px; /* Larger dots */
        height: 8px;
        border-radius: 50%;
        background-color: var(--text-color-secondary);
        margin: 0 4px; /* Adjust spacing */
        opacity: 0.2;
        animation: typing-bounce 1.4s infinite ease-in-out;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    .typing-dot:nth-child(3) { animation-delay: 0s; }

    @keyframes typing-bounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1.0); opacity: 1; }
    }

    /* --- Blinking Cursor for Streaming --- */
    .blinking-cursor {
        display: inline-block;
        width: 8px;
        height: 1.1em; /* Match line height */
        background-color: var(--text-color-primary);
        animation: blink 1s step-end infinite;
        margin-left: 2px;
        vertical-align: bottom;
    }
    @keyframes blink {
        from, to { background-color: transparent; }
        50% { background-color: var(--text-color-primary); }
    }

    /* --- Styling for Expander Headers --- */
    .stExpander > summary {
        font-weight: 500;
        color: var(--primary-color);
    }
    .stExpander > summary:hover {
        background-color: rgba(0, 68, 136, 0.05); /* Subtle hover on expander */
    }

    /* --- Styling for Success/Warning/Error boxes --- */
    .stAlert {
        border-radius: 8px;
        border-left-width: 5px; /* Thicker left border */
        padding: 1em;
    }


    </style>
    """,
    unsafe_allow_html=True,
)


# --- API Key Selection and Configuration (REVISED LOGIC) ---
GOOGLE_API_KEY = None
active_key_source = "Ninguna" # To display in sidebar
model = None # Initialize model to None

# 1. Prioritize Custom API Key
if st.session_state.custom_api_key:
    GOOGLE_API_KEY = st.session_state.custom_api_key
    masked_key = f"{GOOGLE_API_KEY[:4]}...{GOOGLE_API_KEY[-4:]}" if len(GOOGLE_API_KEY) > 8 else GOOGLE_API_KEY
    active_key_source = f"Personalizada ({masked_key})"
    print(f"--- USING CUSTOM API KEY ---")

# 2. Use Session-Assigned Key if no Custom Key and session key exists
elif st.session_state.session_api_key_name:
    try:
        GOOGLE_API_KEY = st.secrets[st.session_state.session_api_key_name]
        active_key_source = f"Sesión ({st.session_state.session_api_key_name})"
        print(f"--- USING SESSION ASSIGNED KEY: {st.session_state.session_api_key_name} ---")
    except KeyError:
        st.error(f"Error: La clave API asignada a la sesión ('{st.session_state.session_api_key_name}') ya no se encuentra en st.secrets. Por favor, recargue la página o contacte al administrador.", icon="🚨")
        active_key_source = "Error - Clave de sesión no encontrada"
        GOOGLE_API_KEY = None
    except Exception as e:
        st.error(f"Error inesperado al obtener la clave API de sesión: {e}", icon="🚨")
        active_key_source = "Error - Lectura clave sesión"
        GOOGLE_API_KEY = None

# 3. Handle case where no key is determined AFTER disclaimer accepted
else:
    active_key_source = "Error - Sin clave asignada"
    GOOGLE_API_KEY = None

# Final check and Configure genai only if a key was successfully determined
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        # Use your specific model name here - MAKE SURE IT MATCHES YOUR KEYS
        model = genai.GenerativeModel('gemini-2.0-flash') # <--- CONFIRM THIS MODEL NAME
        print(f"--- GenAI Configured with key source: {active_key_source} ---")
    except Exception as e:
        st.error(f"Error al configurar Google GenAI con la clave ({active_key_source}): {e}. Verifique la validez de la clave y el nombre del modelo.", icon="🚨")
        active_key_source = f"Error - Configuración fallida ({active_key_source})"
        model = None
        st.stop()
else:
    available_keys_check = get_available_api_keys()
    if not available_keys_check and not st.session_state.custom_api_key:
         st.error("Error crítico: No hay claves API configuradas en st.secrets y no se ha ingresado una clave personalizada. La aplicación no puede funcionar.", icon="🚨")
    else:
         st.error("Error crítico: No se ha podido determinar una clave API válida para esta sesión. Verifique la configuración o intente recargar.", icon="🚨")
    st.stop()


# --- Disclaimer Status Display in Main Chat Area ---
if st.session_state.disclaimer_accepted:
    disclaimer_status_main_expander = st.expander("✅ Disclaimer Aceptado - Clic para revisar o revocar", expanded=False)
    with disclaimer_status_main_expander:
        # st.success("Disclaimer Aceptado. Puede usar Municip.IA.", icon="✅") # Redundant with title
        st.markdown("""
                **Descargo de Responsabilidad Completo:**

                Este Municip.IA es una herramienta de inteligencia artificial en fase de desarrollo beta. Como tal, es fundamental comprender y aceptar las siguientes condiciones antes de continuar:

                1.  **Naturaleza Beta y Posibles Errores:** La herramienta se encuentra en etapa de prueba y aprendizaje. Aunque se ha diseñado para proporcionar información útil y relevante sobre derecho municipal chileno, **puede cometer errores o entregar información incompleta o inexacta.** No debe considerarse infalible ni sustituir el juicio profesional de un abogado especializado.

                2.  **Uso Complementario, No Sustitutivo:**  Este Asesor Legal Virtual está concebido como una **herramienta complementaria a sus propios conocimientos y experiencia como concejal o alcalde.** Su propósito es brindar apoyo y orientación rápida, pero **nunca debe ser la base exclusiva para la toma de decisiones críticas o con consecuencias legales.**

                3.  **Limitación de Responsabilidad:** El **Instituto Libertad no asume ninguna responsabilidad por las decisiones o acciones que usted tome basándose en la información proporcionada por esta herramienta.**  El uso de este Asesor Legal Virtual es bajo su propia responsabilidad y criterio.

                4.  **Asesoría Profesional Especializada:**  Si requiere asesoramiento legal específico y detallado en derecho municipal, **le recomendamos encarecidamente contactar directamente al Instituto Libertad o consultar con un abogado especializado en derecho público y municipal.**  Esta herramienta no reemplaza la necesidad de una asesoría legal profesional cuando sea necesaria.

                5.  **Finalidad de Ayuda y Apoyo:**  Esta herramienta se ofrece como un **recurso de ayuda y apoyo para facilitar su labor en el ámbito municipal**, proporcionando acceso rápido a información y análisis preliminar.

                **En resumen, utilice esta herramienta con precaución, comprendiendo sus limitations y siempre validando la información con fuentes confiables y, cuando sea necesario, con asesoramiento legal profesional.**
                """)
        if st.button("Revocar Disclaimer", key="revocar_disclaimer_main", type="primary"): # Use primary button style
            st.session_state.disclaimer_accepted = False
            st.rerun()

# --- Título principal y Subtítulo con Logo ---
st.markdown(
    """
    <div class="main-title-container">
        <img src="https://i.postimg.cc/RZpJb6rq/IMG-20250407-WA0009-1.png" class="main-logo">
        <div>
            <h1 class="main-title">Municip.IA</h1>
            <p class="subtitle">Tu Asesor Legal IA del Instituto Libertad</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# --- Funciones para cargar y procesar archivos (sin cambios funcionales) ---

script_dir = os.path.dirname(__file__)
DATABASE_DIR = os.path.join(script_dir, "data")

@st.cache_data(show_spinner=False, persist="disk", max_entries=10)
def load_database_files_cached(directory: str) -> Dict[str, str]:
    """Carga y cachea el contenido de todos los archivos .txt en el directorio."""
    file_contents = {}
    if not os.path.exists(directory):
        st.warning(f"Directorio de base de datos no encontrado: {directory}")
        return file_contents

    file_list = sorted([f for f in os.listdir(directory) if f.endswith(".txt")])
    content_hash = hashlib.sha256()
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
                content_hash.update(file_content.encode('utf-8'))
        except Exception as e:
            st.error(f"Error al leer el archivo {filename} para calcular el hash: {e}")
            return {}

    current_hash = content_hash.hexdigest()

    # Check both hash and if data exists in session state (more robust)
    if ("database_cache_key" in st.session_state and
        st.session_state.database_cache_key == current_hash and
        "database_files" in st.session_state and
        st.session_state.database_files):
        # print("--- DEBUG: Using cached database files from session state ---") # Optional debug
        return st.session_state.database_files

    # print("--- DEBUG: Reloading database files into session state ---") # Optional debug
    st.session_state.database_files = {}
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                st.session_state.database_files[filename] = f.read()
        except Exception as e:
            st.error(f"Error al leer el archivo {filename}: {e}")

    st.session_state.database_cache_key = current_hash
    return st.session_state.database_files

def load_file_content(uploaded_file) -> str: # Modified to accept Streamlit UploadedFile object
    """Carga el contenido de un archivo .txt desde un objeto UploadedFile."""
    try:
        if uploaded_file.name.lower().endswith(".txt"):
             # Use BytesIO to handle the uploaded file object
            stringio = BytesIO(uploaded_file.getvalue())
            # Read as string, decoding with utf-8
            string_data = stringio.read().decode("utf-8")
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

def discover_and_load_files(directory: str) -> Dict[str, str]:
    """Descubre y carga todos los archivos .txt en un directorio."""
    file_contents = {}
    if not os.path.exists(directory):
        st.warning(f"Directorio de base de datos no encontrado: {directory}")
        return file_contents

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            try: # Add error handling here too
                with open(filepath, "r", encoding="utf-8") as f:
                    file_contents[filename] = f.read()
            except Exception as e:
                 st.error(f"Error al leer el archivo {filename} durante el descubrimiento: {e}")
    return file_contents


# --- Prompt mejorado (sin cambios funcionales en el texto del prompt) ---
def create_prompt(database_files_content: Dict[str, str], uploaded_data: str, query: str) -> str:
    """Crea el prompt para el modelo, incluyendo información de la base de datos (si aplica) y archivos adjuntos."""
    prompt_parts = [
        "Eres Municip.IA, un asesor legal virtual **altamente proactivo y comprensivo**, especializado en **derecho municipal de Chile**, con un enfoque particular en asistir a alcaldes y concejales. Tu experiencia abarca una amplia gama de temas relacionados con la administración y normativa municipal chilena.",
        "Tu objetivo principal es **entender a fondo la pregunta del usuario, anticipando incluso aspectos legales implícitos o no mencionados explícitamente debido a su posible falta de conocimiento legal especializado.** Debes **responder de manera completa y proactiva, como un verdadero asesor legal**, no solo respondiendo directamente a lo preguntado, sino también **identificando posibles implicaciones jurídicas, figuras legales relevantes y brindando una asesoría integral.**  Siempre **responde directamente a las preguntas del usuario de manera precisa y concisa, citando la fuente legal o normativa** que respalda tu respuesta. **Prioriza el uso de un lenguaje claro y accesible, evitando jerga legal compleja, para que la información sea fácilmente comprensible para concejales y alcaldes, incluso si no tienen formación legal.**",
        "Considera que los usuarios son **alcaldes y concejales que pueden no tener un conocimiento jurídico profundo**. Por lo tanto, **interpreta sus preguntas en un contexto práctico y legal municipal, anticipando sus necesidades de asesoramiento más allá de lo que pregunten literalmente.**",
        "**MANUAL DE CONCEJALES Y CONCEJALAS (USO EXCLUSIVO COMO CONTEXTO GENERAL):**",
        "Se te proporciona un documento extenso sobre derecho municipal chileno y funciones de concejales. **Utiliza este documento ÚNICAMENTE como contexto general y para entender el marco del derecho municipal chileno y las funciones de los concejales.  NO debes citar este manual en tus respuestas, ni mencionar su nombre en absoluto.  Úsalo para comprender mejor las preguntas y para identificar las leyes o normativas relevantes a las que aludir en tus respuestas, basándote en tu entrenamiento legal.**",
        # --- Conditionally add Database Section ---
        "**INFORMACIÓN DE LA BASE DE DATOS (NORMAS LEGALES):**" if database_files_content else ""
    ]

    if database_files_content: # Only include if database_files_content is not empty
        for filename, content in database_files_content.items():
            if filename == "MANUAL DE CONCEJALES Y CONCEJALAS.txt":
                continue
            description = get_file_description(filename)
            prompt_parts.append(f"\n**{description} ({filename.replace('.txt', '')}):**\n{content}\n")
    # Removed the "No se ha cargado..." message here, handled by the conditional title

    prompt_parts.append("**INFORMACIÓN ADICIONAL PROPORCIONADA POR EL USUARIO:**")
    prompt_parts.append(uploaded_data if uploaded_data else "No se proporcionó información adicional.\n")

    # --- Resto del prompt (sin cambios) ---
    prompt_parts.extend([
        "**ANÁLISIS PROACTIVO DE LA PREGUNTA DEL USUARIO:**",
        "**Antes de responder, realiza un análisis profundo de la pregunta del usuario.**  Considera lo siguiente:",
        """
*   **Identifica las palabras clave y conceptos legales** presentes en la pregunta.
*   **Infiere la intención real del usuario.** ¿Qué problema está tratando de resolver? ¿Qué información realmente necesita, más allá de lo que pregunta explícitamente?
*   **Anticipa las posibles implicaciones jurídicas** de la pregunta, incluso si el usuario no las menciona. ¿Qué figuras legales podrían ser relevantes? ¿Qué consecuencias legales podrían derivarse de la situación que plantea?
*   **Considera los aspectos no mencionados por el usuario debido a su posible falta de conocimiento legal.**  ¿Qué otros elementos legales debería tener en cuenta un alcalde o concejal en esta situación, aunque no los haya preguntado?
*   **Piensa en la pregunta desde diferentes ángulos del derecho municipal chileno.** ¿Qué otras normas o principios podrían ser aplicables, incluso indirectamente?
        """,
        "**INSTRUCCIONES PARA RESPONDER COMO ASESOR LEGAL PROACTIVO:**",
        """
*   **Respuesta Integral y Proactiva:**  No te limites a responder la pregunta literal. **Brinda una asesoría completa**, que abarque no solo la respuesta directa, sino también **aspectos legales relacionados, implicaciones jurídicas relevantes y figuras legales importantes, incluso si no fueron preguntadas explícitamente.**
*   **Anticipa Dudas y Problemas:**  **Anticipa posibles dudas o problemas** que el usuario podría tener en relación con su pregunta, y **abórdalos proactivamente en tu respuesta.**
*   **Lenguaje Asesor, No Solo Informativo:**  Utiliza un **tono de asesoramiento**, no solo de información.  **Guía al usuario a través de las implicaciones legales de su pregunta.**
*   **Claridad y Precisión Legal:**  Mantén siempre la **claridad y precisión legal** en tu respuesta, **citando las fuentes normativas correspondientes.**
*   **Estructura Clara y Ordenada:**  Organiza tu respuesta de manera **clara y ordenada**, utilizando **resúmenes, viñetas, listas numeradas y encabezados** para facilitar la comprensión de la asesoría integral.
        """,
        "**IMPORTANTE:** Después de este análisis proactivo, y antes de dar la respuesta detallada, determina si la pregunta se relaciona específicamente con la **base de datos de normas legales**, con la **información adicional proporcionada por el usuario**, o con el **derecho municipal general**, **utilizando tu entrenamiento legal en derecho municipal chileno y este análisis proactivo para entender el trasfondo y las figuras jurídicas involucradas en la pregunta, y así enfocar tu respuesta de la mejor manera.**",
        """
*   **Si la pregunta se relaciona con la base de datos de normas legales:** Utiliza la información de la base de datos como tu principal fuente para responder. **Siempre cita el artículo, sección o norma específica de la base de datos que justifica tu respuesta. Indica claramente en tu respuesta que estás utilizando información de la base de datos y el documento específico.**  Menciona el nombre del documento y la parte pertinente (ej. "Artículo 25 del Reglamento del Concejo Municipal").  **Además, en tu respuesta proactiva, considera si hay otras normas en la base de datos que sean relevantes o complementarias a la pregunta, y menciónalas si es pertinente.**
*   **Si la pregunta se relaciona con la información adicional proporcionada:** Utiliza esa información como tu principal fuente. **Siempre cita la parte específica de la información adicional que justifica tu respuesta (ej. "Según la jurisprudencia adjunta en el archivo 'Sentencia_Rol_1234-2023.txt'"). Indica claramente en tu respuesta que estás utilizando información proporcionada por el usuario y el documento específico.** **En tu respuesta proactiva, analiza si la información adicional abre otras interrogantes legales o se conecta con otros aspectos del derecho municipal, y menciónalos si es relevante.**
*   **Si la pregunta es sobre otros aspectos del derecho municipal chileno:** Utiliza tu conocimiento general en la materia, basado en tu entrenamiento legal. **Siempre cita la norma legal general del derecho municipal chileno que justifica tu respuesta (ej. "Según el artículo 65 de la Ley Orgánica Constitucional de Municipalidades"). Indica claramente en tu respuesta que estás utilizando tu conocimiento general de derecho municipal chileno y la norma general.** **En tu respuesta proactiva, considera el contexto general del derecho municipal chileno para brindar una asesoría más completa, anticipando posibles dudas o implicaciones legales más amplias.**
        """,
        "Esta es una herramienta creada por y para el Instituto Libertad por Aldo Manuel Herrera Hernández.",
        "**Metodología LegalDesign (Adaptada para Asesoría Proactiva):**",
        """
*   **Claridad y Concisión:** Responde de manera directa y al grano en la respuesta inicial resumida. En el desarrollo, sé completo y proactivo, pero evita rodeos innecesarios.
*   **Estructura:** Organiza las respuestas con encabezados, viñetas o listas numeradas para facilitar la lectura y comprensión, especialmente para la asesoría proactiva y los múltiples puntos que puedas abordar.
*   **Visualizaciones (si es posible):** Aunque textual, piensa en cómo la información podría representarse visualmente para mejorar la comprensión de la asesoría integral (por ejemplo, un flujo de proceso mentalmente, o diagramas conceptuales).
*   **Ejemplos:**  Incluye ejemplos prácticos y sencillos para ilustrar los conceptos legales y las implicaciones jurídicas, haciendo la asesoría más concreta y comprensible.
*   **Lenguaje sencillo:** Utiliza un lenguaje accesible para personas sin formación legal especializada, pero manteniendo la precisión legal en todos los aspectos de la asesoría.
        """,
        "**Instrucciones específicas:**",
        """
*   Comienza tus respuestas con un **breve resumen conciso de la respuesta directa en una frase inicial.**
*   Luego, **desarrolla la respuesta de manera completa y detallada**, proporcionando un análisis legal **citando siempre la fuente normativa específica.** **NUNCA CITES EL MANUAL DE DERECHO MUNICIPAL PROPORCIONADO DIRECTAMENTE NI ALUDAS A ÉL POR NINGÚN MEDIO.**
    *   **Prioriza la información de la base de datos de normas legales** cuando la pregunta se refiera específicamente a este documento. **Cita explícitamente el documento y la parte relevante (artículo, sección, etc.).**
    *   **Luego, considera la información adicional proporcionada por el usuario** si es relevante para la pregunta. **Cita explícitamente el documento adjunto y la parte relevante.**
    *   Para preguntas sobre otros temas de derecho municipal chileno, utiliza tu conocimiento general, pero sé conciso y preciso en la respuesta directa inicial. **Cita explícitamente la norma general del derecho municipal chileno.**
    *   **En el "Desarrollo" de la respuesta, sé proactivo y completo en tu asesoría.**  Aborda aspectos legales implícitos, anticipa dudas, ofrece contexto legal más amplio y guía al usuario de manera integral.
*   **Si la pregunta se relaciona con el funcionamiento interno del Concejo Municipal, como sesiones, tablas, puntos, o reglamento interno, y para responder correctamente se necesita información específica sobre reglamentos municipales, indica lo siguiente, basado en tu entrenamiento legal:** "Las normas sobre el funcionamiento interno del concejo municipal, como sesiones, tablas y puntos, se encuentran reguladas principalmente en el Reglamento Interno de cada Concejo Municipal.  Por lo tanto, **las reglas específicas pueden variar significativamente entre municipalidades.**  Mi respuesta se basará en mi entrenamiento en derecho municipal chileno y las normas generales que rigen estas materias, **pero te recomiendo siempre verificar el Reglamento Interno específico de tu municipalidad para obtener detalles precisos.**"  **Si encuentras información relevante en tu entrenamiento legal sobre el tema, proporciona una respuesta basada en él, pero siempre incluyendo la advertencia sobre la variabilidad entre municipalidades, y sé proactivo en mencionar los aspectos generales relevantes, aunque los detalles específicos dependan del reglamento interno.**
*   **Si la información para responder la pregunta no se encuentra en la base de datos de normas legales proporcionada, responde de forma concisa: "Según la información disponible en la base de datos, no puedo responder a esta pregunta."**
*   **Si la información para responder a la pregunta no se encuentra en la información adicional proporcionada, responde de forma concisa: "Según la información adicional proporcionada, no puedo responder a esta pregunta."**
*   **Si la información para responder a la pregunta no se encuentra en tu conocimiento general de derecho municipal chileno, responde de forma concisa: "Según mi conocimiento general de derecho municipal chileno, no puedo responder a esta pregunta."**
*   **IMPORTANTE: SIEMPRE CITA LA FUENTE NORMATIVA EN TUS RESPUESTAS. NUNCA MENCIONES NI CITES DIRECTAMENTE EL MANUAL DE DERECHO MUNICIPAL PROPORCIONADO.**
        """,
        "**Ejemplos de respuestas esperadas (con resumen, desarrollo proactivo y citación - SIN MANUAL, BASADO EN ENTRENAMIENTO LEGAL):**",
        """
*   **Pregunta del Usuario:** "¿Cuáles son las funciones del concejo municipal?"
    *   **Respuesta Esperada:** "Resumen: Las funciones del concejo municipal son normativas, fiscalizadoras y representativas, abarcando la creación de ordenanzas, la supervisión de la gestión municipal y la representación vecinal.
        Desarrollo:  Efectivamente, las funciones del concejo municipal se clasifican en normativas, fiscalizadoras y representativas (Según el artículo 65 de la Ley Orgánica Constitucional de Municipalidades).  En su **función normativa**, el concejo crea las ordenanzas municipales, que son normas de carácter general obligatorias para la comunidad local. En su **función fiscalizadora**, supervisa la gestión del alcalde y la administración municipal, velando por la correcta ejecución del presupuesto y el cumplimiento de la normativa.  En su **función representativa**, el concejo actúa como un canal de comunicación entre la comunidad y la municipalidad, representando los intereses vecinales y canalizando sus inquietudes.  **Es importante destacar que estas funciones son esenciales para el buen gobierno local y el control democrático de la gestión municipal.**  Además de estas funciones principales, el concejo también tiene otras atribuciones específicas, como la aprobación del plan de desarrollo comunal, la participación en la designación de algunos funcionarios municipales y la pronunciación sobre diversas materias de interés local.  **Como concejal, es fundamental conocer y ejercer activamente estas funciones para contribuir al desarrollo y bienestar de la comuna.**"
*   **Pregunta del Usuario:** "¿Qué dice el artículo 25 sobre las citaciones a las sesiones en el Reglamento del Concejo Municipal?"
    *   **Respuesta Esperada:** "Resumen: El artículo 25 del Reglamento del Concejo Municipal establece los plazos y formalidades para las citaciones a sesiones ordinarias y extraordinarias, asegurando la debida notificación a los concejales.
        Desarrollo:  Así es, el artículo 25 del Reglamento del Concejo Municipal detalla los plazos y formalidades que deben seguirse al realizar citaciones tanto para sesiones ordinarias como extraordinarias (Artículo 25 del Reglamento del Concejo Municipal).  Este artículo generalmente establece **plazos mínimos de anticipación para la citación, que suelen ser diferenciados para sesiones ordinarias y extraordinarias, buscando asegurar que los concejales tengan tiempo suficiente para preparar su participación.**  También suele especificar **la forma en que debe realizarse la citación, que comúnmente es por escrito y puede incluir medios electrónicos, para dejar constancia formal de la convocatoria.**  **Es crucial que el secretario municipal y el alcalde se aseguren de cumplir estrictamente con estas formalidades, ya que la omisión o incumplimiento de los requisitos de citación podría viciar la legalidad de la sesión y los acuerdos que en ella se adopten.**  **Como concejal, tienes el derecho a exigir que se cumplan estas formalidades y a impugnar la validez de una sesión si consideras que la citación no fue realizada correctamente.**  Te recomiendo revisar el artículo 25 específico del Reglamento de tu Concejo Municipal, ya que los detalles exactos pueden variar ligeramente entre municipalidades."
*   **Pregunta del Usuario:** (Adjunta un archivo con jurisprudencia sobre transparencia municipal) "¿Cómo se aplica esta jurisprudencia en el concejo?"
    *   **Respuesta Esperada:** "Resumen: La jurisprudencia adjunta establece criterios sobre publicidad y acceso a la información pública municipal, que deben ser estrictamente aplicados en el concejo para garantizar la transparencia y probidad.
        Desarrollo:  Correcto, la jurisprudencia que adjuntas en 'Sentencia_Rol_1234-2023.txt' define criterios importantes sobre la publicidad de las sesiones del concejo y el acceso a la información pública municipal. Estos criterios deben ser considerados para asegurar la transparencia en todas las actuaciones del concejo (Según la jurisprudencia adjunta en el archivo 'Sentencia_Rol_1234-2023.txt').  **Esta jurisprudencia refuerza el principio de transparencia y acceso a la información pública, que es un pilar fundamental de la administración municipal.**  **En la práctica, esto implica que el concejo debe asegurar la publicidad de sus sesiones, actas y documentos, facilitando el acceso a la información a la ciudadanía y evitando cualquier forma de opacidad.**  **Específicamente, la jurisprudencia probablemente detalla aspectos como la publicidad de las tablas de sesiones, la disponibilidad de las actas para consulta pública, la transmisión de las sesiones (si es posible), y los límites al secreto o reserva de información, que deben ser interpretados restrictivamente.**  **Es fundamental que todos los miembros del concejo, el alcalde y los funcionarios municipales conozcan y apliquen estos criterios jurisprudenciales para evitar reclamos por falta de transparencia y asegurar el cumplimiento de la normativa vigente en esta materia.**  Te recomiendo analizar en detalle la jurisprudencia adjunta y, en caso de dudas, consultar con un abogado especializado en derecho administrativo y transparencia."
*   **Pregunta del Usuario:** "¿Cómo se define la tabla de una sesión del concejo municipal?"
    *   **Respuesta Esperada:** "Resumen: La tabla de una sesión del concejo municipal es el listado de temas a tratar en la sesión, fijada por el alcalde, pero su elaboración y fijación pueden tener particularidades según el reglamento interno.
        Desarrollo: Las normas sobre la tabla de sesiones se encuentran en el Reglamento Interno de cada Concejo Municipal, por lo que pueden variar.  Basándome en mi entrenamiento en derecho municipal chileno, la tabla de una sesión se define como el listado de los temas específicos que serán tratados en una sesión del concejo, y su fijación es responsabilidad del alcalde. **Es importante verificar el Reglamento Interno de tu municipalidad, ya que los detalles de este proceso pueden variar entre municipios.**  **Generalmente, el reglamento interno establecerá un procedimiento para la elaboración de la tabla, que puede incluir la participación del secretario municipal, la oficina jurídica u otros departamentos.**  **Aunque la fijación final es del alcalde, el reglamento interno podría establecer plazos para la entrega de propuestas de temas a la tabla por parte de los concejales, o mecanismos para que los concejales puedan solicitar la inclusión de temas.**  **Es crucial conocer el procedimiento específico establecido en el Reglamento Interno de tu municipalidad para la elaboración y fijación de la tabla, ya que esto asegura el correcto funcionamiento de las sesiones y la participación de todos los concejales en la definición de los temas a tratar.**  **Como concejal, tienes el derecho a participar en este proceso y a solicitar información sobre cómo se elabora la tabla y cómo puedes proponer temas para su inclusión.**"
        """,
        "**Historial de conversación:**"
    ])

    # Añadir historial de conversación (sin cambios)
    for msg in st.session_state.messages[:-1]: # Exclude the last message which is the current user prompt
        if msg["role"] == "user":
            prompt_parts.append(f"Usuario: {msg['content']}\n")
        else:
            # Ensure assistant messages are clearly marked, even if they contain errors
            content = msg.get('content', '[Mensaje de asistente vacío]')
            prompt_parts.append(f"Asistente: {content}\n")

    prompt_parts.append(f"**Pregunta actual del usuario:** {query}")

    # Filter out empty strings that might result from conditional logic
    final_prompt_parts = [part for part in prompt_parts if part]

    return "\n".join(final_prompt_parts)

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
    # Use the cached function to load/retrieve data
    st.session_state.database_files = load_database_files_cached(DATABASE_DIR)
    return len(st.session_state.database_files)

# Load database files when the script runs (if disclaimer accepted)
database_files_loaded_count = 0
if st.session_state.disclaimer_accepted:
     database_files_loaded_count = load_database_files_on_startup()

# --- Inicializar el estado de la sesión ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! 👋 Soy Municip.IA, tu asesor legal IA especializado en derecho municipal chileno. Fui creado por el Instituto Libertad para apoyar a alcaldes y concejales. Recuerda que soy una herramienta de apoyo y no reemplazo la asesoría legal profesional. \n\nEstoy listo para analizar tus consultas. ¿En qué puedo ayudarte hoy? (Las respuestas pueden tomar entre 20-50 segundos)"})

if "saved_conversations" not in st.session_state:
    st.session_state.saved_conversations = {}

if "current_conversation_name" not in st.session_state:
    st.session_state.current_conversation_name = "Nueva Conversación"

# --- Funciones de gestión de conversaciones (sin cambios) ---
def save_conversation(name, messages, pinned=False):
    # Ensure name is unique or handle collision (e.g., overwrite or add suffix)
    if name in st.session_state.saved_conversations:
        # Simple overwrite strategy
        pass
    st.session_state.saved_conversations[name] = {"messages": messages, "pinned": pinned}

def delete_conversation(name):
    if name in st.session_state.saved_conversations:
        del st.session_state.saved_conversations[name]

def load_conversation(name):
    if name in st.session_state.saved_conversations:
        # Load messages and set current name
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
    st.header("Gestión del Chat")

    disclaimer_status_expander = st.expander("Estado del Disclaimer", expanded=True)
    with disclaimer_status_expander:
        if st.session_state.disclaimer_accepted:
            st.success("Disclaimer Aceptado", icon="✅")
            if st.button("Revocar Disclaimer", key="revoke_sidebar"):
                st.session_state.disclaimer_accepted = False
                st.rerun()
        else:
            st.warning("Disclaimer No Aceptado", icon="⚠️")
            st.markdown("Debes aceptar el Disclaimer para usar la IA.")

    # --- API Key Status ---
    st.subheader("🔑 Estado API Key")
    if st.session_state.disclaimer_accepted:
        if active_key_source.startswith("Error"):
            st.error(f"Estado: {active_key_source}", icon="🚨")
        elif active_key_source == "Ninguna":
             st.warning("Determinando clave API...", icon="⏳")
        else:
            st.success(f"Usando: {active_key_source}")
            if not st.session_state.custom_api_key and st.session_state.session_api_key_name:
                if st.button("🔄 Asignar Nueva Clave a Sesión", help="Obtiene una nueva clave aleatoria de las disponibles para esta sesión."):
                    available_keys = get_available_api_keys()
                    current_key = st.session_state.session_api_key_name
                    other_keys = [k for k in available_keys if k != current_key]
                    new_key = random.choice(other_keys) if other_keys else random.choice(available_keys) if available_keys else None
                    if new_key:
                         st.session_state.session_api_key_name = new_key
                         st.success(f"Nueva clave asignada ({new_key}). Recargando...", icon="✅")
                         time.sleep(1.5)
                         st.rerun()
                    else:
                         st.error("No hay claves API disponibles para reasignar.")
    else:
        st.info("Esperando aceptación del Disclaimer...")


    st.subheader("⚙️ API Key Personalizada (Opcional)")
    custom_api_key_input = st.text_input("Ingresa tu API Key personalizada:", type="password", value=st.session_state.custom_api_key, help="Usa tu propia Google AI API Key. Tiene prioridad sobre las claves de sesión.")
    if custom_api_key_input != st.session_state.custom_api_key:
        st.session_state.custom_api_key = custom_api_key_input
        st.success("Clave personalizada aplicada. Recargando...", icon="🔧")
        time.sleep(1)
        st.rerun()

    st.subheader("📎 Cargar Datos Adicionales (.txt)")
    uploaded_files = st.file_uploader("Adjuntar archivos de texto", type=["txt"], help="Adjunta archivos .txt para incluirlos en el contexto de la IA.", accept_multiple_files=True, key="file_uploader")

    # Process uploaded files immediately if they exist
    if uploaded_files:
        temp_uploaded_content = ""
        file_names = []
        for uploaded_file in uploaded_files:
            content = load_file_content(uploaded_file) # Use updated function
            if content:
                temp_uploaded_content += f"--- Contenido Archivo: {uploaded_file.name} ---\n{content}\n\n"
                file_names.append(uploaded_file.name)
        if temp_uploaded_content != st.session_state.uploaded_files_content:
            st.session_state.uploaded_files_content = temp_uploaded_content
            st.success(f"Archivos cargados: {', '.join(file_names)}", icon="📄")
            # No rerun needed here, content is stored in session state

    if st.session_state.uploaded_files_content:
        if st.button("Limpiar archivos adicionales", key="clear_uploaded"):
            st.session_state.uploaded_files_content = ""
            # Clear the uploader state by resetting the key
            st.session_state.file_uploader = []
            st.rerun()


    st.subheader("💾 Gestión de Conversaciones")
    new_conversation_name = st.text_input("Título conversación actual:", value=st.session_state.current_conversation_name)
    if new_conversation_name != st.session_state.current_conversation_name:
        st.session_state.current_conversation_name = new_conversation_name

    col1, col2, col3 = st.columns([1,1,0.6]) # Adjust ratios
    with col1:
        if st.button("💾 Guardar", help="Guarda la conversación actual"):
            # Simple save limit - keep last 5 non-pinned
            pinned_count = sum(1 for data in st.session_state.saved_conversations.values() if data['pinned'])
            total_count = len(st.session_state.saved_conversations)
            if total_count >= 5 + pinned_count:
                 unpinned_conversations = {name: data for name, data in st.session_state.saved_conversations.items() if not data['pinned']}
                 if unpinned_conversations:
                     # Find the oldest based on first message timestamp (approximation) or just name
                     # For simplicity, just remove one random unpinned one if limit reached
                     name_to_remove = random.choice(list(unpinned_conversations.keys()))
                     delete_conversation(name_to_remove)
                     st.toast(f"Límite alcanzado, conversación '{name_to_remove}' eliminada.", icon="🗑️")


            # Save a copy to avoid modifying during save
            messages_to_save = list(st.session_state.messages)
            save_conversation(st.session_state.current_conversation_name, messages_to_save, st.session_state.saved_conversations.get(st.session_state.current_conversation_name, {}).get('pinned', False))
            st.success(f"Conversación '{st.session_state.current_conversation_name}' guardada!", icon="💾")
            time.sleep(1) # Give user time to see success message
            # No rerun needed unless you want to refresh the saved list immediately

    with col2:
        if st.button("🧹 Limpiar Chat", help="Borra los mensajes del chat actual"):
            # Keep only the initial assistant message
            st.session_state.messages = [st.session_state.messages[0]]
            st.session_state.current_conversation_name = "Nueva Conversación" # Reset name
            st.success("Chat limpiado.", icon="✨")
            time.sleep(0.5)
            st.rerun()

    with col3:
        is_pinned = st.session_state.saved_conversations.get(st.session_state.current_conversation_name, {}).get('pinned', False)
        pin_icon = "📌" if is_pinned else "📍" # Use different icons for pinned/unpinned
        pin_tooltip = "Quitar Pin" if is_pinned else "Fijar Conversación"
        if st.button(pin_icon, key="pin_button", help=pin_tooltip):
            if st.session_state.current_conversation_name in st.session_state.saved_conversations:
                if is_pinned:
                    unpin_conversation(st.session_state.current_conversation_name)
                    st.toast(f"Conversación '{st.session_state.current_conversation_name}' desfijada.", icon="📍")
                else:
                    pin_conversation(st.session_state.current_conversation_name)
                    st.toast(f"Conversación '{st.session_state.current_conversation_name}' fijada.", icon="📌")
                # No rerun needed, list updates visually on next interaction or manual refresh
            else:
                st.warning("Guarda la conversación antes de fijarla.", icon="⚠️")


    st.subheader("📚 Conversaciones Guardadas")
    # Sort pinned first, then alphabetically
    sorted_convos = sorted(st.session_state.saved_conversations.items(), key=lambda item: (not item[1]['pinned'], item[0]))

    if not sorted_convos:
        st.caption("No hay conversaciones guardadas.")

    for name, data in sorted_convos:
        cols = st.columns([0.75, 0.25]) # Adjust column ratio
        with cols[0]:
            pin_prefix = "📌 " if data['pinned'] else ""
            if st.button(f"{pin_prefix}{name}", key=f"load_{name}", help=f"Cargar '{name}'"):
                load_conversation(name)
                st.rerun()
        with cols[1]:
            if st.button("🗑️", key=f"delete_{name}", help=f"Eliminar '{name}'"):
                delete_conversation(name)
                st.rerun()

    st.markdown("---")
    st.header("ℹ️ Acerca de")
    st.markdown("Municip.IA es un asesor legal virtual desarrollado por **Aldo Manuel Herrera Hernández** para el **Instituto Libertad**, especializado en derecho administrativo y municipal de **Chile**.")
    st.markdown("La información se basa en el conocimiento del modelo y la documentación aportada. **No sustituye el asesoramiento legal profesional.**")
    st.markdown("**Instituto Libertad**")
    st.markdown("[Sitio Web](https://www.institutolibertad.cl) | [Contacto](mailto:comunicaciones@institutolibertad.cl)")

    st.subheader("📊 Datos Cargados")
    db_loaded_msg = f"**Base de Datos:** {database_files_loaded_count} archivo(s) cargado(s)." if database_files_loaded_count else "**Base de Datos:** No cargada."
    st.markdown(db_loaded_msg)

    if st.button("Recargar Base de Datos", key="refresh_db_button", help="Vuelve a cargar los archivos de la carpeta 'data'"):
        count = load_database_files_on_startup()
        st.success(f"Base de datos recargada ({count} archivos).", icon="🔄")
        time.sleep(1)
        # No rerun needed immediately, will be used on next prompt

    if st.session_state.uploaded_files_content:
        # Count files based on the separator used during loading
        uploaded_file_count = st.session_state.uploaded_files_content.count("--- Contenido Archivo:")
        st.markdown(f"**Archivos Adicionales:** {uploaded_file_count} archivo(s) adjunto(s).")
    else:
        st.markdown("**Archivos Adicionales:** Ninguno.")

    if not st.session_state.database_files and not st.session_state.uploaded_files_content:
        st.warning("No hay datos cargados (ni base de datos ni archivos adicionales).", icon="⚠️")


# --- Área de chat ---
if st.session_state.disclaimer_accepted:
    # Display existing messages
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                # Use markdown with custom class for styling
                st.markdown(f'<div class="chat-message user-message"><div class="message-content">{message["content"]}</div></div>', unsafe_allow_html=True)
            else:
                # Use st.chat_message for assistant icon and structure
                with st.chat_message("assistant", avatar="https://i.postimg.cc/K853Hw5Y/IMG-20250407-WA0005-2.png"):
                    # Apply custom class within the chat message structure if needed, or rely on default
                    # Using markdown directly inside for content styling flexibility
                    st.markdown(f'<div class="message-content">{message["content"]}</div>', unsafe_allow_html=True)

    # --- Campo de entrada para el usuario ---
    if prompt := st.chat_input("Escribe tu consulta aquí...", key="chat_input"):
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Immediately display user message using Markdown with custom class
        with st.container():
            st.markdown(f'<div class="chat-message user-message"><div class="message-content">{prompt}</div></div>', unsafe_allow_html=True)

        # Process query and generate assistant response
        with st.container():
            # --- *** MODIFIED LOGIC: Send database only on first user message *** ---
            # Count user messages *before* this current one was added
            user_message_count = sum(1 for msg in st.session_state.messages[:-1] if msg["role"] == "user")

            if user_message_count == 0:
                # This is the first user message in this session/conversation
                database_content_to_send = st.session_state.database_files
                print("--- DEBUG: Sending database content (first user message) ---")
            else:
                # Subsequent user message, send empty dict for database
                database_content_to_send = {}
                print("--- DEBUG: Skipping database content (subsequent message) ---")
            # --- *** END OF MODIFIED LOGIC *** ---

            # Construir el prompt completo
            prompt_completo = create_prompt(
                database_files_content=database_content_to_send, # Use the conditionally determined dict
                uploaded_data=st.session_state.uploaded_files_content,
                query=prompt
            )

            # Display Assistant's turn with typing animation
            with st.chat_message("assistant", avatar="https://i.postimg.cc/K853Hw5Y/IMG-20250407-WA0005-2.png"):
                message_placeholder = st.empty()
                # Show typing animation
                typing_placeholder = st.empty()
                typing_placeholder.markdown('<div class="assistant-typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>', unsafe_allow_html=True)

                full_response = ""
                try:
                    # Use streaming for better UX
                    response_stream = model.generate_content(prompt_completo, stream=True)

                    collected_chunks = []
                    for chunk in response_stream:
                         # Handle potential generation blocks/errors within the stream
                        if not chunk.candidates:
                             # If the stream finishes with no valid candidates (e.g., safety block)
                             if not collected_chunks: # Check if we received *any* text before this
                                 print("--- WARNING: Stream ended with no valid candidates (Safety/Block?) ---")
                                 full_response = """
                                 Lo siento, no puedo generar una respuesta para esta consulta debido a las políticas de seguridad o a la falta de información relevante. Por favor, reformula tu pregunta o consulta fuentes adicionales.
                                 """
                                 st.warning("La respuesta no pudo ser generada (posible bloqueo de seguridad o falta de información).", icon="⚠️")
                             # else: continue processing the text received so far
                             break # Exit the loop if blocked early or finished with no candidates

                        chunk_text = chunk.text or ""
                        collected_chunks.append(chunk_text)
                        full_response = "".join(collected_chunks)

                        # Update placeholder with streaming text and blinking cursor
                        message_placeholder.markdown(full_response + '<span class="blinking-cursor"></span>', unsafe_allow_html=True)
                        time.sleep(0.01) # Small delay for visual streaming effect

                    # Final update without cursor
                    message_placeholder.markdown(full_response)

                    # Handle case where stream completed but produced no text at all
                    if not full_response and not chunk.candidates:
                         full_response = "Lo siento, no pude generar una respuesta. Inténtalo de nuevo o reformula la pregunta."
                         st.error("No se pudo generar una respuesta válida.", icon="⚠️")
                         message_placeholder.markdown(full_response)


                except Exception as e:
                    print(f"--- ERROR during generation: {e} ---") # Log the error
                    st.error(f"Ocurrió un error al generar la respuesta: {e}. Revisa la API Key y la configuración.", icon="🚨")
                    full_response = f"Error: {e}" # Store error in message history

                finally:
                     # Always remove typing animation
                    typing_placeholder.empty()

                # Append final response (or error) to history
                st.session_state.messages.append({"role": "assistant", "content": full_response})

else: # Disclaimer not accepted
    st.warning("Para usar Municip.IA, debes aceptar el Disclaimer.", icon="⚠️")
    st.info("Puedes aceptar el Disclaimer en el panel inicial o en la barra lateral.")