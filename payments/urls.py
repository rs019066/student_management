from django.urls import path
from . import views

app_name = "payments"
urlpatterns = [
    path("", views.payment_list, name="list"),
    path("start/<int:fee_pk>/", views.start, name="start"),
    path("receipt/<int:pk>/", views.receipt, name="receipt"),
]