from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge, Summary
import logging
import frappe
import threading

logger = logging.getLogger("frappe_exporter.metrics_handler")

APP_REGISTRY = CollectorRegistry(auto_describe=True)

# --- Pre-defined Metrics ---

FRAPPE_EXCEPTIONS_TOTAL = Counter(
    "frappe_exceptions_total",
    "Total number of exceptions caught in Frappe method overrides",
    ["site", "method", "exception_type"],
    registry=APP_REGISTRY,
)

GET_DOC_TOTAL = Counter(
    "frappe_get_doc_total",
    "Total number of get_doc calls processed by Frappe",
    ["site", "doctype", "status"],
    registry=APP_REGISTRY,
)

GET_DOC_DURATION_SECONDS = Histogram(
    "frappe_get_doc_duration_seconds",
    "Histogram of get_doc call durations in seconds",
    ["site", "doctype"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=APP_REGISTRY,
)

GET_LIST_TOTAL = Counter(
    "frappe_get_list_total",
    "Total number of get_list calls processed by Frappe",
    ["site", "doctype", "status"],
    registry=APP_REGISTRY,
)

GET_LIST_DURATION_SECONDS = Histogram(
    "frappe_get_list_duration_seconds",
    "Histogram of get_list call durations in seconds",
    ["site", "doctype"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=APP_REGISTRY,
)

# --- Custom Metrics Handling ---

CUSTOM_METRICS = {}
_init_lock = threading.Lock()
_custom_metrics_initialized = False  # Flag to control lazy initialization

METRIC_TYPE_MAP = {
    "Counter": Counter,
    "Gauge": Gauge,
    "Histogram": Histogram,
    "Summary": Summary,
}


# Internal function to run initialization once
def _initialize_custom_metrics_if_needed():
    global _custom_metrics_initialized
    if not _custom_metrics_initialized:
        with _init_lock:
            if not _custom_metrics_initialized:
                initialize_custom_metrics()
                _custom_metrics_initialized = True


# Reads custom metric definitions from the DocType and registers them.
# called lazily and should only execute when a site context is available.
def initialize_custom_metrics():
    global CUSTOM_METRICS

    # Safeguard against running in a context without a site (e.g. build process)
    if not getattr(frappe.local, "site", None):
        logger.warning("No site context found. Skipping custom metric initialization.")
        return

    logger.info("Initializing custom metrics...")
    try:
        if not frappe.db.exists("DocType", "Frappe Exporter Settings"):
            logger.warning(
                "DocType 'Frappe Exporter Settings' not found. Skipping custom metric initialization."
            )
            return
        settings = frappe.get_single("Frappe Exporter Settings")
    except Exception as e:
        logger.warning(
            f"Could not get Frappe Exporter Settings. Skipping custom metric initialization. Error: {e}"
        )
        return

    if not settings.enabled:
        logger.info(
            "Frappe Exporter is disabled in settings. No custom metrics will be initialized."
        )
        return

    for metric_def in settings.custom_metrics:
        metric_name = metric_def.get("metric_name")
        metric_type = metric_def.get("metric_type")
        help_text = metric_def.get("help_text", "No help text provided.")
        label_names_str = metric_def.get("label_names", "")
        label_names = [
            label.strip() for label in label_names_str.split(",") if label.strip()
        ]

        if not all([metric_name, metric_type]):
            logger.error(
                f"Skipping custom metric due to missing name or type: {metric_def.as_dict()}"
            )
            continue

        if (
            metric_name in CUSTOM_METRICS
            or metric_name in APP_REGISTRY._names_to_collectors
        ):
            logger.warning(
                f"Metric '{metric_name}' is already defined or registered. Skipping."
            )
            continue

        metric_class = METRIC_TYPE_MAP.get(metric_type)
        if not metric_class:
            logger.error(
                f"Invalid metric type '{metric_type}' for metric '{metric_name}'. Skipping."
            )
            continue

        try:
            metric_obj = metric_class(
                metric_name, help_text, labelnames=label_names, registry=APP_REGISTRY
            )
            CUSTOM_METRICS[metric_name] = metric_obj
            logger.info(
                f"Successfully created and registered custom metric: '{metric_name}'"
            )
        except Exception as e:
            logger.error(
                f"Failed to create custom metric '{metric_name}': {e}", exc_info=True
            )
    logger.info("Custom metrics initialization complete.")


def get_custom_metric(metric_name):
    _initialize_custom_metrics_if_needed()
    return CUSTOM_METRICS.get(metric_name)


def get_registry():
    _initialize_custom_metrics_if_needed()
    return APP_REGISTRY
