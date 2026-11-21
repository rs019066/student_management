from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from courses.models import Enrollment
from payments.services import PaymentError, record_payment
from .forms import FeeStructureForm, ManualPaymentForm
from .models import FeeStructure, StudentFee


def _is_admin(user):
    return user.is_superuser or user.role == "admin"


@role_required("admin", "student")
def fee_list(request):
    user = request.user
    is_admin = _is_admin(user)
    fees = StudentFee.objects.select_related("student__user", "fee_structure__course")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")

    if is_admin:
        if query:
            fees = fees.filter(
                Q(student__student_id__icontains=query)
                | Q(student__user__username__icontains=query)
                | Q(student__user__first_name__icontains=query)
                | Q(student__user__last_name__icontains=query)
                | Q(fee_structure__name__icontains=query)
            )
    else:
        fees = fees.filter(student__user=user)
    if status in dict(StudentFee.Status.choices):
        fees = fees.filter(status=status)

    sums = fees.exclude(status=StudentFee.Status.WAIVED).aggregate(due=Sum("amount_due"), paid=Sum("amount_paid"))
    due, paid = sums["due"] or 0, sums["paid"] or 0
    page_obj = Paginator(fees, 15).get_page(request.GET.get("page"))
    return render(request, "fees/fee_list.html", {
        "fees": page_obj, "page_obj": page_obj, "is_admin": is_admin,
        "query": query, "status": status, "statuses": StudentFee.Status.choices,
        "total_due": due, "total_paid": paid, "total_balance": max(due - paid, 0),
        "today": timezone.localdate(),
    })


@role_required("admin", "student")
def fee_detail(request, pk):
    fee = get_object_or_404(
        StudentFee.objects.select_related("student__user", "fee_structure__course"), pk=pk
    )
    is_admin = _is_admin(request.user)
    if not is_admin and fee.student.user_id != request.user.pk:
        raise PermissionDenied

    form = None
    if is_admin and fee.balance > 0:
        form = ManualPaymentForm(request.POST or None, fee=fee)
        if request.method == "POST" and form.is_valid():
            try:
                record_payment(fee, form.cleaned_data["amount"], form.cleaned_data["method"],
                               request.user, form.cleaned_data["remarks"])
            except PaymentError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Payment recorded.")
                return redirect("fees:detail", pk=fee.pk)

    return render(request, "fees/detail.html", {
        "fee": fee, "form": form, "is_admin": is_admin,
        "payments": fee.payments.all(),
    })


# ---------- Fee structures (admin only) ----------
@role_required("admin")
def fee_structure_list(request):
    structures = FeeStructure.objects.select_related("course").annotate(assigned=Count("student_fees"))
    return render(request, "fees/structure_list.html", {"structures": structures})


@role_required("admin")
def structure_create(request):
    form = FeeStructureForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fee structure created. Now assign it to the students.")
        return redirect("fees:structures")
    return render(request, "fees/form.html", {"form": form, "title": "Add fee structure"})


@role_required("admin")
def structure_update(request, pk):
    structure = get_object_or_404(FeeStructure, pk=pk)
    form = FeeStructureForm(request.POST or None, instance=structure)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fee structure updated. Fees already assigned keep their old amount.")
        return redirect("fees:structures")
    return render(request, "fees/form.html", {"form": form, "title": "Edit fee structure"})


@role_required("admin")
def structure_generate(request, pk):
    structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method != "POST":
        return redirect("fees:structures")
    if not structure.is_active:
        messages.error(request, "This fee structure is inactive.")
        return redirect("fees:structures")

    enrolled = set(
        Enrollment.objects.filter(course=structure.course, status="active")
        .order_by().values_list("student_id", flat=True)
    )
    existing = set(StudentFee.objects.filter(fee_structure=structure).values_list("student_id", flat=True))
    new_fees = [
        StudentFee(student_id=sid, fee_structure=structure, amount_due=structure.amount)
        for sid in enrolled - existing
    ]
    StudentFee.objects.bulk_create(new_fees)
    messages.success(request, f"Fee assigned to {len(new_fees)} new student(s). {len(existing)} already had it.")
    return redirect("fees:structures")