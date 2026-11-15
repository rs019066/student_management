from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import role_required


@login_required
def dashboard(request):
    """Send each user to the dashboard for their role."""
    user = request.user
    if user.is_superuser or user.role == 'admin':
        return redirect('accounts:admin_dashboard')
    if user.role == 'teacher':
        return redirect('accounts:teacher_dashboard')
    return redirect('accounts:student_dashboard')


@role_required('admin')
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')


@role_required('teacher')
def teacher_dashboard(request):
    return render(request, 'accounts/teacher_dashboard.html')


@role_required('student')
def student_dashboard(request):
    return render(request, 'accounts/student_dashboard.html')