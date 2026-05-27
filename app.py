import streamlit as st
import os
import io
from dotenv import load_dotenv
from agent import run_agent
from tools import search_remote_jobs
from interview_agent import (
    get_first_question, continue_interview,
    generate_interview_report, extract_score, extract_feedback,
    TOTAL_QUESTIONS
)

# ─── Job Search Intent Detection ──────────────────────────────────────────────
JOB_KEYWORDS = [
    "find", "search", "looking for", "job", "jobs", "work",
    "position", "role", "vacancy", "hiring", "remote job",
    "developer", "designer", "engineer", "manager", "analyst",
    "marketer", "writer", "support", "sales", "recruiter"
]

def detect_job_search(text: str) -> str | None:
    """Return extracted job keywords if user is searching for jobs, else None"""
    text_lower = text.lower()
    if any(kw in text_lower for kw in JOB_KEYWORDS):
        # Extract meaningful keywords — strip filler words
        stopwords = {"find","me","i","a","for","some","please","can","you",
                     "want","need","looking","search","show","get","remote",
                     "job","jobs","work","position","roles","any","good"}
        words = [w for w in text_lower.split() if w not in stopwords]
        return " ".join(words[:5]) if words else text_lower
    return None

def fetch_jobs_context(keywords: str) -> str:
    """Call job API and format results as context string for the agent"""
    result = search_remote_jobs(keywords=keywords, limit=5)
    if not result.get("success") or not result.get("jobs"):
        return f"No jobs found for '{keywords}'. Try different keywords."

    lines = [f"Here are the latest remote jobs for '{keywords}':\n"]
    for i, job in enumerate(result["jobs"], 1):
        lines.append(
            f"{i}. {job['title']} — {job['company']}\n"
            f"   💰 Salary: {job.get('salary','Not specified')}\n"
            f"   📍 Location: {job.get('location','Remote')}\n"
            f"   📅 Posted: {job.get('posted_date','')}\n"
            f"   🔗 Apply: {job.get('url','N/A')}\n"
        )
    return "\n".join(lines)

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

load_dotenv()

# ─── Load API Key ──────────────────────────────────────────────────────────────
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# ─── CV Extractor ─────────────────────────────────────────────────────────────
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
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif file_type == "txt":
            return uploaded_file.read().decode("utf-8").strip()
    except Exception:
        return ""
    return ""

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Remote Job Finder AI", page_icon="🌍", layout="centered")

