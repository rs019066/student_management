from django.urls import path
from . import views

app_name = "courses"
urlpatterns = [
    path("", views.course_list, name="list"),
    path("departments/", views.department_list, name="departments"),
    path("departments/add/", views.department_create, name="department_add"),
    path("add/", views.course_create, name="add"),
    path("<int:pk>/edit/", views.course_update, name="edit"),
    path("subjects/", views.subject_list, name="subjects"),
    path("subjects/add/", views.subject_create, name="subject_add"),
    path("enrollments/", views.enrollment_list, name="enrollments"),
    path("enrollments/add/", views.enrollment_create, name="enrollment_add"),
]
