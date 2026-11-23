from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.conf import settings
from accounts.decorators import role_required
from fees.models import StudentFee
from .khalti import KhaltiError, initiate_payment, lookup_payment
from .models import Payment
from .services import PaymentError, create_pending_payment, mark_payment_failed, mark_payment_success


def _is_admin(user):
    return user.is_superuser or user.role == "admin"


@role_required("admin")
def payment_list(request):
    payments = Payment.objects.select_related("student_fee__student__user", "student_fee__fee_structure")
    status = request.GET.get("status", "")
    if status in dict(Payment.Status.choices):
        payments = payments.filter(status=status)
    page_obj = Paginator(payments, 20).get_page(request.GET.get("page"))
    return render(request, "payments/payments_list.html", {
        "payments": page_obj, "page_obj": page_obj, "status": status, "statuses": Payment.Status.choices,
    })


@role_required("student")
def start(request, fee_pk):
    """Create a pending payment and redirect the student to Khalti checkout."""
    fee = get_object_or_404(
        StudentFee.objects.select_related("student__user", "fee_structure"),
        pk=fee_pk, student__user=request.user,
    )
    if fee.balance <= 0:
        messages.info(request, "Nothing is left to pay on this fee.")
        return redirect("fees:detail", pk=fee.pk)
    if request.method != "POST":
        return render(request, "payments/start.html", {"fee": fee})
    try:
        payment = create_pending_payment(fee, Payment.Method.KHALTI)
        return_url = request.build_absolute_uri(reverse("payments:khalti_callback"))
        response = initiate_payment(
            amount=payment.amount,
            purchase_order_id=payment.transaction_id,
            purchase_order_name=fee.fee_structure.name,
            return_url=return_url,
            customer_info={
                "name": request.user.get_full_name() or request.user.username,
                "email": request.user.email or "student@example.com",
                "phone": getattr(getattr(request.user, "student_profile", None), "phone", "") or "9800000000",
            },
        )
        pidx = response.get("pidx")
        payment_url = response.get("payment_url")
        if not pidx or not payment_url:
            mark_payment_failed(payment, response)
            raise KhaltiError("Khalti did not return a payment URL.")
        payment.gateway_reference = pidx
        payment.gateway_response = response
        payment.save(update_fields=["gateway_reference", "gateway_response"])
        return redirect(payment_url)
    except (KhaltiError, PaymentError) as exc:
        if "payment" in locals() and payment.status == Payment.Status.PENDING:
            mark_payment_failed(payment, {"error": str(exc)})
        messages.error(request, str(exc))
        return redirect("fees:detail", pk=fee.pk)


@role_required("student")
def khalti_callback(request):
    """Validate the callback with Khalti lookup before applying money to a fee."""
    purchase_order_id = request.GET.get("purchase_order_id", "")
    pidx = request.GET.get("pidx", "")
    status = request.GET.get("status", "")
    payment = get_object_or_404(
        Payment.objects.select_related("student_fee__student__user"),
        transaction_id=purchase_order_id,
        method=Payment.Method.KHALTI,
        student_fee__student__user=request.user,
    )
    if payment.status == Payment.Status.SUCCESS:
        return redirect("payments:receipt", pk=payment.pk)
    if not pidx or status != "Completed":
        mark_payment_failed(payment, dict(request.GET.items()))
        messages.error(request, "Khalti payment was not completed.")
        return redirect("payments:failure", pk=payment.pk)
    try:
        verification = lookup_payment(pidx, payment.amount)
    except KhaltiError as exc:
        messages.error(request, f"Payment verification failed: {exc}")
        return redirect("payments:failure", pk=payment.pk)
    valid = (
        verification.get("status") == "Completed"
        and verification.get("pidx") == pidx
        and int(verification.get("total_amount", 0)) == int(payment.amount * 100)
    )
    if not valid:
        mark_payment_failed(payment, verification)
        messages.error(request, "Khalti could not verify this payment.")
        return redirect("payments:failure", pk=payment.pk)
    mark_payment_success(payment, verification.get("transaction_id", ""), verification)
    messages.success(request, "Payment completed successfully.")
    return redirect("payments:success", pk=payment.pk)


@role_required("student")
def payment_success(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related("student_fee__fee_structure"),
        pk=pk, status=Payment.Status.SUCCESS,
        student_fee__student__user=request.user,
    )
    return render(request, "payments/success.html", {"payment": payment})


@role_required("student")
def payment_failure(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related("student_fee__fee_structure"),
        pk=pk, student_fee__student__user=request.user,
    )
    return render(request, "payments/failure.html", {"payment": payment})


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
