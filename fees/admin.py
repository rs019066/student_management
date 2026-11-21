from django.contrib import admin
from .models import FeeStructure, StudentFee


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "amount", "due_date", "is_active")
    list_filter = ("course", "is_active")


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = ("student", "fee_structure", "amount_due", "amount_paid", "status")
    list_filter = ("status", "fee_structure")
    search_fields = ("student__student_id", "student__user__username")