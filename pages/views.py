from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.http import Http404
from django.shortcuts import redirect, render

from .forms import ContactForm, StudentSignupForm


def home(request):
    return render(request, "pages/home.html")


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST":
        if request.POST.get("website"):      # hidden field that only bots fill in
            return redirect("pages:contact")
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Your message has been sent. We will get back to you soon.")
            return redirect("pages:contact")
    return render(request, "pages/contact.html", {"form": form})


def signup(request):
    if not getattr(settings, "ALLOW_STUDENT_SIGNUP", True):
        raise Http404
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = StudentSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Welcome! Your account is ready. The admin will enroll you in your course.")
        return redirect("accounts:dashboard")
    return render(request, "pages/signup.html", {"form": form})