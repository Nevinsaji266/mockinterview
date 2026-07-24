import json
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import UserProfile, InterviewSession, InterviewQuestion
from .agents.resume_agent import extract_text_from_pdf, analyze_resume
from .agents.rag_agent import build_rag_index, retrieve_context
from .agents.question_agent import generate_interview_questions
from .agents.evaluation_agent import evaluate_user_answer
from .agents.feedback_agent import generate_immediate_feedback
from .agents.report_agent import generate_interview_report

# ==========================================
# Authentication Views
# ==========================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
        
    if request.method == "POST":
        u = request.POST.get("username")
        p = request.POST.get("password")
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            messages.success(request, "Welcome back!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, "login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
        
    if request.method == "POST":
        u = request.POST.get("username")
        e = request.POST.get("email")
        p = request.POST.get("password")
        pc = request.POST.get("password_confirm")
        
        if p != pc:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")
            
        if User.objects.filter(username=u).exists():
            messages.error(request, "Username already exists.")
            return render(request, "register.html")
            
        user = User.objects.create_user(username=u, email=e, password=p)
        # Initialize UserProfile
        UserProfile.objects.create(user=user)
        
        login(request, user)
        messages.success(request, "Registration successful! Welcome aboard.")
        return redirect("dashboard")
        
    return render(request, "register.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

# ==========================================
# Core Dashboards & Resume Processing
# ==========================================

@login_required
def dashboard(request):
    # Ensure profile exists
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    sessions = InterviewSession.objects.filter(user=request.user).order_by("-created_at")
    
    return render(request, "dashboard.html", {
        "profile": profile,
        "sessions": sessions
    })


@login_required
def upload_resume(request):
    if request.method == "POST" and request.FILES.get("resume"):
        resume_file = request.FILES["resume"]
        profile = request.user.profile
        
        # Save file to model
        profile.resume = resume_file
        profile.save()
        
        try:
            # 1. Parse text from PDF
            pdf_path = profile.resume.path
            parsed_text = extract_text_from_pdf(pdf_path)
            profile.parsed_text = parsed_text
            profile.save()
            
            # 2. Extract structured analysis via Resume Agent
            analysis = analyze_resume(parsed_text)
            profile.analysis_json = analysis
            profile.ats_score = int(analysis.get("ats_score", 0))
            profile.save()
            
            # 3. Create FAISS RAG index
            build_rag_index(request.user.id, parsed_text)
            
            messages.success(request, "Resume processed successfully! ATS Score generated.")
        except Exception as e:
            messages.error(request, f"Error processing resume: {str(e)}")
            
    return redirect("dashboard")

# ==========================================
# Interview Actions & Setup
# ==========================================

@login_required
def setup_interview(request):
    profile = request.user.profile
    if not profile.resume:
        messages.error(request, "Please upload a resume before setting up an interview.")
        return redirect("dashboard")
        
    if request.method == "POST":
        company = request.POST.get("company")
        job_role = request.POST.get("job_role")
        difficulty = request.POST.get("difficulty", "Medium")
        
        # Create new Interview Session
        session = InterviewSession.objects.create(
            user=request.user,
            company=company,
            job_role=job_role,
            difficulty=difficulty,
            status="in_progress"
        )
        
        try:
            # Query relevant context chunks using RAG Agent
            rag_query = f"{job_role} position at {company} details, candidate skills, experience and matching projects"
            context = retrieve_context(request.user.id, rag_query, k=3)
            
            session.resume_summary = context
            session.save()
            
            # Generate 5 personalized questions via Question Generation Agent
            questions_data = generate_interview_questions(
                company=company,
                job_role=job_role,
                difficulty=difficulty,
                resume_analysis=profile.analysis_json,
                rag_context=context
            )
            
            # Save generated questions to DB
            for idx, q_item in enumerate(questions_data.get("questions", [])):
                InterviewQuestion.objects.create(
                    session=session,
                    question_text=q_item.get("question_text"),
                    category=q_item.get("category"),
                    order=q_item.get("order", idx + 1)
                )
                
            return redirect("interview_room", session_id=session.id)
            
        except Exception as e:
            session.delete()  # Clean up failed session
            messages.error(request, f"Failed to setup interview: {str(e)}")
            return redirect("setup_interview")
            
    return render(request, "setup_interview.html")


@login_required
def interview_room(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    if session.status == "completed":
        return redirect("interview_report", session_id=session.id)
        
    questions = session.questions.all().order_by("order")
    questions_list = []
    for q in questions:
        questions_list.append({
            "id": q.id,
            "question_text": q.question_text,
            "category": q.category,
            "order": q.order
        })
        
    return render(request, "interview.html", {
        "session": session,
        "questions_json": questions_list
    })

# ==========================================
# APIs & Scoring Endpoints
# ==========================================

@login_required
def submit_answer_api(request, session_id):
    """
    Submits user speech transcript answer and voice metrics, saving them to DB.
    Evaluation is deferred to the end of the interview.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        q_id = data.get("question_id")
        answer = data.get("answer")
        voice_metrics = data.get("voice_metrics")
        
        question = get_object_or_404(InterviewQuestion, id=q_id, session=session)
        
        # Save transcript and voice metrics
        question.user_response = answer
        question.voice_metrics_json = voice_metrics
        question.save()
        
        return JsonResponse({
            "success": True
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def evaluate_single_question(q, company, job_role):
    """
    Helper function to evaluate a single question using LLM and cache results.
    """
    if not q.evaluation_json:
        eval_data = evaluate_user_answer(
            company=company,
            job_role=job_role,
            question_text=q.question_text,
            category=q.category,
            user_response=q.user_response or ""
        )
        q.evaluation_json = eval_data
        q.score = int(eval_data.get("score", 0))
        q.save()
    return q


@login_required
def interview_report(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    questions = session.questions.all().order_by("order")
    
    # If the session is in_progress but all questions have user_responses, compile report.
    if session.status == "in_progress":
        answered_count = questions.exclude(user_response__isnull=True).exclude(user_response="").count()
        if answered_count == questions.count() and questions.count() > 0:
            try:
                # 1. Run all evaluations in parallel to speed up bulk compilation
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [
                        executor.submit(evaluate_single_question, q, session.company, session.job_role)
                        for q in questions
                    ]
                    evaluated_questions = [future.result() for future in futures]

                # 2. Format question evaluations for the Report Agent
                questions_evals = []
                for q in evaluated_questions:
                    questions_evals.append({
                        "order": q.order,
                        "category": q.category,
                        "question_text": q.question_text,
                        "user_response": q.user_response,
                        "score": q.score,
                        "evaluation_json": q.evaluation_json,
                        "voice_metrics_json": q.voice_metrics_json
                    })
                    
                # Compile Report via Report Agent
                report_data = generate_interview_report(
                    company=session.company,
                    job_role=session.job_role,
                    difficulty=session.difficulty,
                    resume_analysis=request.user.profile.analysis_json,
                    questions_evaluations=questions_evals
                )
                
                # Save report metrics to DB and mark as complete
                session.overall_score = int(report_data.get("overall_score", 0))
                session.report_json = report_data
                session.status = "completed"
                session.save()
                
            except Exception as e:
                messages.error(request, f"Error compiling interview report: {str(e)}")
                return redirect("dashboard")
        else:
            messages.warning(request, "Please complete all questions before checking the report.")
            return redirect("interview_room", session_id=session.id)
            
    return render(request, "report.html", {
        "session": session,
        "report": session.report_json,
        "questions": questions
    })

