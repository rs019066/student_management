from django.urls import path
from . import views

app_name = "fees"
urlpatterns = [
    path("", views.fee_list, name="list"),
    path("<int:pk>/", views.fee_detail, name="detail"),
    path("structures/", views.fee_structure_list, name="structures"),
    path("structures/add/", views.structure_create, name="structure_add"),
    path("structures/<int:pk>/edit/", views.structure_update, name="structure_edit"),
    path("structures/<int:pk>/generate/", views.structure_generate, name="structure_generate"),
]