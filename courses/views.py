from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from .forms import CourseForm, DepartmentForm, EnrollmentForm, SubjectForm
from .models import Course, Department, Enrollment, Subject


def _save_form(request, form_class, *, instance=None, redirect_to, title, success):
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, success)
        return redirect(redirect_to)
    return render(request, "courses/form.html", {"form": form, "object": instance, "title": title})


# ---------- Departments ----------
@role_required("admin")
def department_list(request):
    return render(request, "courses/department_list.html", {"departments": Department.objects.all()})


@role_required("admin")
def department_create(request):
    return _save_form(request, DepartmentForm, redirect_to="courses:departments",
                      title="Add department", success="Department created successfully.")


# ---------- Courses ----------
@role_required("admin")
def course_list(request):
    query = request.GET.get("q", "").strip()
    courses = Course.objects.select_related("department")
    if query:
        courses = courses.filter(Q(name__icontains=query) | Q(code__icontains=query))
    return render(request, "courses/course_list.html", {"courses": courses, "query": query})


@role_required("admin")
def course_create(request):
    return _save_form(request, CourseForm, redirect_to="courses:list",
                      title="Add course", success="Course created successfully.")


@role_required("admin")
def course_update(request, pk):
    return _save_form(request, CourseForm, instance=get_object_or_404(Course, pk=pk),
                      redirect_to="courses:list", title="Edit course",
                      success="Course updated successfully.")


# ---------- Subjects ----------
@role_required("admin", "teacher")
def subject_list(request):
    subjects = Subject.objects.select_related("course", "teacher")
    if request.user.role == "teacher" and not request.user.is_superuser:
        subjects = subjects.filter(teacher=request.user)
    return render(request, "courses/subject_list.html", {"subjects": subjects})


@role_required("admin")
def subject_create(request):
    return _save_form(request, SubjectForm, redirect_to="courses:subjects",
                      title="Add subject", success="Subject created successfully.")


# ---------- Enrollments ----------
@role_required("admin")
def enrollment_list(request):
    enrollments = Enrollment.objects.select_related("student__user", "course")
    return render(request, "courses/enrollment_list.html", {"enrollments": enrollments})


@role_required("admin")
def enrollment_create(request):
    return _save_form(request, EnrollmentForm, redirect_to="courses:enrollments",
                      title="Add enrollment", success="Enrollment created successfully.")