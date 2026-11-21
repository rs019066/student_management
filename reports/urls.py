from django.urls import path
from . import views

app_name = "reports"
urlpatterns = [
    path("", views.report_home, name="home"),
    path("attendance/", views.attendance_summary, name="attendance"),
    path("results/", views.result_sheet, name="results"),
]