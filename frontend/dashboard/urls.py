from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
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
    path("evaluation-history/", views.evaluation_history, name="evaluation_history"),
    path("monitoring/", views.monitoring_dashboard, name="monitoring"),
]