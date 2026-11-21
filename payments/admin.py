from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "student_fee", "amount", "method", "status", "paid_at")
    list_filter = ("status", "method")
    readonly_fields = ("transaction_id", "created_at", "paid_at")