import streamlit as st
import google.generativeai as genai
import os
import time
# import requests # Not used directly, can be removed if not needed elsewhere
# from io import BytesIO # Not used directly, can be removed if not needed elsewhere
# from pathlib import Path # Not used directly, can be removed if not needed elsewhere
from typing import List, Dict # Keep Dict for type hinting
import hashlib
import random # Import random module

# --- Session State Initialization ---
# Keep existing states
if "authentication_successful" not in st.session_state:
    st.session_state.authentication_successful = True # Set to True to bypass password
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
# if "password_input" not in st.session_state: # Not used anymore
#     st.session_state.password_input = ""
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "saved_conversations" not in st.session_state:
    st.session_state.saved_conversations = {}
if "current_conversation_name" not in st.session_state:
    st.session_state.current_conversation_name = "Nueva Conversación"
if "database_files" not in st.session_state: # Keep original name if used by cache function
    st.session_state.database_files = {}
if "uploaded_files_content" not in st.session_state:
    st.session_state.uploaded_files_content = ""
if "database_cache_key" not in st.session_state: # Keep original name if used by cache function
    st.session_state.database_cache_key = None
if "uploaded_file_names" not in st.session_state: # Add state for uploaded file names display
    st.session_state.uploaded_file_names = []


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

# --- Initial Screen (Disclaimer - Single Step) ---
# --- Incorporate API Key Assignment Here ---
if not st.session_state.disclaimer_accepted:
    initial_screen_placeholder = st.empty()
    with initial_screen_placeholder.container():
        st.title("Acceso a Municip.IA")
        st.markdown("---") # Separator
        with st.expander("Descargo de Responsabilidad (Leer antes de usar la IA)", expanded=True): # Expanded
            st.markdown("""
            **Descargo de Responsabilidad Completo:**
            {Your Disclaimer Text Here}
            """) # Keep your full disclaimer text
        disclaimer_accepted_checkbox = st.checkbox("Acepto los términos y condiciones y comprendo las limitations de esta herramienta.", key="disclaimer_checkbox")

        if disclaimer_accepted_checkbox:
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
            st.rerun() # Re-run to show main app and use the assigned key

    st.stop() # Stop execution here if disclaimer not accepted


