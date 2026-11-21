from decimal import Decimal

from django import forms

from payments.models import Payment
from .models import FeeStructure


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class FeeStructureForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ["name", "course", "amount", "due_date", "description", "is_active"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


class ManualPaymentForm(BootstrapMixin, forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    method = forms.ChoiceField(choices=[
        (Payment.Method.CASH, "Cash"),
        (Payment.Method.BANK, "Bank voucher"),
    ])
    remarks = forms.CharField(max_length=255, required=False, label="Voucher no. or remarks")

    def __init__(self, *args, fee, **kwargs):
        super().__init__(*args, **kwargs)
        self.fee = fee
        self.fields["amount"].initial = fee.balance
        self.fields["amount"].help_text = f"Balance: Rs. {fee.balance}"

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount > self.fee.balance:
            raise forms.ValidationError(f"Amount cannot be more than the balance (Rs. {self.fee.balance}).")
        return amount