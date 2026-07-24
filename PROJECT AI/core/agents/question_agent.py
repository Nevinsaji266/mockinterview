from langchain_core.prompts import ChatPromptTemplate
from .config import get_llm, safe_invoke

from .resume_agent import parse_json_from_llm

def generate_interview_questions(company, job_role, difficulty, resume_analysis, rag_context):
    """
    Generates a structured list of interview questions tailored to the company, role,
    difficulty level, and candidate's resume/RAG context.
    """
    llm = get_llm(temperature=0.7, json_mode=True)
    
    # Identify if the company is a high-bar tech firm
    high_bar_companies = [
        "google", "amazon", "meta", "netflix", "microsoft", "apple", "uber", "airbnb",
        "spotify", "stripe", "twitter", "x", "bytedance", "salesforce", "adobe", "nvidia"
    ]
    is_high_bar = company.lower() in high_bar_companies
    
    company_style_guideline = ""
    if is_high_bar:
        company_style_guideline = (
            f"Note: {company} is a top-tier technology firm. The questions generated MUST match their legendary high standards:\n"
            f"- Technical questions (Questions 2-5) should assess deep structural concepts, scale, optimization, memory footprint, algorithmic complexity, or complex distributed system design relative to the '{job_role}' role.\n"
            f"- Behavioral questions (Questions 6-9) should map to their known hiring philosophy (e.g., if Amazon, focus on Leadership Principles like customer obsession or ownership; if Google, assess 'Googley' collaboration, cognitive ability under ambiguity, and system thinking).\n"
            "- Make questions challenging, realistic, and highly specific to the candidate's projects. Do not ask generic trivia."
        )
    else:
        company_style_guideline = (
            f"Generate professional interview questions representing standards at {company} for a {job_role} position. "
            "Tailor the technical depth based on the projects and skills in the resume, matching the target difficulty. "
            "Ensure the questions test practical problem-solving skills, engineering trade-offs, and best practices."
        )

    system_prompt = (
        "You are an expert Interviewer Agent at {company}.\n"
        "Your task is to generate exactly 10 personalized interview questions (consisting of 4 Technical, 4 Behavioral, and 2 HR questions) "
        "for a candidate applying for the '{job_role}' role at difficulty level '{difficulty}'.\n"
        "To customize the questions, analyze the resume details, skills, and projects provided, and leverage the retrieved "
        "RAG context from their resume to ask highly specific questions.\n\n"
        "{company_style_guideline}\n\n"
        "Requirements:\n"
        "1. Question 1 (HR): Introduce themselves relative to the role or explain why they want to work at this specific company.\n"
        "2. Question 2, 3, 4 & 5 (Technical): Specific to the role (e.g. coding, database schema, concurrency, caching, system architecture, etc.) and deep-dives into the projects/skills listed in their resume.\n"
        "3. Question 6, 7, 8 & 9 (Behavioral): Specific situational questions based on the candidate's past projects/experiences assessing teamwork, conflict resolution, dealing with failure/success, and project delivery.\n"
        "4. Question 10 (HR): Career aspirations, future trajectory, or a wrap-up interview scenario.\n\n"
        "You must return ONLY a JSON object containing the exact structure below. Do not write anything other than the JSON.\n\n"
        "Expected JSON format:\n"
        "{{\n"
        '  "questions": [\n'
        '    {{"order": 1, "category": "HR", "question_text": "..."}},\n'
        '    {{"order": 2, "category": "Technical", "question_text": "..."}},\n'
        '    {{"order": 3, "category": "Technical", "question_text": "..."}},\n'
        '    {{"order": 4, "category": "Technical", "question_text": "..."}},\n'
        '    {{"order": 5, "category": "Technical", "question_text": "..."}},\n'
        '    {{"order": 6, "category": "Behavioral", "question_text": "..."}},\n'
        '    {{"order": 7, "category": "Behavioral", "question_text": "..."}},\n'
        '    {{"order": 8, "category": "Behavioral", "question_text": "..."}},\n'
        '    {{"order": 9, "category": "Behavioral", "question_text": "..."}},\n'
        '    {{"order": 10, "category": "HR", "question_text": "..."}}\n'
        '  ]\n'
        "}}\n"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Resume Analysis:\n{resume_analysis}\n\nRetrieved Resume Context (RAG):\n{rag_context}")
    ])

    chain = prompt | llm
    response = safe_invoke(chain, {
        "company": company,
        "job_role": job_role,
        "difficulty": difficulty,
        "company_style_guideline": company_style_guideline,
        "resume_analysis": resume_analysis,
        "rag_context": rag_context
    })

    return parse_json_from_llm(response.content)

