from django import forms
from django.contrib.auth import get_user_model
from .models import Student

User = get_user_model()


class StudentForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Required when creating a student.")

    class Meta:
        model = Student
        fields = ["student_id", "date_of_birth", "phone", "address", "admission_date"]
        widgets = {"date_of_birth": forms.DateInput(attrs={"type": "date"}), "admission_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            user = self.instance.user
            for name in ("username", "email", "first_name", "last_name"):
                self.fields[name].initial = getattr(user, name)
            self.fields["password"].required = False

            for field in self.fields.values():
                field.widget.attrs.setdefault("class", "form-control")

            self.fields["username"].widget.attrs["autocomplete"] = "off"
            self.fields["password"].widget.attrs["autocomplete"] = "new-password"

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = User.objects.filter(username=username)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError("That username is already in use.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.instance.pk and not password:
            raise forms.ValidationError("A password is required for a new student.")
        return password

    def save(self, commit=True):
        student = super().save(commit=False)
        user = student.user if student.pk else User()
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.role = User.Role.STUDENT
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            student.user = user
            student.save()
        return student
