from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from students.models import Student
from .models import ContactMessage

User = get_user_model()


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


def _next_student_id():
    n = (Student.objects.order_by("-id").values_list("id", flat=True).first() or 0) + 1
    while Student.objects.filter(student_id=f"S{n:04d}").exists():
        n += 1
    return f"S{n:04d}"


class StudentSignupForm(BootstrapMixin, forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=25, required=False)
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "The two passwords do not match.")
            else:
                candidate = User(
                    username=cleaned.get("username", ""), email=cleaned.get("email", ""),
                    first_name=cleaned.get("first_name", ""), last_name=cleaned.get("last_name", ""),
                )
                try:
                    validate_password(p1, candidate)
                except ValidationError as exc:
                    self.add_error("password1", exc)
        return cleaned

    @transaction.atomic
    def save(self):
        d = self.cleaned_data
        user = User(
            username=d["username"], email=d["email"],
            first_name=d["first_name"], last_name=d["last_name"],
            role=User.Role.STUDENT,
        )
        user.set_password(d["password1"])
        user.save()
        Student.objects.create(user=user, student_id=_next_student_id(), phone=d["phone"])
        return user


class ContactForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}