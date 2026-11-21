from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.utils import timezone
from fees.models import StudentFee

from accounts.decorators import role_required
from attendance.models import Attendance
from courses.models import Subject
from results.models import Exam, Result
from students.models import Student
from .utils import csv_response, pdf_response
from courses.models import Course, Subject

LOW_ATTENDANCE = 75  # percent; below this the row is shown in red


def _is_teacher(user):
    return user.role == "teacher" and not user.is_superuser


def _subjects_for(user):
    subjects = Subject.objects.filter(is_active=True).select_related("course")
    return subjects.filter(teacher=user) if _is_teacher(user) else subjects


def _exams_for(user):
    exams = Exam.objects.select_related("subject__course")
    return exams.filter(subject__teacher=user) if _is_teacher(user) else exams


def _name(student):
    return student.user.get_full_name() or student.user.username


def _num(value):
    return format(value.normalize(), "f")


def _export(kind, filename, title, subtitle, headers, rows):
    if kind == "csv":
        return csv_response(filename, headers, rows)
    return pdf_response(filename, title, subtitle, headers, rows)


@role_required("admin", "teacher")
def report_home(request):
    return render(request, "reports/home.html")


# ---------- Attendance summary ----------
ATTENDANCE_HEADERS = ["Student ID", "Name", "Total", "Present", "Late", "Absent", "Excused", "Attendance %"]


def _attendance_rows(subject, date_from, date_to):
    records = Attendance.objects.filter(subject=subject)
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    stats = {
        r["student"]: r
        for r in records.values("student").annotate(
            total=Count("id"),
            present=Count("id", filter=Q(status="present")),
            late=Count("id", filter=Q(status="late")),
            absent=Count("id", filter=Q(status="absent")),
            excused=Count("id", filter=Q(status="excused")),
        )
    }
    students = (
        Student.objects.filter(Q(enrollments__course=subject.course, enrollments__status="active")
                               | Q(attendance_records__subject=subject))
        .select_related("user").distinct().order_by("student_id")
    )
    rows = []
    for s in students:
        st = stats.get(s.pk)
        if st:
            percentage = round((st["present"] + st["late"]) / st["total"] * 100, 1)
            row = {"total": st["total"], "present": st["present"], "late": st["late"],
                   "absent": st["absent"], "excused": st["excused"], "percentage": percentage}
        else:
            row = {"total": 0, "present": 0, "late": 0, "absent": 0, "excused": 0, "percentage": None}
        row.update({"student_id": s.student_id, "name": _name(s)})
        row["low"] = row["percentage"] is not None and row["percentage"] < LOW_ATTENDANCE
        rows.append(row)
    return rows


@role_required("admin", "teacher")
def attendance_summary(request):
    subjects = _subjects_for(request.user)
    subject_id = request.GET.get("subject", "")
    subject = subjects.filter(pk=subject_id).first() if subject_id.isdigit() else None
    date_from = parse_date(request.GET.get("date_from") or "")
    date_to = parse_date(request.GET.get("date_to") or "")

    rows = []
    if subject:
        if date_from and date_to and date_from > date_to:
            messages.error(request, "The start date must be before the end date.")
        else:
            rows = _attendance_rows(subject, date_from, date_to)
            kind = request.GET.get("export")
            if rows and kind in ("csv", "pdf"):
                period = f"{date_from or 'start'} to {date_to or 'today'}"
                data = [
                    [r["student_id"], r["name"], r["total"], r["present"], r["late"], r["absent"], r["excused"],
                     f'{r["percentage"]}%' if r["percentage"] is not None else "-"]
                    for r in rows
                ]
                return _export(
                    kind, f"attendance_{slugify(subject.code)}",
                    "Attendance Summary",
                    f"{subject.code} - {subject.name} | {subject.course.name} | {period}",
                    ATTENDANCE_HEADERS, data,
                )

    params = request.GET.copy()
    params.pop("export", None)
    return render(request, "reports/attendance.html", {
        "subjects": subjects, "subject": subject, "rows": rows,
        "date_from": date_from, "date_to": date_to,
        "querystring": params.urlencode(), "low_limit": LOW_ATTENDANCE,
    })


# ---------- Result sheet ----------
RESULT_HEADERS = ["Student ID", "Name", "Marks", "Full marks", "Percentage", "Grade", "Result"]


