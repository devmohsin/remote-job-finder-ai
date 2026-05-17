import streamlit as st
import os
import io
import PyPDF2
from dotenv import load_dotenv
from agent import run_agent

# Safe import for docx
try:
    import docx
    DOCX_SUPPORTED = True
except ImportError:
    DOCX_SUPPORTED = False

# Load environment variables (.env for local, Streamlit secrets for cloud)
load_dotenv()

# ─── CV Text Extraction ───────────────────────────────────────────────────────
def extract_text_from_file(uploaded_file) -> str:
    """Extract text from PDF, DOCX or TXT file"""
    file_type = uploaded_file.name.split(".")[-1].lower()

    try:
        if file_type == "pdf":
            reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()

        elif file_type == "docx":
            if not DOCX_SUPPORTED:
                return "DOCX_NOT_SUPPORTED"
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return text.strip()

        elif file_type == "txt":
            return uploaded_file.read().decode("utf-8").strip()

        else:
            return ""

    except Exception:
        return ""

# ─── Load API Key Automatically (Hidden from users) ───────────────────────────
# Try Streamlit secrets first (cloud), then fall back to .env (local)
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass  # Running locally, key loaded from .env

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Remote Job Finder AI",
    page_icon="🌍",
    layout="centered"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    .feature-card {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.3rem 0;
    }
    .stChatMessage {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🌍 Remote Job Finder AI</h1>
    <p>Your personal AI assistant for finding remote jobs worldwide</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🚀 What I Can Do")
    features = [
        "🔍 Search remote jobs worldwide",
        "📝 Review your CV/Resume",
        "✉️ Write cover letters",
        "💡 Give career advice",
        "🎯 Match jobs to your skills"
    ]
    for f in features:
        st.markdown(f'<div class="feature-card">{f}</div>', unsafe_allow_html=True)

    st.divider()

    st.header("💬 Quick Start")
    st.markdown("""
    Try saying:
    - *"Find Python developer jobs"*
    - *"I am a graphic designer with 3 years experience"*
    - *"Review my CV"*
    - *"Write a cover letter for a marketing role at Shopify"*
    """)

    st.divider()

    # CV Upload
    st.header("📄 Upload Your CV")
    uploaded_cv = st.file_uploader(
        "Upload CV (PDF, Word or TXT)",
        type=["pdf", "docx", "txt"],
        help="Supports PDF, Word (.docx) and plain text files"
    )
    if uploaded_cv:
        with st.spinner("Reading your CV..."):
            cv_text = extract_text_from_file(uploaded_cv)
        if cv_text == "DOCX_NOT_SUPPORTED":
            st.warning("⚠️ Word format not available. Please upload PDF or TXT.")
        elif cv_text:
            st.session_state.cv_text = cv_text
            st.success("✅ CV uploaded! Ask me to review it.")
        else:
            st.error("❌ Could not read the file. Please try PDF or TXT format.")

    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()

# ─── Session State ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "cv_text" not in st.session_state:
    st.session_state.cv_text = None

# ─── Welcome Message ───────────────────────────────────────────────────────────
if not st.session_state.chat_history:
    with st.chat_message("assistant"):
        st.markdown("""
👋 **Hi! I'm your Remote Job Finder AI!**

I can help you:
- 🔍 **Find remote jobs** that match your skills
- 📝 **Review your CV** and suggest improvements
- ✉️ **Write cover letters** for specific jobs
- 💡 **Give advice** on landing remote work

**To get started, tell me:**
- What is your profession or skill set?
- How many years of experience do you have?
- What salary are you looking for?

Let's find your perfect remote job! 🚀
        """)

# ─── Display Chat History ──────────────────────────────────────────────────────
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# ─── Chat Input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("Type your message here... (e.g. 'Find me Python developer jobs')")

if user_input:
    # Check API key is configured (only shown to developer, not users)
    if not os.environ.get("GROQ_API_KEY"):
        st.error("⚠️ Service is currently unavailable. Please try again later.")
        st.stop()

    # If CV was uploaded, prepend it to the message
    full_input = user_input
    if st.session_state.cv_text and "review" in user_input.lower() and "cv" in user_input.lower():
        full_input = f"{user_input}\n\nHere is my CV:\n{st.session_state.cv_text}"

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Add to messages
    st.session_state.messages.append({"role": "user", "content": full_input})

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching for the best opportunities..."):
            try:
                response = run_agent(st.session_state.messages)

                # Display response
                st.markdown(response)

                # Save to history
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
