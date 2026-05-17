# 🌍 Remote Job Finder AI Agent

An AI-powered agent built with **Python** and **Streamlit** that helps people find remote jobs worldwide, review CVs, and write cover letters.

---

## ✨ Features

- 🔍 **Job Search** — Searches real remote jobs from Remotive & RemoteOK (free APIs)
- 📝 **CV Review** — Analyzes your CV and gives a score with improvement tips
- ✉️ **Cover Letter Writer** — Writes professional cover letters instantly
- 💡 **Career Advice** — Gives personalized remote work advice
- 🎯 **Skill Matching** — Matches your skills to the best opportunities

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| AI API | AI brain |
| Streamlit | Web interface |
| Remotive API | Job listings (free) |
| RemoteOK API | Job listings (free) |

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/devmohsin/remote-job-finder-ai.git
cd remote-job-finder-ai
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your API key
```bash
cp .env.example .env
# Edit .env and add your API key
```

### 4. Run the app
```bash
streamlit run app.py
```

### 5. Open in browser
```
http://localhost:8501
```

---

## 💬 Example Conversations

```
User: "Find Python developer jobs"
Agent: Searches and shows 5 latest remote Python jobs with salary & apply links

User: "I am a graphic designer with 3 years experience"  
Agent: Asks about salary expectations, then shows matching design jobs

User: "Review my CV" (after uploading CV)
Agent: Gives CV score, lists issues, and provides specific improvements

User: "Write a cover letter for Senior Designer at Shopify"
Agent: Generates a professional, personalized cover letter instantly
```

---

## 📁 Project Structure

```
Agent/
├── app.py          # Streamlit frontend
├── agent.py        # AI agent + agentic loop
├── tools.py        # Job search & CV tools
├── requirements.txt
├── .env.example    # API key template
├── .gitignore
└── README.md
```

---

## 🔑 API Keys Needed

| API | Required | Cost | Link |
|-----|----------|------|------|
| AI API Key | ✅ Yes | Pay per use | Set in `.env` file |
| Remotive | ❌ No | Free | Auto |
| RemoteOK | ❌ No | Free | Auto |

---

## 💰 How to Monetize

- Charge $9.99/month for unlimited job searches
- Offer CV review as a paid service ($20-50)
- Add affiliate links for job platforms
- White-label it for HR agencies

---

Built with ❤️ by devmohsin
