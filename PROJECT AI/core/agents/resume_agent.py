import json
import re
from pypdf import PdfReader
from langchain_core.prompts import ChatPromptTemplate
from .config import get_llm, safe_invoke


def extract_text_from_pdf(pdf_file):
    """
    Parses a PDF file object (or filepath) and extracts all raw text.
    """
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""

def parse_json_from_llm(text):
    """
    Helper to clean and extract JSON data from the LLM output,
    stripping markdown backticks if present.
    """
    # Clean output if it is wrapped in markdown code blocks
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    # Try parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: find the first '{' and last '}'
        match = re.search(r"(\{.*?\})", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Could not parse valid JSON from output: {text}")

def analyze_resume(resume_text):
    """
    Runs the Resume Analysis Agent to extract structured details and compute an ATS score.
    """
    llm = get_llm(temperature=0.2, json_mode=True)
    
    system_prompt = (
        "You are an expert Resume Analysis Agent and Professional Recruiter.\n"
        "Your task is to analyze the provided resume text and extract key structural information, "
        "calculate a dynamic ATS (Applicant Tracking System) score (0-100), and highlight areas "
        "of strengths, weaknesses, missing keywords, and suggestions for improvement.\n"
        "You must return ONLY a JSON object containing the exact structure below. Do not include any other markdown outside the JSON.\n\n"
        "Expected JSON format:\n"
        "{{\n"
        '  "name": "Candidate Name (or User if not found)",\n'
        '  "skills": ["Skill 1", "Skill 2", ...],\n'
        '  "education": [{{"degree": "Degree Name", "institution": "University/School", "year": "Graduation Year"}}],\n'
        '  "experience": [{{"role": "Job Title", "company": "Company Name", "duration": "Dates/Duration", "description": "Responsibilities"}}],\n'
        '  "projects": [{{"name": "Project Name", "description": "Project details"}}],\n'
        '  "certifications": ["Certification 1", "Achievement 2", ...],\n'
        '  "ats_score": 75,\n'
        '  "missing_keywords": ["Keywords that would enhance ATS readability for common roles"],\n'
        '  "strengths": ["Strength 1", "Strength 2", "Strength 3"],\n'
        '  "weaknesses": ["Weakness 1", "Weakness 2", "Weakness 3"],\n'
        '  "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]\n'
        "}}\n"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Resume Text:\n{resume_text}")
    ])

    # Invoke LLM
    chain = prompt | llm
    response = safe_invoke(chain, {"resume_text": resume_text})
    
    # Parse and return JSON
    return parse_json_from_llm(response.content)

