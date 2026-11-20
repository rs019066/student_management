from django import forms
from .models import Course, Department, Enrollment, Subject


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code", "description"]


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["department", "name", "code", "duration_years", "description", "is_active"]


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["course", "name", "code", "credits", "semester", "is_active"]


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["student", "course", "academic_year", "status"]
