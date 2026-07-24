from langchain_core.prompts import ChatPromptTemplate
from .config import get_llm, safe_invoke

from .resume_agent import parse_json_from_llm

def generate_interview_report(company, job_role, difficulty, resume_analysis, questions_evaluations):
    """
    Synthesizes the complete session answers and grades into a final comprehensive scorecard report.
    """
    llm = get_llm(temperature=0.3, json_mode=True)
    
    system_prompt = (
        "You are an expert Interview Board Panel Agent.\n"
        "Your task is to compile a comprehensive, high-quality final interview assessment report "
        "for a candidate applying for the '{job_role}' role at '{company}' (Difficulty: '{difficulty}').\n"
        "Review the candidate's resume analysis details, the history of questions asked, their scores, strengths, weaknesses, responses, "
        "and their voice metrics (speaking duration, words per minute, speech recognition confidence, and filler word counts).\n\n"
        "Compile the metrics into a professional, structured JSON object with the following fields:\n"
        "1. overall_score (Integer 0-100): Calculated as the average of the individual question scores.\n"
        "2. technical_assessment: Synthesis of candidate's technical competency and domain depth, highlighting areas of strong technical understanding and gaps.\n"
        "3. communication_assessment: Detailed review of candidate's pacing, clarity, structure (STAR method), and vocal confidence. Directly analyze their overall pacing (WPM), filler word usage, and how confident/articulous their speech was, offering clear improvement tips.\n"
        "4. voice_analysis: A detailed breakdown and critique of the candidate's voice parameters across the interview, including: average speaking rate (WPM), total filler words used, vocal confidence score (out of 100), and specific recommendations on pacing (too fast, too slow, or just right), breathing, and minimizing hesitations.\n"
        "5. key_strengths: List of the top 3 strengths demonstrated across the interview (technical or communication/delivery).\n"
        "6. key_weaknesses: List of the top 3 weaknesses or skill/delivery gaps identified.\n"
        "7. development_plan: List of 4-5 specific recommended study topics, speech coaching tips, or action items.\n"
        "8. final_decision: One of ['Strong Hire', 'Hire', 'No Hire'] with a brief 1-sentence justification.\n\n"
        "You must return ONLY a JSON object matching this structure. Do not output any other content.\n\n"
        "Expected JSON format:\n"
        "{{\n"
        '  "overall_score": 80,\n'
        '  "technical_assessment": "Comprehensive review of technical performance...",\n'
        '  "communication_assessment": "Comprehensive review of communication and delivery...",\n'
        '  "voice_analysis": {{\n'
        '    "average_wpm": 135,\n'
        '    "total_fillers": 12,\n'
        '    "vocal_confidence_score": 85,\n'
        '    "pacing_feedback": "Your speaking speed was...",\n'
        '    "recommendations": ["Avoid using filler words like...", "Use natural pauses instead of...", "..."]\n'
        '  }},\n'
        '  "key_strengths": ["...", "...", "..."],\n'
        '  "key_weaknesses": ["...", "...", "..."],\n'
        '  "development_plan": ["...", "...", "..."],\n'
        '  "final_decision": "Hire - Candidate showed robust system understanding..."\n'
        "}}\n"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Resume Analysis:\n{resume_analysis}\n\nQuestions & Evaluations:\n{questions_evaluations}")
    ])

    # Format the questions and evaluations nicely for the LLM
    formatted_evals = []
    for q in questions_evaluations:
        formatted_evals.append(
            f"Question {q['order']} ({q['category']}): {q['question_text']}\n"
            f"Candidate Response: {q['user_response']}\n"
            f"Score: {q['score']}/100\n"
            f"Evaluation: {q['evaluation_json']}\n"
            f"Voice & Pacing Metrics: {q['voice_metrics_json']}\n"
            f"---"
        )
    evals_text = "\n\n".join(formatted_evals)

    chain = prompt | llm
    response = chain.invoke({
        "company": company,
        "job_role": job_role,
        "difficulty": difficulty,
        "resume_analysis": resume_analysis,
        "questions_evaluations": evals_text
    })

    return parse_json_from_llm(response.content)

