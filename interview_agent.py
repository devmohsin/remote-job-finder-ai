import os
import json
from groq import Groq
from pdf_generator import generate_pdf

MODEL = "llama-3.3-70b-versatile"

TOTAL_QUESTIONS = 6

# ── System prompt for interviewer ────────────────────────────────────────────
INTERVIEWER_PROMPT = """You are an expert technical and behavioral interviewer conducting a professional job interview.

Your job is to:
1. Ask ONE interview question at a time
2. Evaluate the candidate's answer
3. Give a score and short feedback
4. Ask the next question

STRICT RULES:
- Ask only ONE question per message
- After the candidate answers, ALWAYS start your reply with:
  SCORE: X/10
  FEEDBACK: [2-3 sentences of honest feedback]
  Then ask the next question
- Be professional, encouraging but honest
- Mix behavioral questions (Tell me about...) and technical questions
- Do NOT ask all questions at once
- Do NOT reveal the total number of questions

Question types to cover across the interview:
1. Introduction (Tell me about yourself)
2. Experience & background
3. Technical/skill-specific question for the job
4. Problem solving / challenging situation
5. Teamwork / collaboration
6. Career goals / motivation

Keep responses concise and professional."""


def get_first_question(job_title: str) -> str:
    """Generate the opening question to start the interview"""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=300,
        messages=[
            {"role": "system", "content": INTERVIEWER_PROMPT},
            {"role": "user", "content": f"Start a mock interview for the position of: {job_title}. Ask the first question only."}
        ]
    )
    return response.choices[0].message.content


def continue_interview(job_title: str, messages: list, question_number: int) -> tuple:
    """
    Continue the interview — evaluate last answer and ask next question
    Returns (response_text, is_finished)
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    is_last = question_number >= TOTAL_QUESTIONS

    system = INTERVIEWER_PROMPT
    if is_last:
        system += f"\n\nIMPORTANT: This was the LAST question (question {TOTAL_QUESTIONS} of {TOTAL_QUESTIONS}). After evaluating this answer, do NOT ask another question. Instead, say: 'That concludes our interview! Type REPORT to see your full performance report.'"

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "system", "content": system}] + messages
    )

    text = response.choices[0].message.content
    return text, is_last


def generate_interview_report(job_title: str, qa_pairs: list) -> tuple:
    """
    Generate a detailed interview performance report
    Returns (report_text, pdf_bytes)
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # Build Q&A summary for the report
    qa_summary = ""
    for i, qa in enumerate(qa_pairs, 1):
        qa_summary += f"\nQ{i}: {qa['question']}\nAnswer: {qa['answer']}\nScore: {qa.get('score', 'N/A')}\nFeedback: {qa.get('feedback', 'N/A')}\n"

    prompt = f"""Generate a detailed interview performance report for a candidate who interviewed for: {job_title}

Interview Q&A Summary:
{qa_summary}

Write a professional report with these sections:
1. OVERALL PERFORMANCE SUMMARY
2. FINAL SCORE (calculate average from individual scores, show as X/10)
3. STRENGTHS (bullet points)
4. AREAS TO IMPROVE (bullet points)
5. TOP RECOMMENDATIONS (3-5 specific tips)
6. INTERVIEW READINESS LEVEL (Not Ready / Almost Ready / Ready / Excellent)

Be specific, honest, and encouraging. Make it actionable."""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": "You are an expert career coach writing a detailed interview performance report."},
            {"role": "user", "content": prompt}
        ]
    )

    report_text = response.choices[0].message.content

    # Generate PDF
    try:
        pdf_bytes = generate_pdf(f"Interview Report — {job_title}", report_text)
    except Exception:
        pdf_bytes = None

    return report_text, pdf_bytes


def extract_score(text: str) -> int:
    """Extract score from agent response like SCORE: 7/10"""
    import re
    match = re.search(r'SCORE:\s*(\d+)/10', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0


def extract_feedback(text: str) -> str:
    """Extract feedback text from agent response"""
    import re
    match = re.search(r'FEEDBACK:\s*(.+?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""
