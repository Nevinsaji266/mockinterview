from django.contrib import admin
from .models import UserProfile, InterviewSession, InterviewQuestion

admin.site.register(UserProfile)
admin.site.register(InterviewSession)
admin.site.register(InterviewQuestion)
