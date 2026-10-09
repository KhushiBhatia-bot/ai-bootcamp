from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("policies/", views.policies, name="policies"),
    path(
        "policies/upload/",
        views.upload_policy,
        name="upload_policy"
    ),
    path(
    "evaluate-policy/",
    views.evaluate_policy_view,
    name="evaluate_policy",
    ),
    path("ask-ai/", views.ask_ai, name="ask_ai"),
    path("compliance/", views.compliance, name="compliance"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("evaluation-history/", views.evaluation_history, name="evaluation_history"),
    path("monitoring/", views.monitoring_dashboard, name="monitoring"),
]