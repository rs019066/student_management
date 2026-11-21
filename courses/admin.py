from django.contrib import admin
from .models import Course, Department, Enrollment, Subject


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "department", "duration_years", "is_active")
    list_filter = ("department", "is_active")
    search_fields = ("code", "name")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "course", "semester", "credits", "is_active")
    list_filter = ("course", "semester", "is_active")
    search_fields = ("code", "name")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "academic_year", "status", "enrolled_on")
    list_filter = ("status", "academic_year", "course")
    search_fields = ("student__student_id", "student__user__username", "course__name")
