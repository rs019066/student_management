from django import forms
from .models import Course, Department, Enrollment, Subject


class BootstrapMixin:
    """Add Bootstrap classes to every field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class DepartmentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class CourseForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ["department", "name", "code", "duration_years", "description", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class SubjectForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["course", "name", "code", "credits", "semester", "teacher", "is_active"]


class EnrollmentForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["student", "course", "academic_year", "status"]