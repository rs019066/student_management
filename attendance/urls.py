from django.urls import path
from . import views

app_name = "attendance"
urlpatterns = [
    path("", views.attendance_list, name="list"),
    path("add/", views.attendance_create, name="add"),
]
