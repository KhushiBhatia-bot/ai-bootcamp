from django.urls import path

from .views import (
    chat_page,
    login_page,
    register_page,
    verify_email_page,
)


urlpatterns = [
    path("", login_page, name="login"),
    path("register/", register_page, name="register"),
    path("verify-email/", verify_email_page, name="verify-email"),
    path("chat/", chat_page, name="chat"),
]