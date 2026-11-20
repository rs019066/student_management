from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "phone", "admission_date")
    search_fields = ("student_id", "user__username", "user__first_name", "user__last_name", "user__email")
    list_filter = ("admission_date",)

    @admin.display(description="Name")
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
