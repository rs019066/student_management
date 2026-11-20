from django.contrib import admin
from .models import Exam, Result


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "date", "full_marks", "pass_marks")
    list_filter = ("subject__course", "date")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "marks_obtained", "grade")
    list_filter = ("exam",)