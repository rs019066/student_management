from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Exam(models.Model):
    name = models.CharField(max_length=100, help_text="Example: Midterm, Final")
    subject = models.ForeignKey("courses.Subject", on_delete=models.PROTECT, related_name="exams")
    date = models.DateField()
    full_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    pass_marks = models.DecimalField(max_digits=6, decimal_places=2, default=40)

    class Meta:
        ordering = ["-date", "subject"]
        constraints = [models.UniqueConstraint(fields=["subject", "name"], name="unique_exam_name_per_subject")]

    def clean(self):
        if self.full_marks is not None and self.pass_marks is not None and self.pass_marks > self.full_marks:
            raise ValidationError("Pass marks cannot be higher than full marks.")

    def __str__(self):
        return f"{self.name} - {self.subject.name}"


class Result(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="results")
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT, related_name="results")
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    remarks = models.CharField(max_length=200, blank=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["exam__date", "exam__subject"]
        constraints = [models.UniqueConstraint(fields=["student", "exam"], name="unique_result_per_exam")]

    def clean(self):
        if self.exam_id is None or self.marks_obtained is None:
            return
        if self.marks_obtained < 0 or self.marks_obtained > self.exam.full_marks:
            raise ValidationError("Marks must be between 0 and the full marks of the exam.")

    @property
    def percentage(self):
        return round(self.marks_obtained / self.exam.full_marks * 100, 2)

    @property
    def passed(self):
        return self.marks_obtained >= self.exam.pass_marks

    @property
    def grade(self):
        if not self.passed:
            return "F"
        p = self.percentage
        if p >= 80:
            return "A"
        if p >= 70:
            return "B"
        if p >= 60:
            return "C"
        return "D"

    def __str__(self):
        return f"{self.student} - {self.exam}: {self.marks_obtained}"