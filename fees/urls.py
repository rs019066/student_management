from django.urls import path
from . import views

app_name = "fees"
urlpatterns = [
    path("", views.fee_list, name="list"),
    path("structures/", views.fee_structure_list, name="structures"),
]
