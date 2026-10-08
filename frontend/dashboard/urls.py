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
]