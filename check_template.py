from django.template.loader import get_template
from django.template import TemplateDoesNotExist

names = [
    "base.html", "base_public.html",
    "includes/message.html", "includes/sidebar.html",
    "pages/home.html", "pages/about.html", "pages/contact.html", "pages/signup.html",
    "accounts/login.html", "accounts/password_change.html",
    "accounts/admin_dashboard.html", "accounts/teacher_dashboard.html", "accounts/student_dashboard.html",
]
for n in names:
    try:
        get_template(n)
        print("OK   ", n)
    except TemplateDoesNotExist:
        print("MISSING", n)