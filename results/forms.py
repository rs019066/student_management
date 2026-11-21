from django import forms
from .models import Exam


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["name", "subject", "date", "full_marks", "pass_marks"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css)