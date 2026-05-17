import json
import os
from groq import Groq
from pdf_generator import generate_pdf
from tools import search_remote_jobs, search_remoteok_jobs, review_cv, write_cover_letter, get_job_categories

# Model to use (free on Groq)
MODEL = "llama-3.3-70b-versatile"

# System prompt
SYSTEM_PROMPT = """You are RemoteJobBot, a helpful AI assistant that specializes in helping people find remote jobs worldwide.

You help users with:
1. Searching for remote jobs based on their skills and experience
2. Reviewing and improving their CV/Resume
3. Writing professional cover letters
4. Giving career advice for remote work

Your personality:
- Friendly, encouraging, and professional
- Always ask clarifying questions to find the best jobs for the user
- Celebrate when you find great job matches
- Give honest, constructive feedback on CVs

When searching for jobs:
- Always ask about their skills, experience level, and expected salary if not provided
- Search using multiple keywords for better results
- Present jobs in a clear, easy-to-read format
- Always include the apply link

When reviewing CVs:
- Be encouraging but honest
- Give specific, actionable suggestions
- Focus on what will help them get hired faster

When writing cover letters:
- Write the FULL cover letter directly in your response as plain text
- Do NOT mention any PDF link or URL
- Do NOT say "here is your CV in PDF format"
- Do NOT generate or mention any download links
- Just write the complete cover letter text — the app handles PDF download automatically

IMPORTANT RULES — NEVER break these:
- NEVER generate fake URLs or links
- NEVER say "here is your PDF at https://..."
- NEVER mention fictional download links
- NEVER say a PDF has been created or sent
- PDF download is handled automatically by the app — you only need to write the content as plain text

Always respond in a friendly, conversational tone. Use emojis occasionally to keep things engaging. 🚀"""

# Define tools (Groq uses OpenAI-compatible format)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_remote_jobs",
            "description": "Search for remote job listings using keywords. Use this when the user wants to find remote jobs. Returns job title, company, salary, location, and apply link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Job search keywords e.g. 'python developer', 'graphic designer', 'customer support'"
                    },
                    "category": {
                        "type": "string",
                        "description": "Job category filter (optional) e.g. 'software-dev', 'design', 'marketing'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of jobs to return (default 5, max 10)"
                    }
                },
                "required": ["keywords"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_remoteok_jobs",
            "description": "Search RemoteOK platform for remote jobs by tag/skill. Good for tech and developer jobs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Skill or technology tag e.g. 'python', 'react', 'design', 'marketing'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of jobs to return (default 5)"
                    }
                },
                "required": ["tag"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "review_cv",
            "description": "Review and analyze a user's CV/Resume text. Gives a score, identifies issues, and provides improvement suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cv_text": {
                        "type": "string",
                        "description": "The full text content of the user's CV/Resume"
                    }
                },
                "required": ["cv_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_cover_letter",
            "description": "Write a professional cover letter for a specific job application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_title": {
                        "type": "string",
                        "description": "The job title they are applying for"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "The name of the company"
                    },
                    "candidate_skills": {
                        "type": "string",
                        "description": "The candidate's main skills and expertise"
                    },
                    "years_experience": {
                        "type": "string",
                        "description": "Years of experience e.g. '3 years', '5+ years'"
                    }
                },
                "required": ["job_title", "company_name", "candidate_skills", "years_experience"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_job_categories",
            "description": "Get a list of popular remote job categories. Use this when the user is unsure what category to search in.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_pdf",
            "description": "Create and generate a downloadable PDF file with any content. Use this whenever the user asks to create a PDF, generate a PDF, download something as PDF, or save content to PDF.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the PDF document e.g. 'Cover Letter', 'CV Review', 'Hello World'"
                    },
                    "content": {
                        "type": "string",
                        "description": "The full content/body text to include in the PDF"
                    },
                    "filename": {
                        "type": "string",
                        "description": "The filename for the PDF e.g. 'cover_letter.pdf', 'hello_world.pdf'"
                    }
                },
                "required": ["title", "content"]
            }
        }
    }
]


def execute_tool(tool_name: str, tool_input: dict, pdf_store: dict) -> str:
    """Execute the requested tool and return result as string"""
    try:
        if tool_name == "search_remote_jobs":
            result = search_remote_jobs(**tool_input)
        elif tool_name == "search_remoteok_jobs":
            result = search_remoteok_jobs(**tool_input)
        elif tool_name == "review_cv":
            result = review_cv(**tool_input)
        elif tool_name == "write_cover_letter":
            result = write_cover_letter(**tool_input)
        elif tool_name == "get_job_categories":
            result = get_job_categories()
        elif tool_name == "create_pdf":
            # Generate PDF and store bytes directly in pdf_store dict
            try:
                title    = tool_input.get("title", "Document")
                content  = tool_input.get("content", "")
                filename = tool_input.get("filename", "document.pdf")
                if not filename.endswith(".pdf"):
                    filename += ".pdf"
                pdf_bytes = generate_pdf(title, content)
                pdf_store["bytes"]    = pdf_bytes
                pdf_store["filename"] = filename
                result = {"success": True, "message": f"PDF '{filename}' created! Download button will appear below."}
            except Exception as e:
                result = {"success": False, "message": f"PDF creation failed: {str(e)}"}
        else:
            result = {"success": False, "message": f"Unknown tool: {tool_name}"}

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"success": False, "message": f"Tool error: {str(e)}"})


def run_agent(messages: list) -> tuple:
    """
    Run the AI agent with the agentic loop
    Returns (text_response, pdf_bytes, pdf_filename)
    """
    # Initialize client here so it picks up the API key at runtime
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # PDF store — passed into execute_tool so it can store PDF bytes directly
    pdf_store = {"bytes": None, "filename": "document.pdf"}

    # Add system message at the start
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    while True:
        # Call Groq API
        response = client.chat.completions.create(
            model=MODEL,
            messages=full_messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=2048
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # Check if model wants to use a tool
        if finish_reason == "tool_calls" and message.tool_calls:

            # Add assistant message with tool calls to history
            full_messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name  = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                # Run the tool (pass pdf_store so create_pdf can fill it)
                tool_result = execute_tool(tool_name, tool_input, pdf_store)

                # Add tool result to messages
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

        else:
            # Agent is done — return text + any PDF that was generated
            text = message.content or "Sorry, I could not generate a response. Please try again."
            return text, pdf_store["bytes"], pdf_store["filename"]
