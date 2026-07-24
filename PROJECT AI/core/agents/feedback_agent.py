from langchain_core.prompts import ChatPromptTemplate
from .config import get_llm, safe_invoke


def generate_immediate_feedback(question_text, user_response, evaluation_json):
    """
    Generates a real-time conversational feedback bubble response, explaining how the
    user did, highlighting one key strength, and offering actionable advice.
    """
    llm = get_llm(temperature=0.6)
    
    system_prompt = (
        "You are an encouraging and professional Interview Coach Agent.\n"
        "Your task is to review the candidate's response to an interview question, along with the automated "
        "evaluation details (which contain scores, strengths, and weaknesses), and draft a quick, spoken-feel constructive feedback paragraph.\n"
        "Keep it conversational, warm, and highly constructive (around 3-4 sentences).\n"
        "Structure it as:\n"
        "1. Direct assessment: Acknowledge what they did well (reference the strength).\n"
        "2. Actionable advice: Highlight the main area they missed or could explain better.\n"
        "3. Recommended study topic: Briefly recommend a specific concept, principle, or technique (e.g. STAR method) to look into."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Question:\n{question_text}\n\nCandidate's Response:\n{user_response}\n\nEvaluation Details:\n{evaluation_json}")
    ])

    chain = prompt | llm
    response = safe_invoke(chain, {
        "question_text": question_text,
        "user_response": user_response,
        "evaluation_json": str(evaluation_json)
    })

    return response.content.strip()

