from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("resume/upload/", views.upload_resume, name="upload_resume"),
    path("interview/setup/", views.setup_interview, name="setup_interview"),
    path("interview/<int:session_id>/", views.interview_room, name="interview_room"),
    path("sessions/<int:session_id>/report/", views.interview_report, name="interview_report"),
    
    # AJAX APIs
    path("api/sessions/<int:session_id>/submit-answer/", views.submit_answer_api, name="submit_answer_api"),
]
