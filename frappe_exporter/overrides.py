from .exception import exportException
import logging
import time
import frappe
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


def get_whitelisted_doctypes():
    cached_val = frappe.cache().get_value("frappe_exporter_whitelisted_doctypes")
    if cached_val:
        return cached_val

    try:
        # Using frappe.db.get_singles_dict to avoid triggering get_doc hooks
        settings = frappe.db.get_singles_dict("Frappe Exporter Settings")
        if settings.get("enabled") and settings.get("whitelisting_enabled"):
            # This part is safe as it doesn't trigger hooks
            whitelisted_docs = frappe.get_all(
                "Whitelisted Doctype",
                fields=["doctype_name"],
                parent="Frappe Exporter Settings",
            )
            whitelisted_set = {d.doctype_name for d in whitelisted_docs}
            result = (True, whitelisted_set)
        else:
            # Whitelisting is disabled, so all doctypes are allowed.
            result = (False, set())

        frappe.cache().set_value("frappe_exporter_whitelisted_doctypes", result)
        return result
    except Exception:
        # If settings don't exist or there's an error, behave as if disabled.
        return (False, set())


def is_doctype_whitelisted(doctype):
    if not doctype:
        return False

    enabled, whitelist = get_whitelisted_doctypes()

    if not enabled:
        return True

    return doctype in whitelist


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
    return doctype if doctype else "unknown_doctype"


def get_doc_wrapper(*args, **kwargs):
    global _original_get_doc

    # FIX: During specific system operations, do not process metrics to avoid recursive calls.
    if frappe.flags.in_migrate or frappe.flags.in_install or frappe.flags.in_patch:
        return _original_get_doc(*args, **kwargs)

    site = get_current_site()
    start_time = time.monotonic()
    status = "success"
    result_doc = None
    exception_obj = None

    try:
        result_doc = _original_get_doc(*args, **kwargs)
        return result_doc
    except Exception as e:
        status = "error"
        exception_obj = e
        raise
    finally:
        # This block runs even if an exception is raised
        doctype = extract_doctype_from_args("get_doc", args, kwargs, result_doc)

        if is_doctype_whitelisted(doctype):
            GET_DOC_TOTAL.labels(site=site, doctype=doctype, status=status).inc()
            if status == "success":
                duration_seconds = time.monotonic() - start_time
                GET_DOC_DURATION_SECONDS.labels(site=site, doctype=doctype).observe(
                    duration_seconds
                )

            if exception_obj:
                exportException(exception_obj, "get_doc")


def get_list_wrapper(*args, **kwargs):
    global _original_get_list

    # FIX: During specific system operations, do not process metrics to avoid recursive calls.
    if frappe.flags.in_migrate or frappe.flags.in_install or frappe.flags.in_patch:
        return _original_get_list(*args, **kwargs)

    site = get_current_site()
    doctype = extract_doctype_from_args("get_list", args, kwargs)
    start_time = time.monotonic()
    status = "success"
    exception_obj = None

    try:
        return _original_get_list(*args, **kwargs)
    except Exception as e:
        status = "error"
        exception_obj = e
        raise
    finally:
        # This block runs even if an exception is raised
        if is_doctype_whitelisted(doctype):
            GET_LIST_TOTAL.labels(site=site, doctype=doctype, status=status).inc()
            if status == "success":
                duration_seconds = time.monotonic() - start_time
                GET_LIST_DURATION_SECONDS.labels(site=site, doctype=doctype).observe(
                    duration_seconds
                )

            if exception_obj:
                exportException(exception_obj, "get_list")


_overrides_applied_flag = False


def apply_overrides():
    global _original_get_doc, _original_get_list, _overrides_applied_flag
    if _overrides_applied_flag:
        return

    logger.info("Applying Frappe method overrides for Prometheus Exporter...")

    # Store original methods
    if hasattr(frappe, "get_doc") and not hasattr(
        frappe.get_doc, "_instrumented_by_exporter"
    ):
        _original_get_doc = frappe.get_doc
        frappe.get_doc = get_doc_wrapper
        # Preventing double-wrapping
        setattr(frappe.get_doc, "_instrumented_by_exporter", True)
        logger.info("Instrumented frappe.get_doc")

    if hasattr(frappe, "get_list") and not hasattr(
        frappe.get_list, "_instrumented_by_exporter"
    ):
        _original_get_list = frappe.get_list
        frappe.get_list = get_list_wrapper
        # Preventing double-wrapping
        setattr(frappe.get_list, "_instrumented_by_exporter", True)
        logger.info("Instrumented frappe.get_list")

    _overrides_applied_flag = True
