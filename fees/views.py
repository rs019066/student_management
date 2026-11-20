from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import FeeStructure, StudentFee


@login_required
def fee_list(request):
    return render(request, "fees/fee_list.html", {"fees": StudentFee.objects.select_related("student__user", "fee_structure")})


@login_required
def fee_structure_list(request):
    return render(request, "fees/structure_list.html", {"structures": FeeStructure.objects.select_related("course")})
