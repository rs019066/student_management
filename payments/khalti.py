"""Small Khalti KPG-2 client using Python's standard library.

Khalti amounts are sent in paisa. The secret key is read from Django settings,
never from source code.
"""
import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class KhaltiError(Exception):
    """Raised when Khalti cannot initiate or verify a transaction."""


def _post(path, payload):
    base_url = getattr(settings, "KHALTI_API_BASE_URL", "https://dev.khalti.com/api/v2").rstrip("/")
    secret_key = getattr(settings, "KHALTI_SECRET_KEY", "").strip()
    if not secret_key:
        raise KhaltiError("Khalti is not configured. Set KHALTI_SECRET_KEY in the environment.")
    request = Request(
        f"{base_url}/{path.lstrip('/')}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Key {secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        detail = getattr(exc, "read", lambda: b"")()
        raise KhaltiError(f"Khalti request failed: {detail.decode('utf-8', 'ignore') or exc}") from exc
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise KhaltiError("Khalti returned an invalid response.") from exc
    if not isinstance(data, dict):
        raise KhaltiError("Khalti returned an unexpected response.")
    return data


def initiate_payment(*, amount, purchase_order_id, purchase_order_name, return_url, customer_info):
    amount_paisa = int((Decimal(str(amount)) * 100).quantize(Decimal("1")))
    return _post("epayment/initiate/", {
        "return_url": return_url,
        "website_url": getattr(settings, "KHALTI_WEBSITE_URL", return_url),
        "amount": amount_paisa,
        "purchase_order_id": purchase_order_id,
        "purchase_order_name": purchase_order_name,
        "customer_info": customer_info,
    })


def lookup_payment(pidx, amount):
    amount_paisa = int((Decimal(str(amount)) * 100).quantize(Decimal("1")))
    return _post("epayment/lookup/", {"pidx": pidx, "amount": amount_paisa})
