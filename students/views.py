from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import StudentForm
from .models import Student


@login_required
def student_list(request):
    query = request.GET.get("q", "").strip()
    students = Student.objects.select_related("user")
    if query:
        students = students.filter(student_id__icontains=query) | students.filter(user__username__icontains=query) | students.filter(user__first_name__icontains=query) | students.filter(user__last_name__icontains=query)
    return render(request, "students/student_list.html", {"students": students, "query": query})


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related("user"), pk=pk)
    return render(request, "students/student_detail.html", {"student": student})


@login_required
def student_create(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student created successfully.")
        return redirect("students:detail", pk=form.instance.pk)
    return render(request, "students/student_form.html", {"form": form, "title": "Add student"})


@login_required
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Student updated successfully.")
        return redirect("students:detail", pk=student.pk)
    return render(request, "students/student_form.html", {"form": form, "title": "Edit student"})


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.user.delete()
        messages.success(request, "Student deleted successfully.")
        return redirect("students:list")
    return render(request, "students/student_confirm_delete.html", {"student": student})
