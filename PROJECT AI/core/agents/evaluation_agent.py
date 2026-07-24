from langchain_core.prompts import ChatPromptTemplate
from .config import get_llm, safe_invoke

from .resume_agent import parse_json_from_llm

def evaluate_user_answer(company, job_role, question_text, category, user_response):
    """
    Evaluates the user's spoken answer for technical accuracy, communication quality,
    and returns a structured score and detailed analysis.
    """
    llm = get_llm(temperature=0.3, json_mode=True)
    
    system_prompt = (
        "You are an expert Answer Evaluation Agent.\n"
        "Your role is to assess the quality of a candidate's verbal response during a mock interview "
        "for a '{job_role}' role at '{company}'.\n"
        "Evaluate the response based on the category '{category}' and the question: '{question_text}'.\n\n"
        "Grading Guidelines:\n"
        "1. Score (0-100): Be objective. Deduced points for generic/vague answers, lack of structural detail, or incorrect technical facts. Technical answers must show real engineering depth. Behavioral answers should use the STAR (Situation, Task, Action, Result) methodology.\n"
        "2. Technical Correctness: Assess if the terminology is correct, logic is sound, and industry-standard practices are mentioned.\n"
        "3. Communication Quality: Rate the delivery structure, grammar, professionalism, and conciseness.\n"
        "4. Highlight exactly what was good (strengths) and what was missing or incorrect (weaknesses).\n"
        "5. Provide a clear, detailed 'model_answer' showing how a top-tier candidate would answer this question perfectly.\n\n"
        "You must return ONLY a JSON object containing the exact structure below. Do not output anything else.\n\n"
        "Expected JSON format:\n"
        "{{\n"
        '  "score": 85,\n'
        '  "technical_correctness": "Feedback on technical depth and accuracy...",\n'
        '  "communication_quality": "Feedback on communication clarity, structure, and delivery...",\n'
        '  "strengths": ["Strength point 1", "Strength point 2"],\n'
        '  "weaknesses": ["Weakness point 1", "Weakness point 2"],\n'
        '  "model_answer": "Complete perfect mock answer representing the highest standards..."\n'
        "}}\n"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Candidate's Spoken Answer (Speech-to-Text Transcript):\n{user_response}")
    ])

    chain = prompt | llm
    response = safe_invoke(chain, {
        "company": company,
        "job_role": job_role,
        "question_text": question_text,
        "category": category,
        "user_response": user_response
    })

    return parse_json_from_llm(response.content)

