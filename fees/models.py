from django.db import models
from decimal import Decimal

class FeeStructure(models.Model):
    name = models.CharField(max_length=120)
    course = models.ForeignKey("courses.Course", on_delete=models.PROTECT, related_name="fee_structures")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["course", "name"]

    def __str__(self):
        return f"{self.name} - {self.course}"


class StudentFee(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partial"
        PAID = "paid", "Paid"
        WAIVED = "waived", "Waived"

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="fees")
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.PROTECT, related_name="student_fees")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    assigned_on = models.DateField(auto_now_add=True)
    paid_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-assigned_on"]
        constraints = [models.UniqueConstraint(fields=["student", "fee_structure"], name="unique_fee_per_student_structure")]

    def __str__(self):
        return f"{self.student} - {self.fee_structure.name}"
    @property
    def balance(self):
        if self.status == self.Status.WAIVED:
            return Decimal("0")
        return max(self.amount_due - self.amount_paid, Decimal("0"))