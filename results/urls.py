from django.urls import path
from . import views

app_name = "results"
urlpatterns = [
    path("", views.exam_list, name="exams"),
    path("exams/add/", views.exam_create, name="exam_add"),
    path("exams/<int:pk>/marks/", views.marks_entry, name="marks"),
    path("my/", views.my_results, name="my"),
    path("report-card/<int:student_pk>/", views.report_card, name="report_card"),
]