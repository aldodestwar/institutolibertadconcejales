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
    st.session_state.authentication_successful = True # Set to True to bypass password
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "password_input" not in st.session_state:
    st.session_state.password_input = "" # Initialize password input
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = "" # Initialize custom API key state

# --- NEW: Session state for the assigned API key name for this specific session ---
if "session_api_key_name" not in st.session_state:
    st.session_state.session_api_key_name = None # e.g., will store "GOOGLE_API_KEY_3"


# --- Function to get available API keys (no changes needed here) ---
def get_available_api_keys() -> List[str]:
    """Checks for configured API keys in st.secrets and returns a list of available key names."""
    available_keys = []
    # print("--- DEBUGGING st.secrets ---") # Optional debug prints
    # print("Contents of st.secrets:", st.secrets)
    for i in range(1, 15): # Check for up to 15 API keys
        key_name = f"GOOGLE_API_KEY_{i}"
        # Use hasattr for safer checking in case secrets structure changes
        # And check if the key actually has a value
        try:
            # Combine check and access for efficiency
            secret_value = getattr(st.secrets, key_name, None) or st.secrets.get(key_name, None)
            if secret_value: # Ensure it's not empty or None
                 available_keys.append(key_name)
        except Exception: # Catch potential errors during access
             pass # Ignore if key doesn't exist or causes error
    # print("Available keys found by function:", available_keys)
    # print("--- DEBUGGING st.secrets END ---")
    return available_keys


# --- Initial Screen (Password and Disclaimer - Single Step) ---
if not st.session_state.disclaimer_accepted:
    initial_screen_placeholder = st.empty()
    with initial_screen_placeholder.container():
        st.title("Acceso a Municip.IA")
        # Removed password input
        # password = st.text_input("Ingrese la clave de usuario", type="password", value=st.session_state.password_input) # Persist input

        # Removed button for verification and password check
        # if st.button("Verificar Clave"): # Button for verification
        #     if password.lower() == "ilconcejales":
        #         st.session_state.authentication_successful = True
        #     else:
        #         st.session_state.authentication_successful = False
        #         st.error("Clave incorrecta. Intente nuevamente.")

        # Show disclaimer always now, authentication is bypassed
        # if st.session_state.authentication_successful: # Show disclaimer only after correct password
        st.markdown("---") # Separator
        with st.expander("Descargo de Responsabilidad (Leer antes de usar la IA)", expanded=False):
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

            # --- !!! API KEY ASSIGNMENT LOGIC !!! ---
            # Assign a key to the session ONLY if one hasn't been assigned yet for this session
            if st.session_state.session_api_key_name is None:
                available_keys = get_available_api_keys()     # <--- Obtiene la lista de disponibles
                if available_keys:
                    # ---!!! AQUÍ OCURRE LA SELECCIÓN ALEATORIA !!!---
                    st.session_state.session_api_key_name = random.choice(available_keys)
                    # --------------------------------------------------
                    print(f"--- SESSION KEY ASSIGNED (Randomly Chosen): {st.session_state.session_api_key_name} ---") # Debug print
                else:
                    # Handle case where no keys are available in secrets
                    st.session_state.session_api_key_name = None # Keep it None if assignment fails
                    print("--- WARNING: No available API keys in st.secrets to assign to session. ---")
                    # Error will be handled later if no key can be used
            # --- !!! END OF ASSIGNMENT LOGIC !!! ---


            initial_screen_placeholder.empty() # Clear initial screen
            st.rerun() # Re-run to show main app

        # Removed password persistence
        # st.session_state.password_input = password # Update password input for persistence
    st.stop() # Stop execution here if disclaimer not accepted

# --- Configuración de la página ---
st.set_page_config(
    page_title="Municip.IA - Instituto Libertad",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed" # Changed to "collapsed"
)

