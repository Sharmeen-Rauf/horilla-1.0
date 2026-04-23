from django.urls import path

from ai_assistant import views

urlpatterns = [
    path("", views.ai_chat_page, name="ai-assistant"),
    path("chat/", views.ai_chat_api, name="ai-assistant-chat"),
    path("dashboard/", views.ai_dashboard_page, name="ai-dashboard"),
    path("analyze/", views.ai_analyze_api, name="ai-analyze"),
    path("org-health/", views.ai_org_health_api, name="ai-org-health"),
]
