from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import AttendanceForm
from .models import Attendance


@login_required
def attendance_list(request):
    records = Attendance.objects.select_related("student__user", "subject")
    return render(request, "attendance/attendance_list.html", {"records": records})


@login_required
def attendance_create(request):
    form = AttendanceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("attendance:list")
    return render(request, "attendance/attendance_form.html", {"form": form})
