from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from fees.models import StudentFee
from .models import Payment


class PaymentError(Exception):
    """Raised when a payment cannot be created or recorded."""


def _apply_to_fee(fee, amount):
    fee.amount_paid += amount
    if fee.amount_paid >= fee.amount_due:
        fee.status = StudentFee.Status.PAID
        fee.paid_on = timezone.localdate()
    else:
        fee.status = StudentFee.Status.PARTIAL
    fee.save(update_fields=["amount_paid", "status", "paid_on"])


@transaction.atomic
def record_payment(student_fee, amount, method, user, remarks=""):
    """Manual payment (cash or bank voucher) entered by an admin. Saved as successful straight away."""
    fee = StudentFee.objects.select_for_update().get(pk=student_fee.pk)
    amount = Decimal(str(amount))
    if fee.status == StudentFee.Status.WAIVED:
        raise PaymentError("This fee has been waived.")
    if amount <= 0:
        raise PaymentError("Amount must be greater than zero.")
    if amount > fee.balance:
        raise PaymentError(f"Amount cannot be more than the balance ({fee.balance}).")
    payment = Payment.objects.create(
        student_fee=fee, amount=amount, method=method, status=Payment.Status.SUCCESS,
        remarks=remarks, recorded_by=user, paid_at=timezone.now(),
    )
    _apply_to_fee(fee, amount)
    return payment


@transaction.atomic
def create_pending_payment(student_fee, method, amount=None):
    """Person 2 calls this when the student clicks Pay Now. Defaults to the full balance."""
    fee = StudentFee.objects.select_for_update().get(pk=student_fee.pk)
    amount = fee.balance if amount is None else Decimal(str(amount))
    if amount <= 0 or amount > fee.balance:
        raise PaymentError("Nothing to pay, or the amount is more than the balance.")
    return Payment.objects.create(student_fee=fee, amount=amount, method=method)


@transaction.atomic
def mark_payment_success(payment, gateway_reference="", response=None):
    """Person 2 calls this ONLY after the gateway has confirmed the payment on the server.
    Returns False if the payment was already handled, so a refreshed page cannot count twice."""
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status != Payment.Status.PENDING:
        return False
    fee = StudentFee.objects.select_for_update().get(pk=payment.student_fee_id)
    payment.status = Payment.Status.SUCCESS
    payment.gateway_reference = gateway_reference
    payment.gateway_response = response or {}
    payment.paid_at = timezone.now()
    payment.save()
    _apply_to_fee(fee, payment.amount)
    return True


@transaction.atomic
def mark_payment_failed(payment, response=None):
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status != Payment.Status.PENDING:
        return False
    payment.status = Payment.Status.FAILED
    payment.gateway_response = response or {}
    payment.save()
    return True