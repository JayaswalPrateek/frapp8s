import logging

import frappe

from .metrics_handler import FRAPPE_EXCEPTIONS_TOTAL

logger = logging.getLogger("frappe_exporter.exception")


def get_current_site_for_exception():
    try:
        return frappe.local.site
    except Exception:
        return "unknown_site"


def exportException(e, method_name):
    logger.error(f"Exception in {method_name}: {e}", exc_info=True)

    exception_type = type(e).__name__
    site = get_current_site_for_exception()

    # Increment the counter
    FRAPPE_EXCEPTIONS_TOTAL.labels(
        site=site, method=method_name, exception_type=exception_type
    ).inc()
