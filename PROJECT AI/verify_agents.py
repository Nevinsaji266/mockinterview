import sys
import os
import json
from dotenv import load_dotenv

# Load env before importing agents
load_dotenv()

# Add project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.agents.resume_agent import analyze_resume
from core.agents.rag_agent import build_rag_index, retrieve_context
from core.agents.question_agent import generate_interview_questions
from core.agents.evaluation_agent import evaluate_user_answer
from core.agents.feedback_agent import generate_immediate_feedback
from core.agents.report_agent import generate_interview_report

# Mock resume for testing
MOCK_RESUME = """
John Doe
Email: john.doe@email.com | Phone: +1-555-0199 | Portfolio: github.com/johndoe
Summary: Experienced Full Stack Software Engineer with 4+ years of expertise in Python, Django, PostgreSQL, and JavaScript. Built and maintained scalable backend systems, microservices, and responsive user interfaces.

Experience:
Senior Software Engineer | TechCorp Inc. (2024 - Present)
- Architected a Python Django backend for a real-time data streaming platform, reducing request latency by 35%.
- Integrated FAISS vector database to build semantic search engines for user metadata.
- Managed a team of 3 developers, introducing agile workflows and CI/CD pipelines.

Software Engineer | DevStart Co. (2022 - 2024)
- Developed APIs using Django REST Framework (DRF) and built user interfaces using React and Bootstrap.
- Optimized slow SQL queries, reducing database load by 40%.
- Integrated AWS S3 and EC2 for cloud application deployment.

Education:
B.S. in Computer Science | University of Engineering (2018 - 2022)

Skills:
Languages: Python, JavaScript, HTML, CSS, SQL, Shell Scripting
Frameworks: Django, Django REST Framework, React, Bootstrap, Flask
Databases: PostgreSQL, SQLite, Redis, FAISS
Cloud & Tools: AWS, Docker, Git, CI/CD, Linux
"""

def test_pipeline():
    print("=== Step 1: Running Resume Analysis Agent ===")
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in environment. Please set it in .env file.")
        sys.exit(1)
        
    try:
        analysis = analyze_resume(MOCK_RESUME)
        print("Analysis success!")
        print(f"Candidate Name: {analysis.get('name')}")
        print(f"ATS Score: {analysis.get('ats_score')}")
        print(f"Extracted Skills: {analysis.get('skills')[:5]}...")
        print(f"Missing Keywords: {analysis.get('missing_keywords')}")
    except Exception as e:
        print(f"Resume Analysis Agent failed: {e}")
        return

    print("\n=== Step 2: Running RAG Indexing ===")
    user_id = 9999
    try:
        success = build_rag_index(user_id, MOCK_RESUME)
        if success:
            print("FAISS Index constructed successfully!")
            context = retrieve_context(user_id, "Python Django experience")
            print("Retrieved context preview:")
            print(context[:150] + "...")
        else:
            print("RAG Index construction failed.")
            return
    except Exception as e:
        print(f"RAG Retrieval Agent failed: {e}")
        return

    print("\n=== Step 3: Running Question Generation Agent (FAANG/Google Standard) ===")
    company = "Google"
    role = "Django Backend Architect"
    difficulty = "Hard"
    try:
        questions = generate_interview_questions(
            company=company,
            job_role=role,
            difficulty=difficulty,
            resume_analysis=analysis,
            rag_context=context
        )
        print(f"Successfully generated {len(questions.get('questions', []))} questions:")
        for q in questions.get('questions', []):
            print(f"- Q{q.get('order')} [{q.get('category')}]: {q.get('question_text')}")
    except Exception as e:
        print(f"Question Generation Agent failed: {e}")
        return

    print("\n=== Step 4: Running Answer Evaluation & Feedback Agents ===")
    # Pick the first question
    if questions.get('questions'):
        test_q = questions['questions'][0]
        # Mock a spoken answer transcript
        mock_answer = (
            "Yes, I have worked extensively with Django. In my last project at TechCorp, "
            "I architected the backend database and introduced middleware to intercept incoming streams, "
            "which allowed us to cache results in Redis. This reduced the database latency by 35% "
            "and handled 10,000 requests per second. We also used custom middleware for authorization."
        )
        print(f"Question: {test_q['question_text']}")
        print(f"Mock Spoken Response: {mock_answer}")
        
        try:
            # Run Evaluation
            eval_res = evaluate_user_answer(
                company=company,
                job_role=role,
                question_text=test_q['question_text'],
                category=test_q['category'],
                user_response=mock_answer
            )
            print(f"Answer Score: {eval_res.get('score')}/100")
            print(f"Technical Correctness: {eval_res.get('technical_correctness')[:150]}...")
            
            # Run Feedback
            feedback = generate_immediate_feedback(test_q['question_text'], mock_answer, eval_res)
            print("\nCoach Feedback Bubble:")
            print(feedback)
        except Exception as e:
            print(f"Evaluation/Feedback Agent failed: {e}")
            return
    else:
        print("No questions to test.")
        return

    print("\n=== Step 5: Running Interview Report Agent ===")
    try:
        mock_history = [{
            "order": test_q["order"],
            "category": test_q["category"],
            "question_text": test_q["question_text"],
            "user_response": mock_answer,
            "score": eval_res.get("score", 80),
            "evaluation_json": eval_res
        }]
        
        report = generate_interview_report(
            company=company,
            job_role=role,
            difficulty=difficulty,
            resume_analysis=analysis,
            questions_evaluations=mock_history
        )
        print("Final Interview Report Compiled!")
        print(f"Overall Interview Score: {report.get('overall_score')}%")
        print(f"Final Recommendation Decision: {report.get('final_decision')}")
        print(f"Development Study Plan: {report.get('development_plan')}")
    except Exception as e:
        print(f"Report Agent failed: {e}")
        return

    print("\n=== Pipeline Verification Completed Successfully! ===")

if __name__ == "__main__":
    test_pipeline()
