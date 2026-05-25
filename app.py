import streamlit as st
import os
import io
from dotenv import load_dotenv
from agent import run_agent
from interview_agent import (
    get_first_question, continue_interview,
    generate_interview_report, extract_score, extract_feedback,
    TOTAL_QUESTIONS
)

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

# ─── Load API Key Automatically ───────────────────────────────────────────────
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# ─── CV Text Extraction ───────────────────────────────────────────────────────
def extract_text_from_file(uploaded_file) -> str:
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

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Remote Job Finder AI",
    page_icon="🌍",
    layout="centered"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header { text-align: center; padding: 1rem 0; }
    .feature-card {
        background: #f0f2f6; border-radius: 10px;
        padding: 0.8rem; margin: 0.3rem 0;
    }
    .score-box {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border-radius: 12px;
        padding: 1rem; text-align: center; margin: 0.5rem 0;
    }
    .progress-bar {
        background: #e0e0e0; border-radius: 10px;
        height: 12px; margin: 0.5rem 0;
    }
    .progress-fill {
        background: linear-gradient(90deg, #667eea, #764ba2);
        height: 12px; border-radius: 10px;
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

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 Job Finder", "🎤 Mock Interview"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — JOB FINDER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # Sidebar
    with st.sidebar:
        st.header("🚀 What I Can Do")
        features = [
            "🔍 Search remote jobs worldwide",
            "📝 Review your CV/Resume",
            "✉️ Write cover letters",
            "💡 Give career advice",
            "🎯 Match jobs to your skills",
            "🎤 Mock Interview practice"
        ]
        for f in features:
            st.markdown(f'<div class="feature-card">{f}</div>', unsafe_allow_html=True)

        st.divider()
        st.header("💬 Quick Start")
        st.markdown("""
        Try saying:
        - *"Find Python developer jobs"*
        - *"I am a graphic designer, 3 years experience"*
        - *"Review my CV"*
        - *"Write a cover letter for Shopify"*
        """)

        st.divider()
        st.header("📄 Upload Your CV")
        uploaded_cv = st.file_uploader(
            "Upload CV (PDF, Word or TXT)",
            type=["pdf", "docx", "txt"]
        )
        if uploaded_cv:
            file_size_mb = uploaded_cv.size / (1024 * 1024)
            if file_size_mb > 10:
                st.error(f"❌ File too large ({file_size_mb:.1f}MB). Max 10MB.")
            else:
                with st.spinner("Reading your CV..."):
                    cv_text = extract_text_from_file(uploaded_cv)
                if cv_text == "DOCX_NOT_SUPPORTED":
                    st.warning("⚠️ Word format not available. Try PDF or TXT.")
                elif cv_text:
                    st.session_state.cv_text = cv_text
                    st.success(f"✅ CV read! ({len(cv_text.split())} words)")
                    with st.expander("👁️ Preview"):
                        st.text(cv_text[:500] + "..." if len(cv_text) > 500 else cv_text)
                else:
                    st.error("❌ Could not read file. Try PDF or TXT.")

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()

    # Session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "cv_text" not in st.session_state:
        st.session_state.cv_text = None

    # Welcome message
    if not st.session_state.chat_history:
        with st.chat_message("assistant"):
            st.markdown("""
👋 **Hi! I'm your Remote Job Finder AI!**

I can help you:
- 🔍 **Find remote jobs** that match your skills
- 📝 **Review your CV** and suggest improvements
- ✉️ **Write cover letters** for specific jobs
- 🎤 **Practice interviews** — go to the Mock Interview tab!

**To get started, tell me:**
- What is your profession or skill set?
- How many years of experience?
- What salary are you looking for?

Let's get you hired! 🚀
            """)

    # Chat history
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    # Chat input
    user_input = st.chat_input("Type here... e.g. 'Find Python developer jobs'", key="job_finder_input")

    if user_input:
        if not os.environ.get("GROQ_API_KEY"):
            st.error("⚠️ Service unavailable. Please try again later.")
            st.stop()

        full_input = user_input
        if st.session_state.cv_text:
            cv_keywords = ["cv", "resume", "review", "check", "improve",
                           "analyze", "analyse", "feedback", "suggest",
                           "look at", "read", "fix", "update", "score",
                           "rate", "help", "better", "profile"]
            if any(w in user_input.lower() for w in cv_keywords):
                full_input = f"{user_input}\n\n[Attached CV/Resume:]\n{st.session_state.cv_text}"

        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "user", "content": full_input})

        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching for the best opportunities..."):
                try:
                    response, pdf_bytes, pdf_filename = run_agent(st.session_state.messages)
                    st.markdown(response)

                    if pdf_bytes:
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            use_container_width=True
                        )

                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.session_state.messages.append({"role": "assistant", "content": response})

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MOCK INTERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    # ── Interview session state ──────────────────────────────────────────────
    if "interview_active"    not in st.session_state: st.session_state.interview_active    = False
    if "interview_job"       not in st.session_state: st.session_state.interview_job       = ""
    if "interview_history"   not in st.session_state: st.session_state.interview_history   = []
    if "interview_messages"  not in st.session_state: st.session_state.interview_messages  = []
    if "interview_q_count"   not in st.session_state: st.session_state.interview_q_count   = 0
    if "interview_scores"    not in st.session_state: st.session_state.interview_scores    = []
    if "interview_qa_pairs"  not in st.session_state: st.session_state.interview_qa_pairs  = []
    if "interview_finished"  not in st.session_state: st.session_state.interview_finished  = False
    if "interview_report"    not in st.session_state: st.session_state.interview_report    = None
    if "interview_pdf"       not in st.session_state: st.session_state.interview_pdf       = None
    if "last_question"       not in st.session_state: st.session_state.last_question       = ""

    # ── START SCREEN ────────────────────────────────────────────────────────
    if not st.session_state.interview_active:
        st.markdown("## 🎤 AI Mock Interview")
        st.markdown("Practice your interview skills with an AI interviewer. Get scored on each answer and receive a detailed report at the end.")

        col1, col2 = st.columns([3, 1])
        with col1:
            job_title = st.text_input(
                "Enter the job you are interviewing for:",
                placeholder="e.g. Python Developer, Graphic Designer, Marketing Manager"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            start_btn = st.button("🚀 Start Interview", use_container_width=True, type="primary")

        if start_btn and job_title:
            if not os.environ.get("GROQ_API_KEY"):
                st.error("⚠️ Service unavailable. Please try again later.")
            else:
                with st.spinner("Preparing your interview..."):
                    first_q = get_first_question(job_title)
                    st.session_state.interview_active   = True
                    st.session_state.interview_job      = job_title
                    st.session_state.interview_q_count  = 1
                    st.session_state.last_question      = first_q
                    st.session_state.interview_history  = [{"role": "assistant", "content": first_q}]
                    st.session_state.interview_messages = [{"role": "assistant", "content": first_q}]
                st.rerun()

        elif start_btn and not job_title:
            st.warning("⚠️ Please enter a job title to start the interview.")

        # Info cards
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 📋 Format\n- 6 questions\n- One at a time\n- Mix of behavioral & technical")
        with c2:
            st.markdown("### 🎯 Scoring\n- Each answer: 0-10\n- Instant feedback\n- Final report")
        with c3:
            st.markdown("### 📥 Output\n- Detailed PDF report\n- Strengths & weaknesses\n- Tips to improve")

    # ── ACTIVE INTERVIEW ────────────────────────────────────────────────────
    else:
        job = st.session_state.interview_job
        q_count = st.session_state.interview_q_count
        scores = st.session_state.interview_scores

        # Progress bar
        progress = min(q_count - 1, TOTAL_QUESTIONS) / TOTAL_QUESTIONS
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.progress(progress, text=f"Question {min(q_count, TOTAL_QUESTIONS)} of {TOTAL_QUESTIONS}")
        with col2:
            st.metric("Avg Score", f"{avg_score}/10" if scores else "—")
        with col3:
            if st.button("🛑 End Interview", use_container_width=True):
                st.session_state.interview_active   = False
                st.session_state.interview_history  = []
                st.session_state.interview_messages = []
                st.session_state.interview_q_count  = 0
                st.session_state.interview_scores   = []
                st.session_state.interview_qa_pairs = []
                st.session_state.interview_finished = False
                st.session_state.interview_report   = None
                st.session_state.interview_pdf      = None
                st.session_state.last_question      = ""
                st.rerun()

        st.markdown(f"**🎯 Interviewing for: {job}**")
        st.divider()

        # Show report if finished
        if st.session_state.interview_finished and st.session_state.interview_report:
            st.success("🎉 Interview Complete! Here is your performance report:")
            st.markdown(st.session_state.interview_report)
            if st.session_state.interview_pdf:
                st.download_button(
                    label="📥 Download Full Report as PDF",
                    data=st.session_state.interview_pdf,
                    file_name=f"interview_report_{job.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            # Chat history
            for msg in st.session_state.interview_history:
                role = msg["role"]
                with st.chat_message(role):
                    content = msg["content"]
                    # Highlight SCORE line
                    if "SCORE:" in content:
                        lines = content.split("\n")
                        for line in lines:
                            if line.startswith("SCORE:"):
                                score_val = line.replace("SCORE:", "").strip()
                                st.markdown(f"**🏆 {line}**")
                            elif line.startswith("FEEDBACK:"):
                                st.markdown(f"💬 {line}")
                            else:
                                if line.strip():
                                    st.markdown(line)
                    else:
                        st.markdown(content)

            # Answer input
            if not st.session_state.interview_finished:
                answer = st.chat_input("Type your answer here...", key="interview_input")

                if answer:
                    if not os.environ.get("GROQ_API_KEY"):
                        st.error("⚠️ Service unavailable.")
                        st.stop()

                    # Show user answer
                    st.session_state.interview_history.append({"role": "user", "content": answer})
                    st.session_state.interview_messages.append({"role": "user", "content": answer})

                    # Store Q&A pair
                    st.session_state.interview_qa_pairs.append({
                        "question": st.session_state.last_question,
                        "answer": answer
                    })

                    with st.spinner("🤔 Evaluating your answer..."):
                        try:
                            response, is_finished = continue_interview(
                                job,
                                st.session_state.interview_messages,
                                st.session_state.interview_q_count
                            )

                            # Extract score and save
                            score = extract_score(response)
                            feedback = extract_feedback(response)
                            if score > 0:
                                st.session_state.interview_scores.append(score)
                                if st.session_state.interview_qa_pairs:
                                    st.session_state.interview_qa_pairs[-1]["score"] = score
                                    st.session_state.interview_qa_pairs[-1]["feedback"] = feedback

                            st.session_state.interview_history.append({"role": "assistant", "content": response})
                            st.session_state.interview_messages.append({"role": "assistant", "content": response})
                            st.session_state.last_question = response
                            st.session_state.interview_q_count += 1

                            if is_finished:
                                st.session_state.interview_finished = True

                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                    st.rerun()

            # Generate report when finished
            if st.session_state.interview_finished and not st.session_state.interview_report:
                with st.spinner("📊 Generating your performance report..."):
                    try:
                        report_text, pdf_bytes = generate_interview_report(
                            job, st.session_state.interview_qa_pairs
                        )
                        st.session_state.interview_report = report_text
                        st.session_state.interview_pdf    = pdf_bytes
                    except Exception as e:
                        st.error(f"❌ Report error: {str(e)}")
                st.rerun()
