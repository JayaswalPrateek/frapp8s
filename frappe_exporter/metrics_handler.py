from prometheus_client import CollectorRegistry, Counter, Histogram
import logging

logger = logging.getLogger("frappe_exporter.metrics_handler")

# Global registry for all app metrics
# auto_describe=True helps generate HELP strings automatically if not provided
APP_REGISTRY = CollectorRegistry(auto_describe=True)

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
    # Example buckets: 1ms, 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s
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
    # Example buckets, can be different from get_doc if get_list is typically slower
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=APP_REGISTRY,
)


def get_registry():
    return APP_REGISTRY
