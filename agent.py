import json
import anthropic
from tools import search_remote_jobs, search_remoteok_jobs, review_cv, write_cover_letter, get_job_categories

# Initialize Anthropic client
client = anthropic.Anthropic()

# System prompt for the agent
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

Always respond in a friendly, conversational tone. Use emojis occasionally to keep things engaging. 🚀"""

# Define tools for Claude
TOOLS = [
    {
        "name": "search_remote_jobs",
        "description": "Search for remote job listings using keywords. Use this when the user wants to find remote jobs. Returns job title, company, salary, location, and apply link.",
        "input_schema": {
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
                    "description": "Number of jobs to return (default 5, max 10)",
                    "default": 5
                }
            },
            "required": ["keywords"]
        }
    },
    {
        "name": "search_remoteok_jobs",
        "description": "Search RemoteOK platform for remote jobs by tag/skill. Good for tech and developer jobs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "description": "Skill or technology tag e.g. 'python', 'react', 'design', 'marketing'"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of jobs to return (default 5)",
                    "default": 5
                }
            },
            "required": ["tag"]
        }
    },
    {
        "name": "review_cv",
        "description": "Review and analyze a user's CV/Resume text. Gives a score, identifies issues, and provides improvement suggestions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cv_text": {
                    "type": "string",
                    "description": "The full text content of the user's CV/Resume"
                }
            },
            "required": ["cv_text"]
        }
    },
    {
        "name": "write_cover_letter",
        "description": "Write a professional cover letter for a specific job application.",
        "input_schema": {
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
    },
    {
        "name": "get_job_categories",
        "description": "Get a list of popular remote job categories. Use this when the user is unsure what category to search in.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
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
        else:
            result = {"success": False, "message": f"Unknown tool: {tool_name}"}

        return json.dumps(result)
    except Exception as e:
        return json.dumps({"success": False, "message": f"Tool error: {str(e)}"})


def run_agent(messages: list) -> str:
    """
    Run the AI agent with the agentic loop
    Returns the final text response
    """
    while True:
        # Call Claude API
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # Check if Claude wants to use a tool
        if response.stop_reason == "tool_use":
            # Add Claude's response to messages
            messages.append({"role": "assistant", "content": response.content})

            # Process all tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Execute the tool
                    tool_result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    })

            # Add tool results to messages
            messages.append({"role": "user", "content": tool_results})

        else:
            # Claude is done — extract final text response
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text