# --- Configuración de la página (no changes) ---
st.set_page_config(
    page_title="Municip.IA - Instituto Libertad",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Estilos CSS personalizados (no changes) ---
st.markdown(
    """
    <style>
    /* ... (tu CSS existente va aquí, sin cambios) ... */
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


# --- Disclaimer Status Display in Main Chat Area (no changes needed) ---
if st.session_state.disclaimer_accepted:
    disclaimer_status_main_expander = st.expander("Disclaimer Aceptado - Clic para revisar o revocar", expanded=False)
    with disclaimer_status_main_expander:
        st.success("Disclaimer Aceptado. Puede usar Municip.IA.", icon="✅")
        st.markdown("""
                **Descargo de Responsabilidad Completo:**
                {Your Disclaimer Text Here}
                """) # Keep your full disclaimer text
        if st.button("Revocar Disclaimer", key="revocar_disclaimer_main"):
            st.session_state.disclaimer_accepted = False
            # Optional: Also reset the assigned session key upon revocation?
            st.session_state.session_api_key_name = None
            st.rerun()

# --- Título principal y Subtítulo con Logo (no changes) ---
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("https://i.postimg.cc/RZpJb6rq/IMG-20250407-WA0009-1.png", width=80)
with col_title:
    st.markdown('<h1 class="main-title">Municip.IA</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Instituto Libertad</p>', unsafe_allow_html=True)


# --- Funciones para cargar y procesar archivos ---

# Usar ruta relativa para la carpeta de datos (más portable)
script_dir = os.path.dirname(__file__)
# Handle potential __file__ issues in some deployment environments
try:
    DATABASE_DIR = os.path.join(script_dir, "data")
except NameError: # __file__ might not be defined
    DATABASE_DIR = "data" # Assume 'data' folder in the current working directory
if not os.path.isdir(DATABASE_DIR):
     print(f"WARNING: Database directory '{DATABASE_DIR}' not found. Assuming no database files.")
     # Optionally create it: os.makedirs(DATABASE_DIR, exist_ok=True)

@st.cache_data(show_spinner=False, persist="disk", max_entries=10)
def load_database_files_cached(directory: str) -> Dict[str, str]:
    """Carga y cachea el contenido de todos los archivos .txt en el directorio, invalidando el caché si los archivos cambian según el hash del contenido."""
    file_contents = {}
    if not os.path.exists(directory) or not os.path.isdir(directory): # Check if it's a directory
        st.warning(f"Directorio de base de datos no encontrado o no es un directorio: {directory}")
        return file_contents

    try:
        file_list = sorted([f for f in os.listdir(directory) if f.endswith(".txt") and os.path.isfile(os.path.join(directory, f))])
    except OSError as e:
        st.error(f"Error al listar archivos en el directorio '{directory}': {e}")
        return file_contents # Return empty on directory access error

    if not file_list:
        print(f"No .txt files found in directory: {directory}") # Info message
        # Decide if this should be a warning in the UI
        # st.info(f"No se encontraron archivos .txt en la base de datos ({directory}).")
        return file_contents

    content_hash = hashlib.sha256()
    all_content_for_hash = ""

    # Calculate hash based on content first
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_content = f.read()
                # Add filename and content to hash calculation for more robustness
                all_content_for_hash += filename + file_content
        except Exception as e:
            st.error(f"Error al leer el archivo {filename} para calcular el hash: {e}")
            return {} # Return empty dict on error to avoid using potentially incomplete data

    content_hash.update(all_content_for_hash.encode('utf-8'))
    current_hash = content_hash.hexdigest()

    # Check cache using the combined content hash
    # Use the original session state key name for cache check
    if "database_cache_key" in st.session_state and \
       st.session_state.database_cache_key == current_hash and \
       "database_files" in st.session_state and \
       st.session_state.database_files: # Check original key name
        # print("--- Using cached database files ---") # Debug print
        return st.session_state.database_files # Return original key name

    # print("--- Loading database files (cache miss or invalid) ---") # Debug print
    st.session_state.database_files = {} # Reset original key name before reloading
    for filename in file_list:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                st.session_state.database_files[filename] = f.read() # Store in original key name
        except Exception as e:
            st.error(f"Error al leer el archivo {filename}: {e}")
            # Clear and return empty on error during load
            st.session_state.database_files = {}
            return {}

    st.session_state.database_cache_key = current_hash # Update cache key with content hash
    return st.session_state.database_files


# Modify load_file_content to accept UploadedFile object for clarity
from io import BytesIO # Need BytesIO for uploaded files
def load_file_content(uploaded_file) -> str: # Accept UploadedFile object
    """Carga el contenido de un archivo .txt desde un objeto UploadedFile."""
    content = ""
    if uploaded_file is not None:
        try:
            # Use BytesIO to handle the uploaded file object directly
            stringio = BytesIO(uploaded_file.getvalue())
            # Decode assuming UTF-8, add error handling if needed
            content = stringio.read().decode('utf-8')
        except UnicodeDecodeError:
             try:
                 # Try another common encoding like latin-1
                 stringio.seek(0) # Reset stream position
                 content = stringio.read().decode('latin-1')
                 st.warning(f"Archivo '{uploaded_file.name}' decodificado como latin-1.")
             except Exception as e:
                 st.error(f"Error al decodificar el archivo {uploaded_file.name}: {e}")
                 return ""
        except Exception as e:
            st.error(f"Error al leer el archivo adjunto {uploaded_file.name}: {e}")
            return ""
    return content


def get_file_description(filename: str) -> str:
    """Genera una descripción genérica para un archivo basado en su nombre."""
    name_parts = filename.replace(".txt", "").split("_")
    # Handle potential empty strings after split if filename has consecutive underscores
    name_parts = [part for part in name_parts if part]
    return " ".join(word.capitalize() for word in name_parts) if name_parts else filename


# discover_and_load_files seems unused, can be commented out or removed if not needed
# def discover_and_load_files(directory: str) -> Dict[str, str]:
#     """Descubre y carga todos los archivos .txt en un directorio."""
#     # ... implementation ...


# --- Prompt mejorado MODIFICADO para enviar TODOS los documentos ---
# Pass chat history to the function
def create_prompt(database_files_content: Dict[str, str], uploaded_data: str, query: str, chat_history: List[Dict]) -> str:
    """Crea el prompt para el modelo, incluyendo TODA la información de la base de datos, archivos adjuntos e historial."""
    prompt_parts = [
        "Eres Municip.IA, un asesor legal virtual altamente especializado en **derecho municipal de Chile**, con un enfoque particular en asistir a alcaldes y concejales. Tu experiencia abarca una amplia gama de temas relacionados con la administración y normativa municipal chilena.",
        "Tu objetivo principal es **responder directamente a las preguntas del usuario de manera precisa y concisa**, siempre **citando la fuente legal o normativa** que respalda tu respuesta. **Prioriza el uso de un lenguaje claro y accesible, evitando jerga legal compleja, para que la información sea fácilmente comprensible para concejales y alcaldes, incluso si no tienen formación legal.**",
        "**MANUAL DE CONCEJALES Y CONCEJALAS (USO EXCLUSIVO COMO CONTEXTO GENERAL):**",
        "Se te proporciona un documento extenso sobre derecho municipal chileno y funciones de concejales. **Utiliza este documento ÚNICAMENTE como contexto general y para entender el marco del derecho municipal chileno y las funciones de los concejales.  NO debes citar este manual en tus respuestas, ni mencionar su nombre en absoluto.  Úsalo para comprender mejor las preguntas y para identificar las leyes o normativas relevantes a las que aludir en tus respuestas, basándote en tu entrenamiento legal.**",
        "**INFORMACIÓN DE LA BASE DE DATOS (NORMAS LEGALES):**" # Modificado el título
    ]

    # Include database files content
    if database_files_content: # Use the passed dictionary
        manual_found = False
        for filename, content in database_files_content.items():
            # Case-insensitive check for the manual to avoid including it here
            if filename.upper() == "MANUAL DE CONCEJALES Y CONCEJALAS - 2025 ACHM.TXT":
                manual_found = True
                continue # Skip manual here, handled above
            description = get_file_description(filename)
            # Modified line to remove .txt from filename in prompt
            prompt_parts.append(f"\n**{description} ({filename.replace('.txt', '')}):**\n{content}\n")
        if not manual_found:
            print("Warning: Manual 'MANUAL DE CONCEJALES Y CONCEJALAS - 2025 ACHM.txt' not found in database files.")
    else:
        prompt_parts.append("No se ha cargado información de la base de datos.\n") # Modificado el mensaje

    # Include uploaded files content with markers
    prompt_parts.append("**INFORMACIÓN ADICIONAL PROPORCIONADA POR EL USUARIO (Archivos Adjuntos):**")
    prompt_parts.append(uploaded_data if uploaded_data else "No se proporcionó información adicional.\n")

    # Instructions and methodology... (no changes needed here)
    prompt_parts.extend([
        "**IMPORTANTE:** Antes de responder, analiza cuidadosamente la pregunta del usuario...",
        # ... (resto de las instrucciones y ejemplos SIN CAMBIOS) ...
        """
*   **Si la pregunta se relaciona con la base de datos de normas legales:** ...
*   **Si la pregunta se relaciona con la información adicional proporcionada:** ...
*   **Si la pregunta es sobre otros aspectos del derecho municipal chileno:** ...
        """,
        "Esta es una herramienta creada por y para el Instituto Libertad por Aldo Manuel Herrera Hernández.",
        "**Metodología LegalDesign:**",
        """
*   **Claridad y Concisión:** ...
*   **Estructura:** ...
*   **Visualizaciones (si es posible):** ...
*   **Ejemplos:** ...
*   **Lenguaje sencillo:** ...
        """,
        "**Instrucciones específicas:**",
        """
*   Comienza tus respuestas con un **breve resumen conciso...**
*   Luego, **desarrolla la respuesta de manera completa y detallada...**
    *   **Prioriza la información de la base de datos...**
    *   **Luego, considera la información adicional...**
    *   Para preguntas sobre otros temas de derecho municipal chileno...
*   **Si la pregunta se relaciona con el funcionamiento interno del Concejo Municipal...**
*   **Si la información para responder la pregunta no se encuentra en la base de datos...**
*   **Si la información para responder a la pregunta no se encuentra en la información adicional...**
*   **Si la información para responder la pregunta no se encuentra en tu conocimiento general...**
*   **IMPORTANTE: SIEMPRE CITA LA FUENTE NORMATIVA...**
        """,
        "**Ejemplos de respuestas esperadas...**",
        """
*   **Pregunta del Usuario:** "¿Cuáles son las funciones del concejo municipal?" ...
*   **Pregunta del Usuario:** "¿Qué dice el artículo 25..." ...
*   **Pregunta del Usuario:** (Adjunta un archivo...) ...
*   **Pregunta del Usuario:** "¿Cómo se define la tabla..." ...
        """,
        "**Historial de conversación:**"
    ])

    # Add chat history (excluding the very first assistant message if desired)
    history_limit = 10 # Limit history length to avoid overly long prompts
    # Get last N messages (user+assistant = 2*N turns)
    # Ensure we don't slice beyond the list bounds
    start_index = max(0, len(chat_history) - (history_limit * 2))
    limited_history = chat_history[start_index:]

    for msg in limited_history: # Iterate through the passed history
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        # Basic sanitization (replace potential newlines in content to avoid breaking prompt structure)
        content = msg['content'].replace('\n', ' ')
        prompt_parts.append(f"{role}: {content}\n")

    prompt_parts.append(f"**Pregunta actual del usuario:** {query}")

    return "\n".join(prompt_parts)


# --- Carga inicial de archivos (Usa la función cacheada) ---
def load_database_files_on_startup():
    """Carga todos los archivos de la base de datos al inicio usando la función cacheada."""
    # This will now use the cache correctly and store in st.session_state.database_files
    loaded_files = load_database_files_cached(DATABASE_DIR)
    return len(loaded_files)

database_files_loaded_count = load_database_files_on_startup()


# --- Inicializar el estado de la sesión para mensajes (Asegurar que el mensaje inicial solo se añada una vez) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
# Add initial message only if messages list is truly empty after initialization
if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! Soy Municip.IA, tu asesor legal IA especializado en derecho municipal. Esta es una herramienta del Instituto Libertad diseñada para guiar en las funciones de alcalde y concejales, sirviendo como apoyo, pero NO como reemplazo del asesoramiento de un abogado especializado en derecho público. Estoy listo para analizar tus consultas. ¿En qué puedo ayudarte hoy? (Considere que las respuestas pueden demorar entre 20 a 50 segundos)"})


# --- Funciones de gestión de conversaciones (save, delete, load, pin, unpin - no changes needed) ---
def save_conversation(name, messages, pinned=False):
    # Ensure name is not empty
    if not name or not name.strip():
        st.warning("Por favor, ingrese un nombre para guardar la conversación.")
        return
    # Limit number of saved conversations (optional)
    max_saved = 10 # Example limit
    if len(st.session_state.saved_conversations) >= max_saved and name not in st.session_state.saved_conversations:
        # Try removing the oldest unpinned conversation
        unpinned = {k: v for k, v in st.session_state.saved_conversations.items() if not v.get('pinned', False)}
        if unpinned:
            # Simple approximation of oldest: first key in the dict (insertion order for recent Python)
            try:
                oldest_unpinned_name = next(iter(unpinned))
                delete_conversation(oldest_unpinned_name) # Call delete which might show a message
                st.info(f"Límite alcanzado. Se eliminó: '{oldest_unpinned_name}'")
            except StopIteration: # Should not happen if unpinned is not empty
                 pass
        else:
            st.warning(f"Límite de {max_saved} conversaciones guardadas alcanzado y todas están fijadas. Borre alguna conversación para guardar una nueva.")
            return

    # Save a copy to avoid modifying the original list if needed elsewhere
    st.session_state.saved_conversations[name] = {"messages": list(messages), "pinned": data.get('pinned', False)} # Preserve existing pin status if overwriting
    st.success(f"Conversación '{name}' guardada!", icon="💾")

def delete_conversation(name):
    if name in st.session_state.saved_conversations:
        del st.session_state.saved_conversations[name]
        # Don't show success message here if called internally by save_conversation limit logic
        # st.success(f"Conversación '{name}' eliminada.", icon="🗑️")

def load_conversation(name):
    if name in st.session_state.saved_conversations:
        # Load a copy to prevent modifying the saved state directly
        st.session_state.messages = list(st.session_state.saved_conversations[name]["messages"])
        st.session_state.current_conversation_name = name
        st.success(f"Conversación '{name}' cargada.", icon="📂")

def pin_conversation(name):
    if name in st.session_state.saved_conversations:
        st.session_state.saved_conversations[name]["pinned"] = True

def unpin_conversation(name):
    if name in st.session_state.saved_conversations:
        st.session_state.saved_conversations[name]["pinned"] = False


# --- Barra lateral ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo-container"></div>', unsafe_allow_html=True)
    st.header("Estado y Opciones")

    # --- Disclaimer Status ---
    disclaimer_status_expander = st.expander("Estado del Disclaimer", expanded=False)
    with disclaimer_status_expander:
        if st.session_state.disclaimer_accepted:
            st.success("Disclaimer Aceptado", icon="✅")
        else:
            st.warning("Disclaimer No Aceptado", icon="⚠️")
            st.markdown("Acepta el Disclaimer para usar Municip.IA.")

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


    # --- Custom API Key Input ---
    st.subheader("API Key Personalizada (Opcional)")
    custom_api_key_input = st.text_input("Ingresa tu API Key personalizada:", type="password", value=st.session_state.custom_api_key, help="Si ingresas una clave aquí, se usará en lugar de la clave asignada a la sesión. Borra el campo para volver a usar la clave de sesión.")
    if custom_api_key_input != st.session_state.custom_api_key:
        st.session_state.custom_api_key = custom_api_key_input
        st.rerun() # Rerun to apply the new custom key

    st.markdown("---")

    # --- Cargar Datos Adicionales ---
    st.subheader("Cargar Datos Adicionales")
    uploaded_files = st.file_uploader(
        "Adjuntar archivos adicionales (.txt)",
        type=["txt"],
        help="Puedes adjuntar archivos .txt adicionales (.txt) para que sean considerados en la respuesta.",
        accept_multiple_files=True,
        key="file_uploader" # Add a key for stability
    )

    # Process uploaded files immediately if they change
    # Consolidate uploaded content into a single string
    if uploaded_files:
        new_uploaded_content = ""
        new_file_names = []
        has_changes = False
        # Check if the set of uploaded file names is different from the last stored set
        current_filenames_set = {f.name for f in uploaded_files}
        previous_filenames_set = set(st.session_state.get("uploaded_file_names", []))

        if current_filenames_set != previous_filenames_set:
            has_changes = True
            for uploaded_file in uploaded_files:
                content = load_file_content(uploaded_file)
                if content:
                    new_uploaded_content += f"--- INICIO Archivo: {uploaded_file.name} ---\n"
                    new_uploaded_content += content + "\n"
                    new_uploaded_content += f"--- FIN Archivo: {uploaded_file.name} ---\n\n"
                    new_file_names.append(uploaded_file.name)

            st.session_state.uploaded_files_content = new_uploaded_content
            st.session_state.uploaded_file_names = new_file_names
            st.success(f"{len(new_file_names)} archivo(s) adjunto(s) procesado(s).")
            # Optional: Rerun if you want the chat to immediately reflect the new files
            # st.rerun()

    # Display names of currently loaded uploaded files
    if st.session_state.get("uploaded_file_names"):
        st.markdown("**Archivos adjuntos cargados:**")
        for name in st.session_state["uploaded_file_names"]:
            st.caption(f"- {name}")

    if st.button("Limpiar archivos adjuntos"):
        st.session_state.uploaded_files_content = ""
        st.session_state.uploaded_file_names = []
        # Clear the uploader state by rerunning might be enough,
        # sometimes direct manipulation of widget state is tricky.
        st.rerun()

    st.markdown("---")

    # --- Gestión de Conversaciones ---
    st.header("Historial de Conversaciones")
    new_conversation_name = st.text_input(
        "Título conversación actual:",
        value=st.session_state.current_conversation_name,
        key="conversation_name_input"
        )
    # Update state if input changes
    if new_conversation_name != st.session_state.current_conversation_name:
        st.session_state.current_conversation_name = new_conversation_name

    col1, col2, col3 = st.columns([1,1,0.5])
    with col1:
        if st.button("💾 Guardar", help="Guarda la conversación actual con el título de arriba."):
             current_name_to_save = st.session_state.current_conversation_name # Use name from state
             is_pinned_status = False # Default pin status for new save
             # If overwriting, preserve pinned status
             if current_name_to_save in st.session_state.saved_conversations:
                  is_pinned_status = st.session_state.saved_conversations[current_name_to_save].get('pinned', False)
             save_conversation(current_name_to_save, st.session_state.messages, is_pinned_status)

    with col2:
        if st.button("🗑️ Borrar Chat", help="Limpia el historial del chat actual.", key="clear_chat_sidebar"):
            if st.session_state.messages:
                 # Keep only the first message (initial assistant greeting)
                 st.session_state.messages = [st.session_state.messages[0]]
            else:
                 st.session_state.messages = []
            st.session_state.current_conversation_name = "Nueva Conversación"
            st.rerun()

    with col3:
        # Pinning applies to SAVED conversations. Check if the *current name* exists in saved.
        current_name_check = st.session_state.current_conversation_name
        is_saved = current_name_check in st.session_state.saved_conversations
        if is_saved:
            is_pinned = st.session_state.saved_conversations[current_name_check].get('pinned', False)
            pin_icon = "📌" if is_pinned else "📍"
            pin_tooltip = "Desfijar conversación" if is_pinned else "Fijar conversación"
            if st.button(pin_icon, help=pin_tooltip, key="pin_button"):
                if is_pinned:
                    unpin_conversation(current_name_check)
                else:
                    pin_conversation(current_name_check)
                st.rerun()
        else:
            st.button("📍", help="Guarda la conversación primero para poder fijarla.", key="pin_button_disabled", disabled=True)


    st.subheader("Conversaciones Guardadas")
    saved_sorted = sorted(
        st.session_state.saved_conversations.items(),
        key=lambda item: (not item[1].get('pinned', False), item[0].lower())
    )

    if not saved_sorted:
        st.caption("No hay conversaciones guardadas.")

    for name, data in saved_sorted:
        cols_saved = st.columns([0.8, 0.2]) # Use different variable name
        with cols_saved[0]:
            pin_indicator = "📌 " if data.get('pinned', False) else ""
            if st.button(f"{pin_indicator}{name}", key=f"load_{name}", help=f"Cargar '{name}'"):
                load_conversation(name)
                st.rerun()
        with cols_saved[1]:
            if st.button("🗑️", key=f"delete_{name}", help=f"Eliminar '{name}'"):
                delete_conversation(name) # Delete function handles removal
                st.success(f"Conversación '{name}' eliminada.", icon="🗑️") # Show feedback here
                # If deleting the currently loaded conversation, reset the chat area
                if name == st.session_state.current_conversation_name:
                    st.session_state.messages = [st.session_state.messages[0]] if st.session_state.messages else []
                    st.session_state.current_conversation_name = "Nueva Conversación"
                st.rerun()

    st.markdown("---")

    # --- Acerca de (no changes) ---
    st.header("Acerca de")
    st.markdown("Este asesor legal virtual fue creado por Aldo Manuel Herrera Hernández...")
    st.markdown("[Sitio Web](https://www.institutolibertad.cl)")
    st.markdown("[Contacto](comunicaciones@institutolibertad.cl)")


    st.markdown("---")

    # --- Datos Cargados (Display) ---
    st.subheader("Datos Cargados")
    # Use the original session state variable name consistent with cache function
    db_files = st.session_state.get("database_files", {})
    if db_files:
        st.markdown(f"**Base de Datos:** {len(db_files)} archivo(s) cargado(s).")
        if st.button("Recargar Base de Datos", key="refresh_db_button", help="Limpia el caché y vuelve a cargar los archivos de la base de datos."):
            load_database_files_cached.clear()
            # Clear the session state variables holding the data and hash
            if "database_files" in st.session_state:
                del st.session_state.database_files
            if "database_cache_key" in st.session_state:
                del st.session_state.database_cache_key
            st.success("Caché de base de datos limpiado. Recargando...", icon="🔄")
            time.sleep(1)
            st.rerun()
    else:
         st.info("Base de datos no cargada o vacía.")

    uploaded_file_names_display = st.session_state.get("uploaded_file_names", [])
    if uploaded_file_names_display:
        st.markdown(f"**Archivos Adjuntos:** {len(uploaded_file_names_display)} archivo(s) cargado(s).")
    else:
        st.markdown("**Archivos Adjuntos:** Ninguno cargado.")

    if not db_files and not uploaded_file_names_display:
        st.info("No hay datos cargados (ni base de datos ni adjuntos).")


# --- Área de chat ---
if st.session_state.disclaimer_accepted:
    # Check if the model object exists and was configured successfully
    if not model:
         # Error message already shown during configuration, avoid repetition
         # st.error("La aplicación no puede funcionar...")
         pass # Or display a minimal message if needed
    else:
        # --- Display existing messages ---
        message_container = st.container()
        with message_container:
            # Iterate through a copy in case the list is modified during generation
            for message in list(st.session_state.messages):
                 if message["role"] == "user":
                     with st.chat_message("user"):
                          st.markdown(message["content"])
                 elif message["role"] == "assistant":
                     with st.chat_message("assistant", avatar="https://i.postimg.cc/K853Hw5Y/IMG-20250407-WA0005-2.png"):
                          st.markdown(message["content"])

        # --- User input field ---
        # Use a key for the chat input
        if prompt := st.chat_input("Escribe tu consulta...", key="user_query_input"):
            # Append user message to state
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Clear uploaded files content if desired upon new query? Optional.
            # st.session_state.uploaded_files_content = ""
            # st.session_state.uploaded_file_names = []
            st.rerun() # Display user message immediately

        # --- Generate response if the last message is from the user ---
        # Check messages list is not empty before accessing [-1]
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
             user_prompt = st.session_state.messages[-1]["content"]

             # Show thinking indicator using st.spinner or chat_message context
             with st.chat_message("assistant", avatar="https://i.postimg.cc/K853Hw5Y/IMG-20250407-WA0005-2.png"):
                 message_placeholder = st.empty()
                 # Use spinner for better visual feedback than manual dots
                 with st.spinner("Municip.IA está pensando..."):
                     try:
                         # Pass the relevant chat history
                         # Exclude the latest user prompt itself from history sent to model
                         history_for_prompt = st.session_state.messages[:-1]
                         # Optionally skip initial assistant greeting from history
                         if history_for_prompt and history_for_prompt[0]["content"].startswith("¡Hola! Soy Municip.IA"):
                              history_for_prompt = history_for_prompt[1:]

                         # Construct the full prompt using the updated function
                         prompt_completo = create_prompt(
                             st.session_state.get("database_files", {}), # Use original key name
                             st.session_state.get("uploaded_files_content", ""),
                             user_prompt,
                             history_for_prompt # Pass the history
                         )
                         # print("\n--- PROMPT ENVIADO A GEMINI ---\n", prompt_completo[:1000], "... \n------\n") # DEBUG: Print start of prompt

                         response = model.generate_content(prompt_completo, stream=True)

                         full_response_chunks = []
                         for chunk in response:
                             try:
                                 # Add safety check for chunk content
                                 chunk_text = chunk.text if hasattr(chunk, 'text') else ""
                                 full_response_chunks.append(chunk_text)
                             except ValueError as ve:
                                 print(f"Warning: Error processing chunk value: {ve}")
                                 # Potentially related to finished responses or safety features
                                 # Depending on the exact error, you might break or continue
                                 if "StopCandidate" in str(ve): # Example check
                                     break
                             except Exception as chunk_ex:
                                 print(f"Error processing chunk content: {chunk_ex}")
                                 full_response_chunks.append("[Error parte resp.] ")

                             full_response = "".join(full_response_chunks)
                             message_placeholder.markdown(full_response + "▌")
                             # Adjust sleep for perceived speed vs resource use
                             # time.sleep(0.01) # Slightly faster

                         # Final display after streaming finishes
                         message_placeholder.markdown(full_response)
                         final_response_text = full_response # Store the complete text

                         # Check for safety blocks or completely empty response AFTER streaming
                         try:
                             # Access prompt_feedback after iteration is complete
                             response_metadata = response.prompt_feedback
                             if response_metadata.block_reason:
                                 block_reason_msg = f" (Razón: {response_metadata.block_reason})"
                                 print(f"--- WARNING: Response blocked{block_reason_msg} ---")
                                 final_response_text = f"""
                                 Lo siento, la respuesta fue bloqueada por políticas de seguridad{block_reason_msg}.
                                 Por favor, reformula tu pregunta evitando contenido potencialmente sensible.
                                 """
                                 message_placeholder.warning(final_response_text)
                         except (ValueError, IndexError, AttributeError) as feedback_err:
                              # Handle cases where feedback might not be available or structure differs
                              print(f"Could not access prompt feedback: {feedback_err}")
                              if not final_response_text.strip(): # Check if response is empty anyway
                                   print(f"--- WARNING: Empty response received ---")
                                   final_response_text = """
                                   Lo siento, no pude generar una respuesta adecuada para tu pregunta.
                                   **Posibles razones:**
                                   * La pregunta podría ser demasiado compleja o específica.
                                   * La información necesaria no se encuentra en los datos disponibles.
                                   * Limitaciones del modelo de IA.
                                   **¿Qué puedes intentar?**
                                   * Reformula tu pregunta.
                                   * Proporciona más detalles o contexto.
                                   """
                                   message_placeholder.warning(final_response_text)


                         # Append the final assistant response to session state
                         # Ensure we append even if it was modified (e.g., blocked message)
                         st.session_state.messages.append({"role": "assistant", "content": final_response_text})
                         # Rerun AFTER appending the assistant message to update the display correctly
                         st.rerun()


                     except Exception as e:
                         st.error(f"Ocurrió un error inesperado al generar la respuesta: {e}. Por favor, revisa la consola para más detalles o intenta de nuevo.", icon="🚨")
                         print(f"--- ERROR during generate_content: {type(e).__name__} - {e} ---") # Log detailed error
                         # Append error message to chat history
                         error_message = f"Error al generar respuesta: {type(e).__name__}"
                         st.session_state.messages.append({"role": "assistant", "content": error_message})
                         # Rerun to show the error message and stop further processing for this turn
                         st.rerun()


else: # Disclaimer not accepted
    # Message is handled by the initial screen logic
    pass # No need for a warning here as the initial screen is shown