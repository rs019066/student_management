from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.decorators import role_required
from courses.models import Subject
from students.models import Student
from .forms import AttendanceForm
from .models import Attendance


def _subjects_for(user):
    """Admins see all active subjects, teachers only their own."""
    subjects = Subject.objects.filter(is_active=True).select_related("course")
    if user.role == "teacher" and not user.is_superuser:
        subjects = subjects.filter(teacher=user)
    return subjects


@login_required
def attendance_list(request):
    user = request.user
    records = Attendance.objects.select_related("student__user", "subject")
    if user.is_superuser or user.role == "admin":
        pass
    elif user.role == "teacher":
        records = records.filter(subject__teacher=user)
    else:
        records = records.filter(student__user=user)
    return render(request, "attendance/attendance_list.html", {"records": records})


@role_required("admin", "teacher")
def attendance_create(request):
    form = AttendanceForm(request.POST or None)
    if request.user.role == "teacher" and not request.user.is_superuser and "subject" in form.fields:
        form.fields["subject"].queryset = Subject.objects.filter(teacher=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Attendance saved.")
        return redirect("attendance:list")
    return render(request, "attendance/attendance_form.html", {"form": form})


@role_required("admin", "teacher")
def attendance_mark(request):
    subjects = _subjects_for(request.user)
    today = timezone.localdate()

    data = request.POST if request.method == "POST" else request.GET
    subject_id = data.get("subject")
    attendance_date = parse_date(data.get("date") or "") or today
    subject = subjects.filter(pk=subject_id).first() if subject_id and subject_id.isdigit() else None

    rows = []
    if subject:
        students = (
            Student.objects.filter(enrollments__course=subject.course, enrollments__status="active")
            .select_related("user")
            .distinct()
            .order_by("student_id")
        )
        valid_statuses = dict(Attendance.Status.choices)

        if request.method == "POST":
            if attendance_date > today:
                messages.error(request, "You cannot mark attendance for a future date.")
            else:
                for s in students:
                    status = request.POST.get(f"status_{s.pk}")
                    if status not in valid_statuses:
                        continue
                    Attendance.objects.update_or_create(
                        student=s, subject=subject, date=attendance_date,
                        defaults={"status": status,
                                  "remarks": request.POST.get(f"remarks_{s.pk}", "").strip()[:255]},
                    )
                messages.success(request, f"Attendance saved for {students.count()} students.")
                return redirect(f"{reverse('attendance:mark')}?subject={subject.pk}&date={attendance_date.isoformat()}")

        existing = {r.student_id: r for r in Attendance.objects.filter(subject=subject, date=attendance_date)}
        for s in students:
            record = existing.get(s.pk)
            rows.append({
                "student": s,
                "status": record.status if record else "present",
                "remarks": record.remarks if record else "",
            })

    return render(request, "attendance/mark.html", {
        "subjects": subjects,
        "subject": subject,
        "date": attendance_date,
        "today": today,
        "rows": rows,
        "statuses": Attendance.Status.choices,
    })