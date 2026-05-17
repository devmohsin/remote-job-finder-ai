import streamlit as st
import os
import io
from dotenv import load_dotenv
from agent import run_agent
from pdf_generator import generate_pdf

# Safe import for pdfplumber
try:
    import pdfplumber
    PDF_SUPPORTED = True
except ImportError:
    PDF_SUPPORTED = False

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
            if not PDF_SUPPORTED:
                return ""
            file_bytes = io.BytesIO(uploaded_file.read())
            text = ""
            with pdfplumber.open(file_bytes) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
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
        # Check file size (max 10MB)
        file_size_mb = uploaded_cv.size / (1024 * 1024)
        if file_size_mb > 10:
            st.error(f"❌ File too large ({file_size_mb:.1f}MB). Please upload a file under 10MB.")
        else:
            with st.spinner("Reading your CV..."):
                cv_text = extract_text_from_file(uploaded_cv)
            if cv_text == "DOCX_NOT_SUPPORTED":
                st.warning("⚠️ Word format not available. Please upload PDF or TXT.")
            elif cv_text:
                st.session_state.cv_text = cv_text
                st.success(f"✅ CV read successfully! ({len(cv_text.split())} words extracted)")
                with st.expander("👁️ Preview extracted text"):
                    st.text(cv_text[:500] + "..." if len(cv_text) > 500 else cv_text)
            else:
                st.error("❌ Could not read the file. Please try a different PDF or TXT format.")

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

    # If CV was uploaded, always attach it so agent can reference it anytime
    full_input = user_input
    if st.session_state.cv_text:
        cv_keywords = [
            "cv", "resume", "review", "check", "improve", "analyze",
            "analyse", "feedback", "suggest", "look at", "read", "fix",
            "update", "score", "rate", "help", "better", "profile"
        ]
        user_lower = user_input.lower()
        if any(word in user_lower for word in cv_keywords):
            full_input = f"{user_input}\n\n[Attached CV/Resume:]\n{st.session_state.cv_text}"

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

                # ── PDF Download Button ──────────────────────────
                pdf_keywords = [
                    "cover letter", "dear hiring", "cv review",
                    "score", "suggestions", "improvements", "resume review"
                ]
                response_lower = response.lower()
                if any(kw in response_lower for kw in pdf_keywords):
                    # Detect title
                    if "cover letter" in response_lower or "dear hiring" in response_lower:
                        pdf_title = "Cover Letter"
                        file_name = "cover_letter.pdf"
                    else:
                        pdf_title = "CV Review Report"
                        file_name = "cv_review.pdf"

                    try:
                        pdf_bytes = generate_pdf(pdf_title, response)
                        st.download_button(
                            label="📥 Download as PDF",
                            data=pdf_bytes,
                            file_name=file_name,
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception:
                        pass  # Don't break app if PDF generation fails

                # Save to history
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
