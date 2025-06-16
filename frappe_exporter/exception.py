import logging
import frappe
from .metrics_handler import FRAPPE_EXCEPTIONS_TOTAL

logger = logging.getLogger("frappe_exporter.exception")

# A list of common high-level Frappe exceptions to monitor, refined based
# on the full list in `frappe.exceptions`. This helps filter out very
# low-level or purely internal exceptions.
HIGH_LEVEL_EXCEPTIONS = (
    # --- Validation & Data Integrity Errors ---
    frappe.exceptions.ValidationError,  # Base for most data-related errors
    frappe.exceptions.DuplicateEntryError,  # Unique constraint violations
    frappe.exceptions.LinkValidationError,  # Invalid links between documents
    frappe.exceptions.DocstatusTransitionError,  # Invalid state changes (e.g., submit cancelled doc)
    frappe.exceptions.UpdateAfterSubmitError,  # Modifying submitted documents
    frappe.exceptions.DocumentLockedError,  # Concurrency issues
    # --- Permissions & Authentication Errors ---
    frappe.exceptions.PermissionError,  # User does not have rights
    frappe.exceptions.AuthenticationError,  # Login failures
    frappe.exceptions.SessionExpired,  # Session has timed out
    frappe.exceptions.CSRFTokenError,  # CSRF security violations
    # --- Database & Performance Errors ---
    frappe.exceptions.QueryTimeoutError,  # Database query took too long
    frappe.exceptions.QueryDeadlockError,  # Database deadlock detected
    frappe.exceptions.TooManyRequestsError,  # Rate limiting exceeded
    frappe.exceptions.TooManyWritesError,  # Write-heavy operations causing issues
    frappe.exceptions.QueueOverloaded,  # Background queue is full
    # --- System & Configuration Errors ---
    frappe.exceptions.OutgoingEmailError,  # Failure in sending emails
    frappe.exceptions.SessionStopped,  # Indication of service interruption
    frappe.exceptions.InReadOnlyMode,  # Site is in maintenance/read-only mode
    frappe.exceptions.SessionBootFailed,  # Critical failure on session start
    frappe.exceptions.ImproperDBConfigurationError,  # DB config issue detected
)


def get_current_site_for_exception():
    try:
        return frappe.local.site
    except Exception:
        return "unknown_site"


# Exports exceptions specifically from the get_doc/get_list wrappers.
# This remains unchanged to avoid interfering with existing metrics.
def exportException(e, method_name):
    logger.debug(f"Exception in wrapped method '{method_name}': {e}")
    exception_type = type(e).__name__
    site = get_current_site_for_exception()

    # Increment the counter with 'method_wrapper' as the source
    FRAPPE_EXCEPTIONS_TOTAL.labels(
        site=site, exception_type=exception_type, source=method_name
    ).inc()


# Handles exceptions caught by the global `on_error` hook.
# It filters for high-level exceptions before exporting them as metrics.
def handle_global_exception(e):
    # Check if the exception is one of the high-level types we want to track.
    if not isinstance(e, HIGH_LEVEL_EXCEPTIONS):
        logger.debug(
            f"Ignoring low-level or internal exception of type {type(e).__name__}"
        )
        return

    logger.info(f"Global handler caught a high-level exception: {type(e).__name__}")

    exception_type = type(e).__name__
    site = get_current_site_for_exception()

    # Increment the counter with 'global_hook' as the source
    FRAPPE_EXCEPTIONS_TOTAL.labels(
        site=site, exception_type=exception_type, source="global_hook"
    ).inc()
