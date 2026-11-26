from django import forms
from .models import Attendance


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["student", "subject", "date", "status", "remarks"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css)
        if "date" in self.fields:
            self.fields["date"].widget = forms.DateInput(attrs={"type": "date", "class": "form-control"})