st.markdown("""
<style>
    .main-header { text-align: center; padding: 0.5rem 0 1rem 0; }
    .feature-card { background:#f0f2f6; border-radius:10px; padding:0.8rem; margin:0.3rem 0; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
defaults = {
    "messages": [], "chat_history": [], "cv_text": None,
    "interview_active": False, "interview_job": "", "interview_history": [],
    "interview_messages": [], "interview_q_count": 0, "interview_scores": [],
    "interview_qa_pairs": [], "interview_finished": False,
    "interview_report": None, "interview_pdf": None, "last_question": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌍 Remote Job Finder AI")

    # Mode selector
    mode = st.radio(
        "Select Mode",
        ["🔍 Job Finder", "🎤 Mock Interview"],
        label_visibility="collapsed"
    )
    st.session_state.mode = mode
    st.divider()

    if mode == "🔍 Job Finder":
        st.header("🚀 What I Can Do")
        for f in ["🔍 Search remote jobs worldwide", "📝 Review your CV/Resume",
                  "✉️ Write cover letters", "💡 Give career advice", "🎯 Match jobs to your skills"]:
            st.markdown(f'<div class="feature-card">{f}</div>', unsafe_allow_html=True)

        st.divider()
        st.header("📄 Upload Your CV")
        uploaded_cv = st.file_uploader("Upload CV (PDF, Word or TXT)", type=["pdf", "docx", "txt"])
        if uploaded_cv:
            file_size_mb = uploaded_cv.size / (1024 * 1024)
            if file_size_mb > 10:
                st.error(f"❌ File too large ({file_size_mb:.1f}MB). Max 10MB.")
            else:
                with st.spinner("Reading your CV..."):
                    cv_text = extract_text_from_file(uploaded_cv)
                if cv_text == "DOCX_NOT_SUPPORTED":
                    st.warning("⚠️ Word not available. Try PDF or TXT.")
                elif cv_text:
                    st.session_state.cv_text = cv_text
                    st.success(f"✅ CV read! ({len(cv_text.split())} words)")
                    with st.expander("👁️ Preview"):
                        st.text(cv_text[:500] + "..." if len(cv_text) > 500 else cv_text)
                else:
                    st.error("❌ Could not read file.")

        st.divider()
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.rerun()

    else:
        st.header("🎤 Mock Interview")
        st.markdown("Practice interviews with AI and get a full performance report.")
        st.divider()
        st.markdown("**📋 Format**\n- 6 questions\n- Mix behavioral & technical")
        st.markdown("**🎯 Scoring**\n- Each answer: 0–10\n- Instant feedback")
        st.markdown("**📥 Output**\n- Full PDF report\n- Strengths & tips")
        if st.session_state.interview_active:
            st.divider()
            if st.button("🛑 End Interview", use_container_width=True):
                for k in ["interview_active","interview_history","interview_messages",
                          "interview_q_count","interview_scores","interview_qa_pairs",
                          "interview_finished","interview_report","interview_pdf","last_question"]:
                    st.session_state[k] = [] if isinstance(st.session_state[k], list) else \
                                          False if isinstance(st.session_state[k], bool) else \
                                          0 if isinstance(st.session_state[k], int) else \
                                          None if st.session_state[k] is None else ""
                st.session_state.interview_active = False
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT AREA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>🌍 Remote Job Finder AI</h1>
    <p>Your personal AI assistant for finding remote jobs worldwide</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODE 1 — JOB FINDER
# ══════════════════════════════════════════════════════════════════════════════
if mode == "🔍 Job Finder":

    if not st.session_state.chat_history:
        with st.chat_message("assistant"):
            st.markdown("""
👋 **Hi! I'm your Remote Job Finder AI!**

I can help you:
- 🔍 **Find remote jobs** that match your skills
- 📝 **Review your CV** and suggest improvements
- ✉️ **Write cover letters** for specific jobs
- 💡 **Give career advice** for remote work

**To get started, tell me:**
- What is your profession or skill set?
- How many years of experience?
- What salary are you looking for?

Let's get you hired! 🚀
            """)

    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    # ── Single chat_input at bottom ───────────────────────────────────────────
    user_input = st.chat_input("Type here... e.g. 'Find Python developer jobs'")

    if user_input:
        if not os.environ.get("GROQ_API_KEY"):
            st.error("⚠️ Service unavailable. Please try again later.")
            st.stop()

        full_input = user_input

        # Inject CV if CV-related message
        if st.session_state.cv_text:
            cv_keywords = ["cv","resume","review","check","improve","analyze",
                           "analyse","feedback","suggest","look at","read","fix",
                           "update","score","rate","help","better","profile"]
            if any(w in user_input.lower() for w in cv_keywords):
                full_input = f"{user_input}\n\n[Attached CV/Resume:]\n{st.session_state.cv_text}"

        # Inject job search results if job-related message
        job_keywords = detect_job_search(user_input)
        if job_keywords:
            with st.spinner("🔍 Searching jobs..."):
                jobs_context = fetch_jobs_context(job_keywords)
            full_input = f"{user_input}\n\n[Job Search Results:]\n{jobs_context}"

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
                        st.download_button("📥 Download PDF", pdf_bytes,
                                           pdf_filename, "application/pdf",
                                           use_container_width=True)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ══════════════════════════════════════════════════════════════════════════════
# MODE 2 — MOCK INTERVIEW
# ══════════════════════════════════════════════════════════════════════════════
else:

    # ── START SCREEN ──────────────────────────────────────────────────────────
    if not st.session_state.interview_active:
        st.markdown("## 🎤 AI Mock Interview")
        st.markdown("Practice your interview skills and get a detailed performance report with scoring.")

        job_title = st.text_input(
            "Enter the job you are interviewing for:",
            placeholder="e.g. Python Developer, Graphic Designer, Marketing Manager"
        )
        start_btn = st.button("🚀 Start Interview", type="primary", use_container_width=True)

        if start_btn and job_title:
            if not os.environ.get("GROQ_API_KEY"):
                st.error("⚠️ Service unavailable.")
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
        elif start_btn:
            st.warning("⚠️ Please enter a job title.")

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown("### 📋 Format\n- 6 questions\n- One at a time\n- Behavioral & technical")
        with c2: st.markdown("### 🎯 Scoring\n- Each answer: 0-10\n- Instant feedback\n- Final score")
        with c3: st.markdown("### 📥 Output\n- Full PDF report\n- Strengths & gaps\n- Improvement tips")

    # ── ACTIVE INTERVIEW ──────────────────────────────────────────────────────
    else:
        job     = st.session_state.interview_job
        scores  = st.session_state.interview_scores
        q_count = st.session_state.interview_q_count
        avg     = round(sum(scores)/len(scores), 1) if scores else 0

        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(min(q_count-1, TOTAL_QUESTIONS)/TOTAL_QUESTIONS,
                        text=f"Question {min(q_count, TOTAL_QUESTIONS)} of {TOTAL_QUESTIONS}")
        with col2:
            st.metric("Avg Score", f"{avg}/10" if scores else "—")

        st.markdown(f"**🎯 Interviewing for: {job}**")
        st.divider()

        # Final report
        if st.session_state.interview_finished and st.session_state.interview_report:
            st.success("🎉 Interview Complete! Here is your performance report:")
            st.markdown(st.session_state.interview_report)
            if st.session_state.interview_pdf:
                st.download_button(
                    "📥 Download Full Report as PDF",
                    st.session_state.interview_pdf,
                    f"interview_report_{job.replace(' ','_')}.pdf",
                    "application/pdf", use_container_width=True
                )
        else:
            # Chat history
            for msg in st.session_state.interview_history:
                with st.chat_message(msg["role"]):
                    content = msg["content"]
                    if "SCORE:" in content:
                        for line in content.split("\n"):
                            if line.startswith("SCORE:"):
                                st.markdown(f"**🏆 {line}**")
                            elif line.startswith("FEEDBACK:"):
                                st.markdown(f"💬 {line}")
                            elif line.strip():
                                st.markdown(line)
                    else:
                        st.markdown(content)

            # Generate report if finished but not yet generated
            if st.session_state.interview_finished and not st.session_state.interview_report:
                with st.spinner("📊 Generating your performance report..."):
                    try:
                        report_text, pdf_bytes = generate_interview_report(
                            job, st.session_state.interview_qa_pairs)
                        st.session_state.interview_report = report_text
                        st.session_state.interview_pdf    = pdf_bytes
                    except Exception as e:
                        st.error(f"❌ Report error: {str(e)}")
                st.rerun()

            # ── Single chat_input at bottom ───────────────────────────────────
            if not st.session_state.interview_finished:
                answer = st.chat_input("Type your answer here...")
                if answer:
                    if not os.environ.get("GROQ_API_KEY"):
                        st.error("⚠️ Service unavailable.")
                        st.stop()

                    st.session_state.interview_history.append({"role": "user", "content": answer})
                    st.session_state.interview_messages.append({"role": "user", "content": answer})
                    st.session_state.interview_qa_pairs.append({
                        "question": st.session_state.last_question, "answer": answer
                    })

                    with st.spinner("🤔 Evaluating your answer..."):
                        try:
                            response, is_finished = continue_interview(
                                job, st.session_state.interview_messages,
                                st.session_state.interview_q_count)
                            score    = extract_score(response)
                            feedback = extract_feedback(response)
                            if score > 0:
                                st.session_state.interview_scores.append(score)
                                st.session_state.interview_qa_pairs[-1]["score"]    = score
                                st.session_state.interview_qa_pairs[-1]["feedback"] = feedback
                            st.session_state.interview_history.append({"role": "assistant", "content": response})
                            st.session_state.interview_messages.append({"role": "assistant", "content": response})
                            st.session_state.last_question   = response
                            st.session_state.interview_q_count += 1
                            if is_finished:
                                st.session_state.interview_finished = True
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                    st.rerun()
