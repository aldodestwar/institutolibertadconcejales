import streamlit as st
import google.generativeai as genai
import os
import time
import requests
from io import BytesIO
from pathlib import Path
from typing import List, Dict
import nltk  # Import nltk for text processing (keyword extraction)
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download necessary NLTK data (run once)
nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)

# --- Configuración de la página ---
st.set_page_config(
    page_title="Asesor Legal Municipal IA - Instituto Libertad",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS personalizados ---
st.markdown(
    """
    <style>
    /* ... (CSS styles - No changes needed, already optimized for UI) ... */
    :root {
        --primary-color: #00838f;
        --primary-hover-color: #00acc1;
        --secondary-bg: #f0f0f0;
        --text-color-primary: #333;
        --text-color-secondary: #555;
        --accent-color: #26a69a;
        --sidebar-bg: #e0f7fa; /* Color de fondo de la barra lateral */
        --sidebar-button-hover: #cce0f5; /* Color de hover de botones de la barra lateral */
        --sidebar-text: #fff; /* Color de texto en la barra lateral */
    }

    body {
        background-color: #f8f9fa; /* Fondo ligeramente más cálido */
        color: var(--text-color-primary);
        font-family: sans-serif;
        overflow-y: scroll; /* Evita saltos de layout */
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
        color: white; /* Texto del título en blanco */
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        transition: transform 0.3s ease-in-out;
    }
    .main-title:hover {
        transform: scale(1.02);
    }

    /* --- Subtítulo con ligera demora en la animación --- */
    .subtitle {
        font-size: 1.2em;
        color: white; /* Texto del subtítulo en blanco */
        margin-bottom: 1.2em;
        opacity: 0;
        animation: slideUp 0.6s ease-out 0.2s forwards; /* Demora de 0.2s */
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 0.7; transform: translateY(0); }
    }

    /* --- Barra lateral --- */
    .sidebar .sidebar-content {
        background-color: var(--sidebar-bg); /* Fondo azul claro */
        padding: 1rem;
    }

    /* --- Contenedor de Mensajes con sombra sutil --- */
    .stChatContainer {
        border-radius: 0.7em;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05); /* Sombra más definida */
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
        width: fit-content; /* Ajuste para el ancho */
        max-width: 80%;
        display: flex;
        flex-direction: column;
        transform: translateY(10px);
        opacity: 0;
        animation: fadeInUp 0.3s ease-out forwards;
        overflow-wrap: break-word; /* Asegura que las palabras largas se rompan */
    }

    @keyframes fadeInUp {
        to { opacity: 1; transform: translateY(0); }
        from { opacity: 0; transform: translateY(10px); } /* Asegura que la animación comience desde abajo */
    }


    .user-message {
        background-color: #e0f7fa;
        color: #004d40;
        align-self: flex-end;
        border-left: 4px solid var(--accent-color);
        box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
    }

    .assistant-message {
        background-color: var(--secondary-bg);
        color: var(--text-color-primary);
        align-self: flex-start;
        border-left: 4px solid #aaa;
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
        border: 1.5px solid #ccc;
        border-radius: 0.5em;
        padding: 0.7em 1em;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput > div > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 5px rgba(var(--primary-color-rgb), 0.5); /* Necesitarías definir --primary-color-rgb */
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
        text-transform: none; /* Sin mayúsculas forzadas */
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
        box-shadow: 0 0 0 2px rgba(0, 131, 143, 0.4);
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
        width: 120px; /* Ligeramente más pequeño */
        height: 120px;
        border-radius: 50%;
        overflow: hidden;
        background-image: url('https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo');
        background-size: cover;
        background-position: center;
        margin-bottom: 1.2em;
        transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1); /* Curva de animación más suave */
    }
    .sidebar-logo-container:hover {
        transform: rotate(5deg) scale(1.05);
    }

    /* --- Títulos de la Barra Lateral --- */
    .sidebar .st-bb {
        font-weight: bold;
        margin-bottom: 0.6em;
        color: var(--text-color-primary);
        border-bottom: 1px solid #eee;
        padding-bottom: 0.4em;
    }

    /* --- Botones de la Barra Lateral (Más sutiles) --- */
    .sidebar .stButton > button {
        background-color: transparent; /* Fondo transparente */
        color: var(--text-color-primary);
        border-radius: 0.4em;
        padding: 0.4em 0.8em;
        font-size: 0.9em;
        font-weight: 400;
        box-shadow: none;
        transition: background-color 0.3s ease-in-out, transform 0.2s ease-out;
    }
    .sidebar .stButton > button:hover {
        background-color: var(--sidebar-button-hover); /* Color de fondo al hacer hover */
        transform: translateX(1px);
    }
    .sidebar .stButton > button:focus {
        background-color: rgba(0, 131, 143, 0.1);
    }

    /* --- Separadores más ligeros --- */
    hr {
        border-top: 1px solid #eee;
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
        background-color: rgba(0, 131, 143, 0.1);
        color: var(--primary-color);
    }
    .sidebar .stButton > button:nth-child(3):hover {
        background-color: rgba(0, 131, 143, 0.2);
    }

    /* --- Animación de "escribiendo..." del asistente --- */
    .assistant-typing {
        display: flex;
        align-items: center;
    }
    .typing-dot {
        width: 0.5em;
        height: 0.5em;
        border-radius: 50%;
        background-color: var(--text-color-secondary);
        margin-right: 0.3em;
        animation: pulse 1.5s infinite ease-in-out;
    }
    .typing-dot:nth-child(2) {
        animation-delay: 0.5s;
    }
    .typing-dot:nth-child(3) {
        animation-delay: 1s;
    }

    @keyframes pulse {
        0% { opacity: 0.4; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.2); }
        100% { opacity: 0.4; transform: scale(0.8); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Título principal y Subtítulo ---
st.markdown('<h1 class="main-title">Asesor Legal Municipal Virtual</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Instituto Libertad</p>', unsafe_allow_html=True)

# --- API Key ---
# --- WARNING: HARDCODING API KEY - FOR TESTING ONLY! ---
# --- DO NOT HARDCODE API KEYS IN PRODUCTION. USE st.secrets! ---
GOOGLE_API_KEY = "AIzaSyB7mSMXiy01z3w8QcD3kWWvZuYjjw5tshE"  # API Key hardcoded for testing!
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

# --- Funciones para cargar y procesar archivos ---

# Usar ruta relativa para la carpeta de datos (más portable)
script_dir = os.path.dirname(__file__)
DATABASE_DIR = os.path.join(script_dir, "data")

# --- Cargar archivos de base de datos y crear índice ---
@st.cache_resource
def load_database_and_create_index_cached(directory: str) -> Dict[str, str]:
    """Carga archivos y crea un índice de keywords para búsqueda rápida."""
    file_contents = discover_and_load_files(directory)
    file_index = create_keyword_index(file_contents)
    return {"file_contents": file_contents, "file_index": file_index}

def load_file_content(filepath: str) -> str:
    """Carga el contenido de un archivo .txt."""
    try:
        if filepath.lower().endswith(".txt"):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        else:
            st.error(f"Tipo de archivo no soportado: {filepath}. Solo se soporta .txt")
            return ""
    except Exception as e:
        st.error(f"Error al leer el archivo {filepath}: {e}")
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
            file_contents[filename] = load_file_content(filepath)
    return file_contents

def create_keyword_index(file_contents: Dict[str, str]) -> Dict[str, List[str]]:
    """Crea un índice de keywords para búsqueda rápida en los documentos."""
    index = {}
    stop_words = set(stopwords.words('spanish')) # Using Spanish stopwords
    for filename, content in file_contents.items():
        tokens = word_tokenize(content.lower())
        keywords = [w for w in tokens if not w in stop_words and w.isalnum()] # Remove stopwords and punctuation
        index[filename] = keywords
    return index

# --- ANALYZE QUERY OPTIMIZADO usando índice ---
def analyze_query(query: str, database_data: Dict) -> List[str]:
    """Analiza la consulta del usuario usando el índice de keywords (OPTIMIZADO)."""
    relevant_files = []
    if not database_data or not database_data["file_index"]: # Check if index is available
        return []

    if "hola" in query.lower() or "saludo" in query.lower():
        return []

    query_keywords = [keyword.lower() for keyword in query.lower().split()]

    for filename, keywords in database_data["file_index"].items(): # Iterate over keywords in index
        filename_lower = filename.lower()

        # Priorizar filename matching (más rápido y relevante)
        if any(keyword in filename_lower for keyword in query_keywords):
            relevant_files.append(filename)
            continue

        # Buscar keywords en el índice en lugar del contenido completo
        if any(keyword in keywords for keyword in query_keywords):
            relevant_files.append(filename)

    return relevant_files

# --- Inicializar el estado para los archivos ---
if "database_data" not in st.session_state:
    st.session_state.database_data = {}
if "uploaded_files_content" not in st.session_state:
    st.session_state.uploaded_files_content = ""

# --- Carga inicial de archivos y creación de índice OPTIMIZADA ---
def load_database_on_startup():
    """Carga la base de datos y crea el índice al inicio usando la función cacheada."""
    st.session_state.database_data = load_database_and_create_index_cached(DATABASE_DIR)
    return len(st.session_state.database_data.get("file_contents", {}))

database_files_loaded_count = load_database_on_startup()


# --- Prompt mejorado --- (SIN CAMBIOS EN EL PROMPT, YA ESTABA OPTIMIZADO EN LA RESPUESTA ANTERIOR)
def create_prompt(relevant_database_data: Dict[str, str], uploaded_data: str, query: str) -> str:
    """Crea el prompt para el modelo, incluyendo solo la información relevante."""
    prompt_parts = [
        "Eres un asesor legal virtual altamente especializado en **derecho municipal de Chile**, con un enfoque particular en asistir a alcaldes y concejales. Tu experiencia abarca una amplia gama de temas relacionados con la administración y normativa municipal chilena.",
        "Tu objetivo principal es **responder directamente a las preguntas del usuario de manera precisa y concisa**, siempre **citando la fuente legal o normativa** que respalda tu respuesta.",
        "**INFORMACIÓN RELEVANTE DE LA BASE DE DATOS:**"
    ]

    if relevant_database_data:
        for filename, content in relevant_database_data.items():
            description = get_file_description(filename)
            prompt_parts.append(f"\n**{description} ({filename}):**\n{content}\n")
    else:
        prompt_parts.append("No se ha cargado información relevante de la base de datos para esta consulta.\n")

    prompt_parts.append("**INFORMACIÓN ADICIONAL PROPORCIONADA POR EL USUARIO:**")
    prompt_parts.append(uploaded_data if uploaded_data else "No se proporcionó información adicional.\n")

    prompt_parts.append("**IMPORTANTE:** Antes de responder, analiza cuidadosamente la pregunta del usuario para determinar si se relaciona específicamente con la **base de datos**, con la **información adicional proporcionada por el usuario**, o con el **derecho municipal general**.")
    prompt_parts.append("""
*   **Si la pregunta se relaciona con la base de datos:** Utiliza la información de la base de datos como tu principal fuente para responder. **Siempre cita el artículo, sección o norma específica de la base de datos que justifica tu respuesta. Indica claramente en tu respuesta que estás utilizando información de la base de datos y el documento específico.**  Menciona el nombre del documento y la parte pertinente (ej. "Artículo 25 del Reglamento del Concejo Municipal").
*   **Si la pregunta se relaciona con la información adicional proporcionada:** Utiliza esa información como tu principal fuente. **Siempre cita la parte específica de la información adicional que justifica tu respuesta (ej. "Según la jurisprudencia adjunta en el archivo 'Sentencia_Rol_1234-2023.txt'"). Indica claramente en tu respuesta que estás utilizando información proporcionada por el usuario y el documento específico.**
*   **Si la pregunta es sobre otros aspectos del derecho municipal chileno:** Utiliza tu conocimiento general en la materia. **Siempre cita la norma legal general del derecho municipal chileno que justifica tu respuesta (ej. "Según el artículo 65 de la Ley Orgánica Constitucional de Municipalidades"). Indica claramente en tu respuesta que estás utilizando tu conocimiento general de derecho municipal chileno y la norma general.**
""")
    prompt_parts.append("Esta es una herramienta creada por y para el Instituto Libertad por Aldo Manuel Herrera Hernández.")
    prompt_parts.append("**Metodología LegalDesign:**")
    prompt_parts.append("""
*   **Claridad y Concisión:** Responde de manera directa y al grano. Evita rodeos innecesarios.
*   **Estructura:** Organiza las respuestas con encabezados, viñetas o listas numeradas para facilitar la lectura y comprensión, especialmente si hay varios puntos en la respuesta.
*   **Visualizaciones (si es posible):** Aunque textual, piensa en cómo la información podría representarse visualmente para mejorar la comprensión (por ejemplo, un flujo de proceso mentalmente).
*   **Ejemplos:**  Si es pertinente, incluye ejemplos prácticos y sencillos para ilustrar los conceptos legales.
*   **Lenguaje sencillo:** Utiliza un lenguaje accesible para personas sin formación legal especializada, pero manteniendo la precisión legal.
""")
    prompt_parts.append("**Instrucciones específicas:**")
    prompt_parts.append("""
*   Comienza tus respuestas **respondiendo directamente a la pregunta del usuario en una frase inicial.**
*   Luego, proporciona un breve análisis legal **citando siempre la fuente normativa específica.**
    *   **Prioriza la información de la base de datos** cuando la pregunta se refiera específicamente a este documento. **Cita explícitamente el documento y la parte relevante (artículo, sección, etc.).**
    *   **Luego, considera la información adicional proporcionada por el usuario** si es relevante para la pregunta. **Cita explícitamente el documento adjunto y la parte relevante.**
    *   Para preguntas sobre otros temas de derecho municipal chileno, utiliza tu conocimiento general, pero sé conciso y preciso. **Cita explícitamente la norma general del derecho municipal chileno.**
*   **Si la información para responder la pregunta no se encuentra en la base de datos proporcionada, responde de forma concisa: "Según la información disponible en la base de datos, no puedo responder a esta pregunta."**
*   **Si la información para responder la pregunta no se encuentra en la información adicional proporcionada, responde de forma concisa: "Según la información adicional proporcionada, no puedo responder a esta pregunta."**
*   **Si la información para responder la pregunta no se encuentra en tu conocimiento general de derecho municipal chileno, responde de forma concisa: "Según mi conocimiento general de derecho municipal chileno, no puedo responder a esta pregunta."**
*   **IMPORTANTE: SIEMPRE CITA LA FUENTE NORMATIVA EN TUS RESPUESTAS.**
""")
    prompt_parts.append("**Ejemplos de respuestas esperadas (con citación):**")
    prompt_parts.append("""
*   **Pregunta del Usuario:** "¿Cuáles son las funciones del concejo municipal?"
    *   **Respuesta Esperada:** "Las funciones del concejo municipal son normativas, fiscalizadoras y representativas (Según el artículo 65 de la Ley Orgánica Constitucional de Municipalidades)."
*   **Pregunta del Usuario:** "¿Qué dice el artículo 25 sobre las citaciones a las sesiones en el Reglamento del Concejo Municipal?"
    *   **Respuesta Esperada:** "El artículo 25 del Reglamento del Concejo Municipal establece los plazos y formalidades para las citaciones a sesiones ordinarias y extraordinarias (Artículo 25 del Reglamento del Concejo Municipal)."
*   **Pregunta del Usuario:** (Adjunta un archivo con jurisprudencia sobre transparencia municipal) "¿Cómo se aplica esta jurisprudencia en el concejo?"
    *   **Respuesta Esperada:** "La jurisprudencia adjunta en 'Sentencia_Rol_1234-2023.txt' establece criterios sobre la publicidad de las sesiones del concejo y el acceso a la información pública municipal, que deben ser considerados para asegurar la transparencia en las actuaciones del concejo (Según la jurisprudencia adjunta en el archivo 'Sentencia_Rol_1234-2023.txt')."
""")
    prompt_parts.append("**Historial de conversación:**")

    # Añadir historial de conversación
    for msg in st.session_state.messages[:-1]:
        if msg["role"] == "user":
            prompt_parts.append(f"Usuario: {msg['content']}\n")
        else:
            prompt_parts.append(f"Asistente: {msg['content']}\n")

    prompt_parts.append(f"**Pregunta actual del usuario:** {query}")

    return "\n".join(prompt_parts)

# --- Inicializar el estado de la sesión ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "¡Hola! Soy tu asesor legal virtual especializado en derecho municipal chileno. **Esta es una herramienta del Instituto Libertad diseñada para guiar en las funciones de alcalde y concejales, sirviendo como apoyo, pero no como reemplazo del asesoramiento de un abogado especializado en derecho público.** Estoy listo para analizar tus consultas. Adjunta cualquier información adicional que desees. ¿En qué puedo ayudarte hoy?"})

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

    st.subheader("Cargar Datos Adicionales")
    uploaded_files = st.file_uploader("Adjuntar archivos adicionales (.txt)", type=["txt"], help="Puedes adjuntar archivos .txt adicionales para que sean considerados en la respuesta.", accept_multiple_files=True)
    if uploaded_files:
        st.session_state.uploaded_files_content = ""
        for uploaded_file in uploaded_files:
            try:
                content = load_file_content(uploaded_file.name) # Pass filename to load_file_content
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
    if st.session_state.database_data.get("file_contents"): # Check if file_contents exists
        st.markdown(f"**Base de Datos:** Se ha cargado información desde {database_files_loaded_count} archivo(s) automáticamente.")
    if st.session_state.uploaded_files_content:
        uploaded_file_count = 0
        if uploaded_files: # Check if uploaded_files is defined to avoid errors on initial load
            uploaded_file_count = len(uploaded_files)
        st.markdown(f"**Archivos Adicionales:** Se ha cargado información desde {uploaded_file_count} archivo(s).") # Updated description to remove PDF
    if not st.session_state.database_data.get("file_contents") and not st.session_state.uploaded_files_content:
        st.warning("No se ha cargado ninguna base de datos del reglamento ni archivos adicionales.")
    elif not st.session_state.database_data.get("file_contents"):
        st.warning("No se ha encontrado o cargado la base de datos del reglamento automáticamente.")

# --- Área de chat ---
for message in st.session_state.messages:
    with st.container():
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message user-message"><div class="message-content">{message["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message"><div class="message-content">{message["content"]}</div></div>', unsafe_allow_html=True)

# --- Campo de entrada para el usuario ---
if prompt := st.chat_input("Escribe tu consulta sobre derecho municipal chileno...", key="chat_input"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Immediately display user message
    with st.container():
        st.markdown(f'<div class="chat-message user-message"><div class="message-content">{prompt}</div></div>', unsafe_allow_html=True)

    # Process query and generate assistant response in a separate container
    with st.container(): # New container for processing and assistant response
        # Analizar la consulta y cargar archivos relevantes
        relevant_filenames = analyze_query(prompt, st.session_state.database_data) # Pass the entire database_data dict
        relevant_database_data = {filename: st.session_state.database_data["file_contents"][filename] for filename in relevant_filenames}

        # Construir el prompt completo
        prompt_completo = create_prompt(relevant_database_data, st.session_state.uploaded_files_content, prompt)

        with st.chat_message("assistant", avatar="https://media.licdn.com/dms/image/v2/C560BAQGtGwxopZ2xDw/company-logo_200_200/company-logo_200_200/0/1663009661966/instituto_libertad_logo?e=2147483647&v=beta&t=0HUEf9MKb_nAq7S1XN76Dce2CVp1xaE_aK5NndktnKo"):
            message_placeholder = st.empty()
            full_response = ""
            is_typing = True  # Indicar que el asistente está "escribiendo"
            typing_placeholder = st.empty()
            typing_placeholder.markdown('<div class="assistant-typing"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>', unsafe_allow_html=True)

            try:
                response = model.generate_content(prompt_completo, stream=True) # Capture the response object
                for chunk in response: # Iterate over the response object
                    full_response += (chunk.text or "")
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.015)  # Ligeramente más rápido
                if not response.candidates: # Check if candidates is empty AFTER stream completion
                    full_response = "Lo siento, no pude generar una respuesta adecuada para tu pregunta.  Puede que la pregunta sea demasiado compleja, o que no tenga suficiente información para responderla correctamente. Por favor, intenta reformular tu pregunta o consulta fuentes legales adicionales."
                    st.error("No se pudo generar una respuesta válida. La consulta podría ser demasiado compleja o no hay información suficiente.", icon="⚠️")

                typing_placeholder.empty()  # Eliminar "escribiendo..." al finalizar
                is_typing = False
                message_placeholder.markdown(full_response)


            except Exception as e:
                typing_placeholder.empty()
                is_typing = False
                st.error(f"Ocurrió un error al generar la respuesta: {e}", icon="🚨") # More prominent error icon
                full_response = f"Ocurrió un error inesperado: {e}. Por favor, intenta de nuevo más tarde."

            st.session_state.messages.append({"role": "assistant", "content": full_response})