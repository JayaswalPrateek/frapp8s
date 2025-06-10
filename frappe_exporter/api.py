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
        response=prometheus_data_bytes,  # This should be bytes or a string
        status=200,
        mimetype="text/plain; version=0.0.4; charset=utf-8",  # Use mimetype for Werkzeug Response
    )

    # Return this Werkzeug Response object directly.
    # Frappe's API handler will recognize this and use it as-is.
    return response
