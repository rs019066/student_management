from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from attendance.models import Attendance
from courses.models import Course, Enrollment, Subject
from results.models import Exam, Result
from students.models import Student
from .decorators import role_required
from .models import User

ATTENDED = ["present", "late"]


@login_required
def dashboard(request):
    """Send each user to the dashboard for their role."""
    user = request.user
    if user.is_superuser or user.role == "admin":
        return redirect("accounts:admin_dashboard")
    if user.role == "teacher":
        return redirect("accounts:teacher_dashboard")
    return redirect("accounts:student_dashboard")


@role_required("admin")
def admin_dashboard(request):
    today = timezone.localdate()
    today_records = Attendance.objects.filter(date=today)
    today_total = today_records.count()
    today_attended = today_records.filter(status__in=ATTENDED).count()
    context = {
        "student_count": Student.objects.count(),
        "teacher_count": User.objects.filter(role="teacher").count(),
        "course_count": Course.objects.filter(is_active=True).count(),
        "subject_count": Subject.objects.filter(is_active=True).count(),
        "enrollment_count": Enrollment.objects.filter(status="active").count(),
        "today_total": today_total,
        "today_percentage": round(today_attended / today_total * 100, 1) if today_total else None,
        "recent_students": Student.objects.select_related("user").order_by("-id")[:5],
        "recent_exams": Exam.objects.select_related("subject")[:5],
    }
    return render(request, "accounts/admin_dashboard.html", context)


@role_required("teacher")
def teacher_dashboard(request):
    user = request.user
    subjects = Subject.objects.filter(teacher=user, is_active=True).select_related("course")
    subject_rows = [
        {
            "subject": s,
            "student_count": Enrollment.objects.filter(course=s.course, status="active").count(),
        }
        for s in subjects
    ]
    recent_sessions = (
        Attendance.objects.filter(subject__teacher=user)
        .values("subject__name", "date")
        .annotate(total=Count("id"))
        .order_by("-date")[:5]
    )
    exams = (
        Exam.objects.filter(subject__teacher=user)
        .select_related("subject")
        .annotate(result_count=Count("results"))[:5]
    )
    context = {
        "subject_rows": subject_rows,
        "recent_sessions": recent_sessions,
        "exams": exams,
    }
    return render(request, "accounts/teacher_dashboard.html", context)


@role_required("student")
def student_dashboard(request):
    student = Student.objects.filter(user=request.user).select_related("user").first()
    context = {"student": student}
    if student:
        records = Attendance.objects.filter(student=student)
        total = records.count()
        attended = records.filter(status__in=ATTENDED).count()
        totals = Result.objects.filter(student=student).aggregate(m=Sum("marks_obtained"), f=Sum("exam__full_marks"))
        context.update({
            "enrollments": student.enrollments.filter(status="active").select_related("course"),
            "attendance_total": total,
            "attendance_percentage": round(attended / total * 100, 1) if total else None,
            "result_percentage": round(totals["m"] / totals["f"] * 100, 2) if totals["f"] else None,
            "latest_results": Result.objects.filter(student=student)
                .select_related("exam__subject").order_by("-exam__date")[:5],
        })
    return render(request, "accounts/student_dashboard.html", context)