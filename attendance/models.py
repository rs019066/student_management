from django.db import models


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="attendance_records")
    subject = models.ForeignKey("courses.Subject", on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "student"]
        constraints = [models.UniqueConstraint(fields=["student", "subject", "date"], name="unique_attendance_per_day")]

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date}"
