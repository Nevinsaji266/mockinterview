from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """
    Extends the Django User model to store the user's uploaded resume,
    parsed text, extracted structured resume analysis data, and ATS scores.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    resume = models.FileField(upload_to="resumes/", blank=True, null=True)
    parsed_text = models.TextField(blank=True, null=True)
    analysis_json = models.JSONField(blank=True, null=True)  # Stores skills, experience, suggestions, etc.
    ats_score = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class InterviewSession(models.Model):
    """
    Represents a specific mock interview session configured by the user.
    """
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interview_sessions")
    company = models.CharField(max_length=100)
    job_role = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20, default="Medium")  # Easy, Medium, Hard
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    created_at = models.DateTimeField(auto_now_add=True)
    overall_score = models.IntegerField(default=0)
    report_json = models.JSONField(blank=True, null=True)  # Final evaluation summary report details
    resume_summary = models.TextField(blank=True, null=True)  # Context summary generated from RAG/Resume

    def __str__(self):
        return f"{self.user.username} - {self.job_role} at {self.company} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class InterviewQuestion(models.Model):
    """
    Represents individual questions generated for an interview session,
    the user's spoken answer, and the AI evaluation details.
    """
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    category = models.CharField(max_length=50)  # Technical, Behavioral, HR
    user_response = models.TextField(blank=True, null=True)  # Audio transcription text
    evaluation_json = models.JSONField(blank=True, null=True)  # Scores, weaknesses, strengths, model answer
    voice_metrics_json = models.JSONField(blank=True, null=True)  # Speaking rate, filler words, recognition confidence
    feedback_text = models.TextField(blank=True, null=True)  # Real-time constructive response
    score = models.IntegerField(default=0)  # Question level score
    order = models.IntegerField(default=0)  # Order sequence in the interview
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.order} ({self.category}) for Session {self.session.id}"
