from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('courses/', include('courses.urls')),
    path('attendance/', include('attendance.urls')),
    path('results/', include('results.urls')),
    path('reports/', include('reports.urls')),
    path('fees/', include('fees.urls')),
    path('payments/', include('payments.urls')),
    path('', lambda request: redirect('accounts:dashboard')),
]