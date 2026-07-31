import streamlit as st
import os
import io
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import pypdf
import docx

# Load environment variables dynamically
load_dotenv(override=True)

# Function to locate API key regardless of case
def get_env_api_key():
    for key_name in ["GOOGLE_API_KEY", "Google_API_Key", "GEMINI_API_KEY", "Gemini_API_Key"]:
        val = os.getenv(key_name)
        if val and val.strip():
            return val.strip()
    for env_k, env_v in os.environ.items():
        if env_k.lower() in ["google_api_key", "gemini_api_key"] and env_v.strip():
            return env_v.strip()
    return ""

# Streamlit Page Configuration
st.set_page_config(
    page_title="AI Document & Chat Assistant",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Styling (Clean Light Canvas with Deep Black Text for Maximum Readability)
st.markdown("""
<style>
    /* Global Canvas */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #edf2f7 100%);
        color: #0f172a;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Gradient Banner */
    .header-container {
        background: linear-gradient(90deg, #1e1b4b 0%, #4338ca 50%, #6d28d9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.4rem;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #334155;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    
    /* ALL INPUT FIELDS & TEXT AREAS - Deep Black Text on White Background */
    input, textarea, select, .stTextInput input, .stSelectbox select, div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    /* Chat Input Field Styling */
    div[data-testid="stChatInput"] {
        border: 2px solid #4f46e5 !important;
        border-radius: 14px !important;
        background-color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.15) !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #000000 !important;
        background-color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border-right: 1px solid #334155 !important;
    }
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
    }
    section[data-testid="stSidebar"] .stTextInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Button Aesthetics */
    .stButton > button {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        color: #ffffff !important;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.6rem 1.4rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
    }
    
    /* CHAT MESSAGE CONTAINERS - Crisp White Cards with High-Contrast Deep Black Text */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04) !important;
    }
    
    /* Force all chat text, paragraph, list, bold text to be solid readable dark color */
    div[data-testid="stChatMessage"] p, 
    div[data-testid="stChatMessage"] span, 
    div[data-testid="stChatMessage"] li, 
    div[data-testid="stChatMessage"] h1, 
    div[data-testid="stChatMessage"] h2, 
    div[data-testid="stChatMessage"] h3,
    div[data-testid="stChatMessage"] div {
        color: #0f172a !important;
        font-size: 1.02rem !important;
        line-height: 1.6 !important;
    }
    
    /* Distinguish User vs Assistant Chat Bubbles */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #f1f5f9 !important;
        border-left: 5px solid #4f46e5 !important;
    }
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background-color: #ffffff !important;
        border-left: 5px solid #06b6d4 !important;
    }
    
    /* Inline Code Blocks inside answers */
    div[data-testid="stChatMessage"] code {
        color: #0f172a !important;
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        padding: 3px 6px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    
    /* File badge styling */
    .file-badge {
        background: #e0e7ff;
        border: 1px solid #6366f1;
        color: #3730a3;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin: 4px 6px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to extract text from files
def extract_file_content(uploaded_file):
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext == '.pdf':
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text, "text"
            
        elif ext == '.docx':
            doc = docx.Document(uploaded_file)
            text = "\n".join([p.text for p in doc.paragraphs if p.text])
            return text, "text"
            
        elif ext in ['.txt', '.md', '.py', '.json', '.csv', '.log', '.html', '.css', '.js']:
            text = uploaded_file.read().decode('utf-8', errors='ignore')
            return text, "text"
            
        elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
            image = Image.open(uploaded_file)
            return image, "image"
            
        else:
            return None, "unsupported"
            
    except Exception as e:
        st.error(f"Error processing file {filename}: {str(e)}")
        return None, "error"

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # API Key Handling
    env_api_key = get_env_api_key()
    
    api_key_input = st.text_input(
        "Gemini API Key",
        value=env_api_key,
        type="password",
        help="API Key is automatically loaded from .env or can be pasted here."
    )
    
    # Working Model Selector
    model_option = st.selectbox(
        "Select Gemini Model",
        ["gemini-flash-latest", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"],
        index=0
    )
    
    st.markdown("---")
    
    # Quick Actions
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("### ℹ️ Features")
    st.markdown("""
    - 📄 **PDF & DOCX Parsing**
    - 📝 **Code & Text Files**
    - 🖼️ **Image Vision Analysis**
    - ⚡ **Real-time Answers**
    """)

# Main Header
st.markdown('<div class="header-container">🤖 AI Document & Chat Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload documents or images, ask questions, and get intelligent answers powered by Gemini AI.</div>', unsafe_allow_html=True)

# API Key Validation Notice
active_api_key = api_key_input.strip()
if not active_api_key:
    st.warning("⚠️ **API Key Missing**: Please enter your Gemini API Key in the sidebar or save `GOOGLE_API_KEY` in your `.env` file to start.")
else:
    genai.configure(api_key=active_api_key)

# File Upload Section
with st.container():
    st.markdown("### 📁 Document & File Upload")
    uploaded_files = st.file_uploader(
        "Upload files for analysis (PDF, Word, Text, Code, Images)",
        type=['pdf', 'docx', 'txt', 'md', 'py', 'json', 'csv', 'png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        help="Upload single or multiple files to query their contents."
    )

processed_texts = []
processed_images = []
file_names = []

if uploaded_files:
    for file in uploaded_files:
        content, content_type = extract_file_content(file)
        file_names.append(file.name)
        if content_type == "text" and content:
            processed_texts.append(f"--- START FILE: {file.name} ---\n{content}\n--- END FILE: {file.name} ---")
        elif content_type == "image" and content:
            processed_images.append(content)

    # Show active file badges
    st.markdown("**Attached Files:** " + " ".join([f'<span class="file-badge">📎 {name}</span>' for name in file_names]), unsafe_allow_html=True)

st.markdown("---")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input & Response Generation
if prompt := st.chat_input("Type your question here..."):
    if not active_api_key:
        st.error("Please provide a valid Gemini API Key in the sidebar or .env file to generate answers.")
    else:
        # Add user prompt to display
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare payload for Gemini API
        contents_payload = []
        
        # Combine uploaded text context if present
        context_str = ""
        if processed_texts:
            context_str = "Context from uploaded documents:\n" + "\n\n".join(processed_texts) + "\n\n"
        
        full_user_prompt = f"{context_str}User Question: {prompt}"
        
        contents_payload.append(full_user_prompt)
        
        # Add images if uploaded
        if processed_images:
            contents_payload.extend(processed_images)

        # Generate Assistant Response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                with st.spinner("Thinking & analyzing..."):
                    # Attempt generation with selected model, falling back to gemini-flash-latest if needed
                    models_to_try = [model_option]
                    if "gemini-flash-latest" not in models_to_try:
                        models_to_try.append("gemini-flash-latest")
                        
                    last_exception = None
                    success = False
                    
                    for m_name in models_to_try:
                        try:
                            model = genai.GenerativeModel(m_name)
                            response_stream = model.generate_content(contents_payload, stream=True)
                            
                            for chunk in response_stream:
                                if chunk.text:
                                    full_response += chunk.text
                                    response_placeholder.markdown(full_response + "▌")
                            
                            response_placeholder.markdown(full_response)
                            success = True
                            break
                        except Exception as e:
                            last_exception = e
                            continue
                    
                    if not success and last_exception:
                        raise last_exception

                # Save assistant response to session state
                if full_response:
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                error_msg = f"❌ **Error generating response**: {str(e)}"
                st.error(error_msg)
                st.info("💡 Tip: Verify your API Key in the sidebar or try selecting 'gemini-flash-latest' from the model dropdown.")