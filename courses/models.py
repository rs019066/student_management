from django.db import models
from django.conf import settings

class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="courses")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, unique=True)
    duration_years = models.PositiveSmallIntegerField(default=4)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Subject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30)
    credits = models.PositiveSmallIntegerField(default=3)
    semester = models.PositiveSmallIntegerField(default=1)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_subjects",
        limit_choices_to={"role": "teacher"},
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["course", "semester", "name"]
        constraints = [models.UniqueConstraint(fields=["course", "code"], name="unique_subject_code_per_course")]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        DROPPED = "dropped", "Dropped"

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="enrollments")
    academic_year = models.CharField(max_length=9, help_text="Example: 2026-2027")
    enrolled_on = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-enrolled_on"]
        constraints = [models.UniqueConstraint(fields=["student", "course", "academic_year"], name="unique_student_course_academic_year")]

    def __str__(self):
        return f"{self.student} - {self.course} ({self.academic_year})"
