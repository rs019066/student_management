from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from courses.models import Subject
from students.models import Student
from .forms import ExamForm
from .models import Exam, Result


def _is_teacher(user):
    return user.role == "teacher" and not user.is_superuser


@role_required("admin", "teacher")
def exam_list(request):
    exams = Exam.objects.select_related("subject__course").annotate(result_count=Count("results"))
    if _is_teacher(request.user):
        exams = exams.filter(subject__teacher=request.user)
    return render(request, "results/exam_list.html", {"exams": exams})


@role_required("admin", "teacher")
def exam_create(request):
    form = ExamForm(request.POST or None)
    if _is_teacher(request.user):
        form.fields["subject"].queryset = Subject.objects.filter(teacher=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Exam created. You can enter marks now.")
        return redirect("results:exams")
    return render(request, "results/form.html", {"form": form, "title": "Add exam"})


@role_required("admin", "teacher")
def marks_entry(request, pk):
    exam = get_object_or_404(Exam.objects.select_related("subject__course"), pk=pk)
    user = request.user
    if _is_teacher(user) and exam.subject.teacher_id != user.pk:
        raise PermissionDenied

    students = (
        Student.objects.filter(enrollments__course=exam.subject.course, enrollments__status="active")
        .select_related("user").distinct().order_by("student_id")
    )
    existing = {r.student_id: r for r in Result.objects.filter(exam=exam)}
    entered, errors = {}, {}

    if request.method == "POST":
        for s in students:
            raw = request.POST.get(f"marks_{s.pk}", "").strip()
            remarks = request.POST.get(f"remarks_{s.pk}", "").strip()[:200]
            entered[s.pk] = {"marks": raw, "remarks": remarks}
            if raw == "":
                continue
            try:
                value = Decimal(raw)
            except InvalidOperation:
                errors[s.pk] = "Enter a number."
                continue
            if value < 0 or value > exam.full_marks:
                errors[s.pk] = f"Must be between 0 and {exam.full_marks}."
                continue
            entered[s.pk]["value"] = value

        if not errors:
            saved = 0
            for s in students:
                item = entered.get(s.pk)
                if not item or "value" not in item:
                    continue
                Result.objects.update_or_create(
                    student=s, exam=exam,
                    defaults={"marks_obtained": item["value"], "remarks": item["remarks"], "entered_by": user},
                )
                saved += 1
            messages.success(request, f"Marks saved for {saved} students.")
            return redirect("results:marks", pk=exam.pk)
        messages.error(request, "Fix the highlighted marks and try again.")

    rows = []
    for s in students:
        if s.pk in entered:
            marks, remarks = entered[s.pk]["marks"], entered[s.pk]["remarks"]
        else:
            r = existing.get(s.pk)
            marks = r.marks_obtained if r else ""
            remarks = r.remarks if r else ""
        rows.append({"student": s, "marks": marks, "remarks": remarks, "error": errors.get(s.pk)})

    return render(request, "results/marks_entry.html", {"exam": exam, "rows": rows})


def _report_context(student):
    results = list(
        Result.objects.filter(student=student)
        .select_related("exam__subject").order_by("exam__subject__semester", "exam__date")
    )
    total = sum((r.marks_obtained for r in results), Decimal("0"))
    full = sum((r.exam.full_marks for r in results), Decimal("0"))
    return {
        "student": student,
        "results": results,
        "total": total,
        "full": full,
        "percentage": round(total / full * 100, 2) if full else None,
        "passed_all": all(r.passed for r in results) if results else None,
    }


@role_required("student")
def my_results(request):
    student = Student.objects.filter(user=request.user).select_related("user").first()
    if student is None:
        messages.error(request, "No student profile is linked to your account. Please contact the admin.")
        return redirect("accounts:dashboard")
    return render(request, "results/report_card.html", _report_context(student))


@role_required("admin", "teacher")
def report_card(request, student_pk):
    student = get_object_or_404(Student.objects.select_related("user"), pk=student_pk)
    return render(request, "results/report_card.html", _report_context(student))