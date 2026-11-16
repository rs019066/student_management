from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CourseForm, DepartmentForm, EnrollmentForm, SubjectForm
from .models import Course, Department, Enrollment, Subject


def _save_form(request, form_class, instance=None, template="courses/form.html"):
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("courses:list")
    return render(request, template, {"form": form, "object": instance})


@login_required
def course_list(request):
    query = request.GET.get("q", "").strip()
    courses = Course.objects.select_related("department")
    if query:
        courses = courses.filter(name__icontains=query) | courses.filter(code__icontains=query)
    return render(request, "courses/course_list.html", {"courses": courses, "query": query})


@login_required
def department_list(request):
    return render(request, "courses/department_list.html", {"departments": Department.objects.all()})


@login_required
def course_create(request): return _save_form(request, CourseForm)
@login_required
def course_update(request, pk): return _save_form(request, CourseForm, get_object_or_404(Course, pk=pk))
@login_required
def subject_create(request): return _save_form(request, SubjectForm)
@login_required
def enrollment_create(request): return _save_form(request, EnrollmentForm)
@login_required
def department_create(request): return _save_form(request, DepartmentForm)


@login_required
def subject_list(request):
    return render(request, "courses/subject_list.html", {"subjects": Subject.objects.select_related("course")})


@login_required
def enrollment_list(request):
    return render(request, "courses/enrollment_list.html", {"enrollments": Enrollment.objects.select_related("student__user", "course")})
