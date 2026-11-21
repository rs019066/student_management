from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from fees.models import StudentFee
from .models import Payment


def _is_admin(user):
    return user.is_superuser or user.role == "admin"


@role_required("admin")
def payment_list(request):
    payments = Payment.objects.select_related("student_fee__student__user", "student_fee__fee_structure")
    status = request.GET.get("status", "")
    if status in dict(Payment.Status.choices):
        payments = payments.filter(status=status)
    page_obj = Paginator(payments, 20).get_page(request.GET.get("page"))
    return render(request, "payments/payment_list.html", {
        "payments": page_obj, "page_obj": page_obj, "status": status, "statuses": Payment.Status.choices,
    })


@role_required("student")
def start(request, fee_pk):
    """PLACEHOLDER for the Pay Now button. Person 2 replaces this view and start.html with the gateway."""
    fee = get_object_or_404(
        StudentFee.objects.select_related("student__user", "fee_structure"),
        pk=fee_pk, student__user=request.user,
    )
    if fee.balance <= 0:
        messages.info(request, "Nothing is left to pay on this fee.")
        return redirect("fees:detail", pk=fee.pk)
    return render(request, "payments/start.html", {"fee": fee})


@role_required("admin", "student")
def receipt(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related(
            "student_fee__student__user", "student_fee__fee_structure__course", "recorded_by"),
        pk=pk, status=Payment.Status.SUCCESS,
    )
    if not _is_admin(request.user) and payment.student_fee.student.user_id != request.user.pk:
        raise PermissionDenied
    return render(request, "payments/receipt.html", {"payment": payment, "fee": payment.student_fee})