# --- Estilos CSS personalizados ---
st.markdown(
    """
    <style>
    /* Ocultar el logo de GitHub */
    .fork-ribbon {
        display: none !important;
    }

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
        background-image: url('https://i.postimg.cc/RZpJb6rq/IMG-20250407-WA0009-1.png')
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


# --- API Key Selection and Configuration (REVISED LOGIC) ---
GOOGLE_API_KEY = None
active_key_source = "Ninguna" # To display in sidebar
model = None # Initialize model to None

# 1. Prioritize Custom API Key
if st.session_state.custom_api_key:
    GOOGLE_API_KEY = st.session_state.custom_api_key
    # Mask the key for display
    masked_key = f"{GOOGLE_API_KEY[:4]}...{GOOGLE_API_KEY[-4:]}" if len(GOOGLE_API_KEY) > 8 else GOOGLE_API_KEY
    active_key_source = f"Personalizada ({masked_key})"
    print(f"--- USING CUSTOM API KEY ---")

# 2. Use Session-Assigned Key if no Custom Key and session key exists
elif st.session_state.session_api_key_name:
    try:
        # Retrieve the actual key value using the name stored in session_state
        GOOGLE_API_KEY = st.secrets[st.session_state.session_api_key_name]
        active_key_source = f"Sesión ({st.session_state.session_api_key_name})" # Show assigned key name
        print(f"--- USING SESSION ASSIGNED KEY: {st.session_state.session_api_key_name} ---")
    except KeyError:
        st.error(f"Error: La clave API asignada a la sesión ('{st.session_state.session_api_key_name}') ya no se encuentra en st.secrets. Por favor, recargue la página o contacte al administrador.", icon="🚨")
        active_key_source = "Error - Clave de sesión no encontrada"
        # Don't stop here yet, let the final check handle it
        GOOGLE_API_KEY = None
    except Exception as e:
        st.error(f"Error inesperado al obtener la clave API de sesión: {e}", icon="🚨")
        active_key_source = "Error - Lectura clave sesión"
        GOOGLE_API_KEY = None

# 3. Handle case where no key is determined AFTER disclaimer accepted
else:
    # This case means disclaimer is accepted, but assignment failed AND no custom key provided.
    active_key_source = "Error - Sin clave asignada"
    GOOGLE_API_KEY = None
    # Error message will be shown in the final check below

# Final check and Configure genai only if a key was successfully determined
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        # Use your specific model name here - MAKE SURE IT MATCHES YOUR KEYS
        model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21') # <--- CONFIRM THIS MODEL NAME
        print(f"--- GenAI Configured with key source: {active_key_source} ---")
    except Exception as e:
        st.error(f"Error al configurar Google GenAI con la clave ({active_key_source}): {e}. Verifique la validez de la clave y el nombre del modelo.", icon="🚨")
        active_key_source = f"Error - Configuración fallida ({active_key_source})"
        model = None # Ensure model is None if config fails
        # Stop execution if configuration fails
        st.stop()
else:
    # If still no API key after disclaimer logic, show error and stop.
    available_keys_check = get_available_api_keys()
    if not available_keys_check and not st.session_state.custom_api_key:
         st.error("Error crítico: No hay claves API configuradas en st.secrets y no se ha ingresado una clave personalizada. La aplicación no puede funcionar.", icon="🚨")
    else:
         st.error("Error crítico: No se ha podido determinar una clave API válida para esta sesión. Verifique la configuración o intente recargar.", icon="🚨")
    st.stop()


# --- Disclaimer Status Display in Main Chat Area ---
if st.session_state.disclaimer_accepted:
    disclaimer_status_main_expander = st.expander("Disclaimer Aceptado - Clic para revisar o revocar", expanded=False)
    with disclaimer_status_main_expander:
        st.success("Disclaimer Aceptado. Puede usar Municip.IA.", icon="✅")
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
        if st.button("Revocar Disclaimer", key="revocar_disclaimer_main"): # Unique key
            st.session_state.disclaimer_accepted = False
            st.rerun()

# --- Título principal y Subtítulo con Logo ---
col_logo, col_title = st.columns([0.1, 0.9]) # Adjust ratios as needed
with col_logo:
    st.image("https://i.postimg.cc/RZpJb6rq/IMG-20250407-WA0009-1.png", width=80) # Adjust width as needed
with col_title:
    st.markdown('<h1 class="main-title">Municip.IA</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Instituto Libertad</p>', unsafe_allow_html=True)


# --- Funciones para cargar y procesar archivos ---

# Usar ruta relativa para la carpeta de datos (más portable)
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
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
                content_hash.update(file_content.encode('utf-8')) # Hash the content, not just filenames
        except Exception as e:
            st.error(f"Error al leer el archivo {filename} para calcular el hash: {e}")
            return {} # Return empty dict on error to avoid using potentially incomplete data

    current_hash = content_hash.hexdigest()

    if "database_cache_key" in st.session_state and st.session_state.database_cache_key == current_hash and st.session_state.database_files:
        return st.session_state.database_files # Return cached data if hash is the same

    st.session_state.database_files = {} # Reset in-memory cache before reloading
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                st.session_state.database_files[filename] = f.read() # Store in session_state cache
        except Exception as e:
            st.error(f"Error al leer el archivo {filename}: {e}")

    st.session_state.database_cache_key = current_hash # Update cache key with content hash
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
        "Eres Municip.IA, un asesor legal virtual **altamente proactivo y comprensivo**, especializado en **derecho municipal de Chile**, con un enfoque particular en asistir a alcaldes y concejales. Tu experiencia abarca una amplia gama de temas relacionados con la administración y normativa municipal chilena.",
        "Tu objetivo principal es **entender a fondo la pregunta del usuario, anticipando incluso aspectos legales implícitos o no mencionados explícitamente debido a su posible falta de conocimiento legal especializado.** Debes **responder de manera completa y proactiva, como un verdadero asesor legal**, no solo respondiendo directamente a lo preguntado, sino también **identificando posibles implicaciones jurídicas, figuras legales relevantes y brindando una asesoría integral.**  Siempre **responde directamente a las preguntas del usuario de manera precisa y concisa, citando la fuente legal o normativa** que respalda tu respuesta. **Prioriza el uso de un lenguaje claro y accesible, evitando jerga legal compleja, para que la información sea fácilmente comprensible para concejales y alcaldes, incluso si no tienen formación legal.**",
        "Considera que los usuarios son **alcaldes y concejales que pueden no tener un conocimiento jurídico profundo**. Por lo tanto, **interpreta sus preguntas en un contexto práctico y legal municipal, anticipando sus necesidades de asesoramiento más allá de lo que pregunten literalmente.**",
        "**MANUAL DE CONCEJALES Y CONCEJALAS (USO EXCLUSIVO COMO CONTEXTO GENERAL):**",
        "Se te proporciona un documento extenso sobre derecho municipal chileno y funciones de concejales. **Utiliza este documento ÚNICAMENTE como contexto general y para entender el marco del derecho municipal chileno y las funciones de los concejales.  NO debes citar este manual en tus respuestas, ni mencionar su nombre en absoluto.  Úsalo para comprender mejor las preguntas y para identificar las leyes o normativas relevantes a las que aludir en tus respuestas, basándote en tu entrenamiento legal.**",
        "**INFORMACIÓN DE LA BASE DE DATOS (NORMAS LEGALES):**" # Modificado el título
    ]

    if database_files_content: # Modificado para usar database_files_content directamente
        for filename, content in database_files_content.items(): # Iterar sobre TODOS los archivos
            if filename == "MANUAL DE CONCEJALES Y CONCEJALAS.txt":
                continue # Exclude manual from this section, it's already handled above
            description = get_file_description(filename)
            # Modified line to remove .txt from filename in prompt
            prompt_parts.append(f"\n**{description} ({filename.replace('.txt', '')}):**\n{content}\n")
    else:
        prompt_parts.append("No se ha cargado información de la base de datos.\n") # Modificado el mensaje

    prompt_parts.append("**INFORMACIÓN ADICIONAL PROPORCIONADA POR EL USUARIO:**")
    prompt_parts.append(uploaded_data if uploaded_data else "No se proporcionó información adicional.\n")

    prompt_parts.extend([ # Usamos extend para añadir múltiples líneas de una vez
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
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! Soy Municip.IA, tu asesor legal IA especializado en derecho municipal. Esta es una herramienta del Instituto Libertad diseñada para guiar en las funciones de alcalde y concejales, sirviendo como apoyo, pero NO como reemplazo del asesoramiento de un abogado especializado en derecho público. Estoy listo para analizar tus consultas. ¿En qué puedo ayudarte hoy? (Considere que las respuestas pueden demorar entre 20 a 50 segundos)"})

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
            st.markdown("Para usar Municip.IA, debes aceptar el Disclaimer.")

    # --- API Key Status (Uses active_key_source determined earlier) ---
    st.subheader("Estado API Key Activa")
    if st.session_state.disclaimer_accepted:
        if active_key_source.startswith("Error"):
            st.error(f"Estado: {active_key_source}", icon="🚨")
        elif active_key_source == "Ninguna": # Should be handled by earlier stop(), but safeguard
             st.warning("Determinando clave API...", icon="⏳")
        else:
            st.success(f"Usando: {active_key_source}", icon="🔑")

            # Button to force re-assign a new random key for the session
            if not st.session_state.custom_api_key and st.session_state.session_api_key_name:
                if st.button("🔄 Asignar Nueva Clave a Sesión"):
                    available_keys = get_available_api_keys()
                    current_key = st.session_state.session_api_key_name
                    other_keys = [k for k in available_keys if k != current_key]

                    if other_keys:
                         new_key = random.choice(other_keys)
                    elif available_keys: # If only one key exists, or only the current one
                         new_key = random.choice(available_keys) # Reassign potentially the same one if only one exists
                    else:
                         new_key = None

                    if new_key:
                         st.session_state.session_api_key_name = new_key
                         st.success(f"Nueva clave asignada ({new_key}). Recargando...", icon="✅")
                         time.sleep(1.5)
                         st.rerun()
                    else:
                         st.error("No hay claves API disponibles para reasignar.")
    else:
        st.info("Esperando aceptación del Disclaimer...")


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
    st.markdown("Este asesor legal virtual fue creado por Aldo Manuel Herrera Hernández para el **Instituto Libertad** y se especializa en asesoramiento en derecho administrativo y municipal de **Chile**.")
    st.markdown("Esta herramienta es desarrollada por el **Instituto Libertad**.")
    st.markdown("La información suministrada se basa en el conocimiento jurídico previo del sistema, incorporando la documentación que usted aporte. Se deja expresa constancia que esta herramienta no sustituye el asesoramiento legal profesional.")
    st.markdown("---")
    st.markdown("**Instituto Libertad**")
    st.markdown("[Sitio Web](https://www.institutolibertad.cl)")
    st.markdown("[Contacto](comunicaciones@institutolibertad.cl)")

    st.subheader("Datos Cargados")
    if st.session_state.database_files:
        st.markdown(f"**Base de Datos:** Se ha cargado información desde {database_files_loaded_count} archivo(s) automáticamente.")
        if st.button("Recargar Base de Datos", key="refresh_db_button"): # Refresh Database Button
            database_files_loaded_count = load_database_files_on_startup()
            st.success("Base de datos recargada.", icon="🔄")
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
                with st.chat_message("assistant", avatar="https://i.postimg.cc/K853Hw5Y/IMG-20250407-WA0005-2.png"): # Moved avatar here
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

            with st.chat_message("assistant", avatar="https://i.postimg.cc/K853Hw5Y/IMG-20250407-WA0005-2.png"):
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
    st.warning("Para usar Municip.IA, debes aceptar el Disclaimer en la barra lateral.", icon="⚠️")