def _result_rows(exam):
    results = {r.student_id: r for r in Result.objects.filter(exam=exam)}
    students = (
        Student.objects.filter(Q(enrollments__course=exam.subject.course, enrollments__status="active")
                               | Q(results__exam=exam))
        .select_related("user").distinct().order_by("student_id")
    )
    rows = []
    for s in students:
        r = results.get(s.pk)
        if r:
            rows.append({
                "student_id": s.student_id, "name": _name(s),
                "marks": _num(r.marks_obtained), "percentage": f"{r.percentage}%",
                "grade": r.grade, "status": "Pass" if r.passed else "Fail",
            })
        else:
            rows.append({
                "student_id": s.student_id, "name": _name(s),
                "marks": "-", "percentage": "-", "grade": "-", "status": "Not entered",
            })
    entered = list(results.values())
    summary = {
        "students": len(rows),
        "entered": len(entered),
        "passed": sum(1 for r in entered if r.passed),
        "average": round(sum(r.marks_obtained for r in entered) / len(entered), 2) if entered else None,
        "highest": max((r.marks_obtained for r in entered), default=None),
    }
    return rows, summary


@role_required("admin", "teacher")
def result_sheet(request):
    exams = _exams_for(request.user)
    exam_id = request.GET.get("exam", "")
    exam = exams.filter(pk=exam_id).first() if exam_id.isdigit() else None

    rows, summary = [], None
    if exam:
        rows, summary = _result_rows(exam)
        kind = request.GET.get("export")
        if rows and kind in ("csv", "pdf"):
            data = [[r["student_id"], r["name"], r["marks"], _num(exam.full_marks),
                     r["percentage"], r["grade"], r["status"]] for r in rows]
            return _export(
                kind, f"results_{slugify(exam.subject.code)}_{slugify(exam.name)}",
                "Result Sheet",
                f"{exam.name} | {exam.subject.code} - {exam.subject.name} | {exam.date:%Y-%m-%d} | "
                f"Full marks {_num(exam.full_marks)}, pass marks {_num(exam.pass_marks)}",
                RESULT_HEADERS, data,
            )

    params = request.GET.copy()
    params.pop("export", None)
    return render(request, "reports/results.html", {
        "exams": exams, "exam": exam, "rows": rows, "summary": summary,
        "querystring": params.urlencode(),
    })

# ---------- Fee report (admin only) ----------
FEE_HEADERS = ["Student ID", "Name", "Fee", "Due date", "Amount due", "Paid", "Balance", "Status"]


@role_required("admin")
def fee_report(request):
    today = timezone.localdate()
    courses = Course.objects.order_by("code")
    course_id = request.GET.get("course", "")
    status = request.GET.get("status", "")

    fees = StudentFee.objects.select_related("student__user", "fee_structure__course")
    course = None
    if course_id.isdigit():
        course = courses.filter(pk=course_id).first()
        if course:
            fees = fees.filter(fee_structure__course=course)
    if status in dict(StudentFee.Status.choices):
        fees = fees.filter(status=status)
    else:
        status = ""
    fees = list(fees.order_by("student__student_id", "fee_structure__name"))

    counted = [f for f in fees if f.status != StudentFee.Status.WAIVED]
    total_due = sum((f.amount_due for f in counted), 0)
    total_paid = sum((f.amount_paid for f in counted), 0)
    totals = {"due": total_due, "paid": total_paid, "balance": max(total_due - total_paid, 0)}

    rows = [{
        "fee": f,
        "name": _name(f.student),
        "overdue": bool(f.fee_structure.due_date and f.fee_structure.due_date < today and f.balance > 0),
    } for f in fees]

    kind = request.GET.get("export")
    if rows and kind in ("csv", "pdf"):
        data = [[
            r["fee"].student.student_id, r["name"], r["fee"].fee_structure.name,
            r["fee"].fee_structure.due_date or "-",
            _num(r["fee"].amount_due), _num(r["fee"].amount_paid), _num(r["fee"].balance),
            r["fee"].get_status_display(),
        ] for r in rows]
        data.append(["", "TOTAL", "", "", _num(totals["due"]), _num(totals["paid"]), _num(totals["balance"]), ""])
        label = course.code if course else "All courses"
        return _export(kind, "fee_report", "Fee Report",
                       f"{label} | {dict(StudentFee.Status.choices).get(status, 'All statuses')} | {today}",
                       FEE_HEADERS, data)

    params = request.GET.copy()
    params.pop("export", None)
    return render(request, "reports/fees.html", {
        "rows": rows, "totals": totals, "courses": courses, "course": course,
        "status": status, "statuses": StudentFee.Status.choices,
        "querystring": params.urlencode(),
    })