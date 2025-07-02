import frappe
from prometheus_client import generate_latest
from werkzeug.wrappers import Response
from .metrics_handler import get_registry


@frappe.whitelist(allow_guest=True)
def metrics():
    # Generate the Prometheus formatted text (bytes)
    prometheus_data_bytes = generate_latest(get_registry())

    # Create a Werkzeug Response object
    response = Response(
        response=prometheus_data_bytes,
        status=200,
        mimetype="text/plain; version=0.0.4; charset=utf-8",
    )

    # Return this Werkzeug Response object directly.
    # Frappe's API handler will recognize this and use it as-is.
    return response


@frappe.whitelist()
def get_custom_doctypes():
    # Frappe and ERPNext are considered core apps. You can add more to this list if needed.
    core_modules = frappe.get_all(
        "Module Def", filters={"app_name": ("in", ["frappe", "erpnext"])}, pluck="name"
    )

    custom_doctypes = frappe.get_all(
        "DocType",
        filters={"custom": 0, "issingle": 0, "module": ("not in", core_modules)},
        fields=["name"],
        order_by="name",
    )
    return [d.name for d in custom_doctypes]
