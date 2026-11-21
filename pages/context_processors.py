from django.conf import settings

SITE = {
    "name": "Student Management System",
    "college": "Your College Name",
    "address": "Your address, City, Nepal",
    "phone": "+977-00-0000000",
    "email": "info@example.com",
    "hours": "Sunday to Friday, 10:00 AM to 5:00 PM",
}


def site(request):
    return {"site": SITE, "allow_signup": getattr(settings, "ALLOW_STUDENT_SIGNUP", True)}