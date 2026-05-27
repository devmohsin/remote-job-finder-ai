import os
from groq import Groq

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are RemoteJobBot, a helpful AI assistant that specializes in helping people find remote jobs worldwide.

You help users with:
1. Presenting remote job search results in a clear, friendly format
2. Reviewing and improving their CV/Resume
3. Writing professional cover letters
4. Giving career advice for remote work

When job results are provided to you in the message, present them in this format for each job:
**[Job Number]. Job Title — Company**
💰 Salary: ...
📍 Location: ...
🔗 Apply: [URL]

When reviewing CVs:
- Give a score out of 100
- List strengths
- List specific improvements
- Be encouraging but honest

When writing cover letters:
- Write the FULL cover letter as plain text
- Do NOT mention any PDF links or URLs
- Keep it professional and personalized

IMPORTANT RULES:
- NEVER generate fake URLs or links
- NEVER say a PDF has been created
- NEVER invent job listings — only present jobs given to you in the context

Always respond in a friendly, conversational tone. Use emojis occasionally. 🚀"""


def run_agent(messages: list) -> tuple:
    """
    Run the AI agent — pure text generation, no tool calling
    Returns (text_response, pdf_bytes, pdf_filename)
    """
    from pdf_generator import generate_pdf

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    response = client.chat.completions.create(
        model=MODEL,
        messages=full_messages,
        max_tokens=2048
    )

    text = response.choices[0].message.content or "Sorry, I could not generate a response."

    # Generate PDF if response contains cover letter or CV review
    pdf_bytes = None
    pdf_filename = "document.pdf"
    text_lower = text.lower()

    if "dear hiring" in text_lower or "cover letter" in text_lower:
        try:
            pdf_bytes = generate_pdf("Cover Letter", text)
            pdf_filename = "cover_letter.pdf"
        except Exception:
            pass
    elif "score:" in text_lower or "cv review" in text_lower or "resume review" in text_lower:
        try:
            pdf_bytes = generate_pdf("CV Review Report", text)
            pdf_filename = "cv_review.pdf"
        except Exception:
            pass

    return text, pdf_bytes, pdf_filename
