import streamlit as st
import os
from dotenv import load_dotenv
from agent import run_agent

# Load environment variables
load_dotenv()

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
    st.header("⚙️ Settings")

    # API Key input
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your key from console.anthropic.com"
    )

    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key
        st.success("✅ API Key set!")

    st.divider()

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
    uploaded_cv = st.file_uploader("Upload CV (TXT format)", type=["txt"])
    if uploaded_cv:
        cv_text = uploaded_cv.read().decode("utf-8")
        st.session_state.cv_text = cv_text
        st.success("✅ CV uploaded! Ask me to review it.")

    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()

# ─── Session State ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # For Claude API
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # For display
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
    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error("⚠️ Please enter your Anthropic API Key in the sidebar to start chatting!")
        st.stop()

    # If CV was uploaded, prepend it to the message
    full_input = user_input
    if st.session_state.cv_text and "review" in user_input.lower() and "cv" in user_input.lower():
        full_input = f"{user_input}\n\nHere is my CV:\n{st.session_state.cv_text}"

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Add to Claude messages
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
                error_msg = f"❌ Error: {str(e)}\n\nPlease check your API key and try again."
                st.error(error_msg)
