import requests
import shared_state
from pdf_generator import generate_pdf


def search_remote_jobs(keywords: str, category: str = "", limit: int = 5) -> dict:
    """
    Search remote jobs using Remotive API (Free, no API key needed)
    """
    try:
        url = "https://remotive.com/api/remote-jobs"
        params = {"search": keywords, "limit": limit}
        if category:
            params["category"] = category

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = data.get("jobs", [])
        if not jobs:
            return {"success": False, "message": "No jobs found for your search.", "jobs": []}

        result = []
        for job in jobs[:limit]:
            result.append({
                "title": job.get("title", "N/A"),
                "company": job.get("company_name", "N/A"),
                "location": job.get("candidate_required_location", "Worldwide"),
                "salary": job.get("salary", "Not specified"),
                "job_type": job.get("job_type", "Full-time"),
                "url": job.get("url", ""),
                "posted_date": job.get("publication_date", "")[:10],
                "description": job.get("description", "")[:300] + "..."
            })

        return {"success": True, "total_found": len(jobs), "jobs": result}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Error fetching jobs: {str(e)}", "jobs": []}


def search_remoteok_jobs(tag: str, limit: int = 5) -> dict:
    """
    Search remote jobs using RemoteOK API (Free, no API key needed)
    """
    try:
        url = f"https://remoteok.com/api?tag={tag}"
        headers = {"User-Agent": "RemoteJobFinderBot/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Skip the first item (it's a legal notice)
        jobs = [j for j in data if isinstance(j, dict) and j.get("position")][:limit]

        if not jobs:
            return {"success": False, "message": "No jobs found on RemoteOK.", "jobs": []}

        result = []
        for job in jobs:
            result.append({
                "title": job.get("position", "N/A"),
                "company": job.get("company", "N/A"),
                "location": "Remote",
                "salary": f"${job.get('salary_min', 'N/A')} - ${job.get('salary_max', 'N/A')}" if job.get("salary_min") else "Not specified",
                "tags": ", ".join(job.get("tags", [])[:5]),
                "url": job.get("url", ""),
                "posted_date": job.get("date", "")[:10]
            })

        return {"success": True, "total_found": len(jobs), "jobs": result}

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Error fetching from RemoteOK: {str(e)}", "jobs": []}


def review_cv(cv_text: str) -> dict:
    """
    Analyze CV text and return structured feedback
    """
    issues = []
    suggestions = []
    score = 100

    # Check length
    word_count = len(cv_text.split())
    if word_count < 100:
        issues.append("CV is too short (less than 100 words)")
        score -= 20
    elif word_count > 800:
        issues.append("CV might be too long (over 800 words) — keep it concise")
        score -= 10

    # Check key sections
    cv_lower = cv_text.lower()
    sections = {
        "experience": ["experience", "work history", "employment"],
        "education": ["education", "degree", "university", "college"],
        "skills": ["skills", "technologies", "tools", "languages"],
        "contact": ["email", "phone", "linkedin", "github"]
    }

    for section, keywords in sections.items():
        if not any(kw in cv_lower for kw in keywords):
            issues.append(f"Missing '{section.title()}' section")
            score -= 15
            suggestions.append(f"Add a clear '{section.title()}' section")

    # Check for action verbs
    action_verbs = ["developed", "built", "created", "managed", "led", "improved",
                    "implemented", "designed", "launched", "achieved", "increased"]
    found_verbs = [v for v in action_verbs if v in cv_lower]
    if len(found_verbs) < 3:
        suggestions.append("Use more action verbs (e.g., Developed, Built, Led, Improved)")
        score -= 10

    # Check for numbers/metrics
    import re
    numbers = re.findall(r'\d+%|\$\d+|\d+ years|\d+ months', cv_text)
    if len(numbers) < 2:
        suggestions.append("Add measurable achievements (e.g., 'Increased sales by 30%', 'Managed team of 5')")
        score -= 10

    score = max(0, score)

    return {
        "success": True,
        "score": score,
        "grade": "Excellent" if score >= 85 else "Good" if score >= 70 else "Needs Improvement",
        "issues": issues if issues else ["No major issues found!"],
        "suggestions": suggestions if suggestions else ["Your CV looks good!"],
        "word_count": word_count
    }


def write_cover_letter(job_title: str, company_name: str, candidate_skills: str, years_experience: str) -> dict:
    """
    Generate a professional cover letter template
    """
    cover_letter = f"""Dear Hiring Manager at {company_name},

I am excited to apply for the {job_title} position at {company_name}. With {years_experience} of hands-on experience and a strong background in {candidate_skills}, I am confident in my ability to contribute meaningfully to your team.

Throughout my career, I have developed expertise in {candidate_skills}, allowing me to deliver high-quality results in fast-paced, remote environments. I am highly self-motivated, communicate proactively, and have a proven track record of meeting deadlines independently — qualities that are essential for remote work success.

What excites me most about {company_name} is the opportunity to work with a forward-thinking team and contribute to impactful projects. I am eager to bring my skills and dedication to help {company_name} achieve its goals.

I would love the opportunity to discuss how my background aligns with your needs. I am available for an interview at your earliest convenience.

Thank you for considering my application. I look forward to hearing from you.

Best regards,
[Your Full Name]
[Your Email]
[Your LinkedIn/Portfolio URL]
[Your Phone Number]"""

    return {
        "success": True,
        "cover_letter": cover_letter,
        "tips": [
            "Customize the opening line to mention something specific about the company",
            "Replace [Your Full Name] and contact details before sending",
            "Add one specific achievement that matches the job requirements",
            "Keep it under 400 words for best results"
        ]
    }


def get_job_categories() -> dict:
    """
    Return popular remote job categories
    """
    return {
        "success": True,
        "categories": [
            "Software Development",
            "Design",
            "Marketing",
            "Customer Support",
            "Sales",
            "Project Management",
            "Writing",
            "Data Science",
            "Finance",
            "HR & Recruiting",
            "DevOps / Sysadmin",
            "Product Management"
        ]
    }


def create_pdf(title: str, content: str, filename: str = "document.pdf") -> dict:
    """
    Create a PDF file from given title and content.
    Use this whenever user asks to create, generate or download a PDF.
    """
    try:
        pdf_bytes = generate_pdf(title, content)
        # Store in shared state so app.py can show download button
        shared_state.pdf_buffer = pdf_bytes
        shared_state.pdf_filename = filename if filename.endswith(".pdf") else filename + ".pdf"
        return {
            "success": True,
            "message": f"PDF '{shared_state.pdf_filename}' has been created successfully! The download button will appear below."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create PDF: {str(e)}"
        }
