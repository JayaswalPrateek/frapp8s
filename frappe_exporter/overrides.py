import logging
import time

import frappe

# Import metrics from metrics_handler
from .metrics_handler import (
    GET_DOC_DURATION_SECONDS,
    GET_DOC_TOTAL,
    GET_LIST_DURATION_SECONDS,
    GET_LIST_TOTAL,
)

logger = logging.getLogger("frappe_exporter.overrides")

# Store references to the original Frappe methods
_original_get_doc = None
_original_get_list = None


def get_current_site():
    try:
        return frappe.local.site
    except Exception:
        # This can happen if called outside a request context (e.g., some background jobs)
        return "unknown_site"


def extract_doctype_from_args(method_name, args, kwargs, result=None):
    doctype = ""
    # Try to get doctype from the first argument if it's a string
    if args and isinstance(args[0], str):
        doctype = args[0]
    # If the first argument is a dict (common for get_doc)
    elif args and isinstance(args[0], dict):
        doctype = args[0].get("doctype", "")
    # Check kwargs
    if not doctype and kwargs.get("doctype"):
        doctype = kwargs.get("doctype")
    # For get_doc, the result (document object) has a .doctype attribute
    if (
        method_name == "get_doc"
        and result
        and hasattr(result, "doctype")
        and not doctype
    ):
        doctype = result.doctype

    return doctype if doctype else f"unknown_doctype_{method_name}"


def get_doc_wrapper(*args, **kwargs):
    global _original_get_doc
    if not _original_get_doc:  # Safety net if not patched
        logger.error("Original frappe.get_doc not found for wrapper!")
        # Attempt to find it dynamically if not set (less ideal)
        _original_get_doc = (
            getattr(frappe, "get_doc_original_for_exporter", None) or frappe.get_doc
        )
        if not hasattr(
            frappe.get_doc, "_instrumented_by_exporter"
        ):  # if it's still not the original
            _original_get_doc = (
                frappe.get_doc
            )  # last resort, might cause recursion if patching failed

    site = get_current_site()

    start_time = time.monotonic()
    status = "success"
    result_doc = None
    try:
        result_doc = _original_get_doc(*args, **kwargs)
        return result_doc
    except Exception:
        status = "error"
        raise
    finally:
        duration_seconds = time.monotonic() - start_time
        doctype = extract_doctype_from_args("get_doc", args, kwargs, result_doc)

        GET_DOC_TOTAL.labels(site=site, doctype=doctype, status=status).inc()
        if status == "success":
            GET_DOC_DURATION_SECONDS.labels(site=site, doctype=doctype).observe(
                duration_seconds
            )


def get_list_wrapper(*args, **kwargs):
    global _original_get_list
    if not _original_get_list:
        logger.error("Original frappe.get_list not found for wrapper!")
        _original_get_list = (
            getattr(frappe, "get_list_original_for_exporter", None) or frappe.get_list
        )
        if not hasattr(frappe.get_list, "_instrumented_by_exporter"):
            _original_get_list = frappe.get_list

    site = get_current_site()
    doctype = extract_doctype_from_args("get_list", args, kwargs)

    start_time = time.monotonic()
    status = "success"
    try:
        return _original_get_list(*args, **kwargs)
    except Exception:
        status = "error"
        raise
    finally:
        duration_seconds = time.monotonic() - start_time
        GET_LIST_TOTAL.labels(site=site, doctype=doctype, status=status).inc()
        if status == "success":
            GET_LIST_DURATION_SECONDS.labels(site=site, doctype=doctype).observe(
                duration_seconds
            )


# Prevents this function from running its logic more than once per Python process
_overrides_applied_flag = False


def apply_overrides():
    global _original_get_doc, _original_get_list, _overrides_applied_flag
    if _overrides_applied_flag:
        return

    logger.info("Applying Frappe method overrides for Prometheus Exporter...")

    if hasattr(frappe, "get_doc") and not hasattr(
        frappe.get_doc, "_instrumented_by_exporter"
    ):
        _original_get_doc = frappe.get_doc
        # setattr(frappe, 'get_doc_original_for_exporter', _original_get_doc)
        frappe.get_doc = get_doc_wrapper
        # Preventing double-wrapping
        setattr(frappe.get_doc, "_instrumented_by_exporter", True)
        logger.info("Instrumented frappe.get_doc")
    else:
        logger.warning("frappe.get_doc already instrumented or not found.")

    if hasattr(frappe, "get_list") and not hasattr(
        frappe.get_list, "_instrumented_by_exporter"
    ):
        _original_get_list = frappe.get_list
        # setattr(frappe, 'get_list_original_for_exporter', _original_get_list)
        frappe.get_list = get_list_wrapper
        # Preventing double-wrapping
        setattr(frappe.get_list, "_instrumented_by_exporter", True)
        logger.info("Instrumented frappe.get_list")
    else:
        logger.warning("frappe.get_list already instrumented or not found.")

    _overrides_applied_flag = True
