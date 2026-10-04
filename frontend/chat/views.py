from django.shortcuts import render


def login_page(request):
    return render(request, "chat/login.html")


def register_page(request):
    return render(request, "chat/register.html")


def verify_email_page(request):
    return render(request, "chat/verify_email.html")


def chat_page(request):
    return render(request, "chat/index.html")