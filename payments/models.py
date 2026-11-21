from django.db import models

# Create your models here.
import uuid

from django.conf import settings
from django.db import models


def new_transaction_id():
    return uuid.uuid4().hex


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank voucher"
        ESEWA = "esewa", "eSewa"
        KHALTI = "khalti", "Khalti"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    student_fee = models.ForeignKey("fees.StudentFee", on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=Method.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField(max_length=64, unique=True, default=new_transaction_id, editable=False)
    gateway_reference = models.CharField(max_length=120, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def receipt_number(self):
        return f"RCPT-{self.pk:06d}"

    def __str__(self):
        return f"{self.transaction_id[:8]} - {self.amount} ({self.status})"