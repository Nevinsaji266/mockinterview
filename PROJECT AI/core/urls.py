from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("interview/setup/", views.interview_setup, name="interview_setup"),
    path("interview/<int:session_id>/", views.interview_room, name="interview_room"),
    path("interview/<int:session_id>/submit/", views.submit_answer, name="submit_answer"),
    path("interview/<int:session_id>/complete/", views.complete_interview, name="complete_interview"),
    path("interview/<int:session_id>/report/", views.interview_report, name="interview_report"),
]
