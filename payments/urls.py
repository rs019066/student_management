from django.urls import path
from . import views

app_name = "payments"
urlpatterns = [
    path("", views.payment_list, name="list"),
    path("start/<int:fee_pk>/", views.start, name="start"),
    path("khalti/callback/", views.khalti_callback, name="khalti_callback"),
    path("success/<int:pk>/", views.payment_success, name="success"),
    path("failure/<int:pk>/", views.payment_failure, name="failure"),
    path("receipt/<int:pk>/", views.receipt, name="receipt"),
]
