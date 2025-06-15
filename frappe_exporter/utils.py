import frappe
from .metrics_handler import get_custom_metric
import logging

logger = logging.getLogger("frappe_exporter.utils")


def update_metric(metric_name, value=1.0, labels=None, action=None):
    """
    Updates a custom Prometheus metric from anywhere in the Frappe codebase.

    This provides an ergonomic way to modify counters, gauges, etc.,
    that have been defined in the Frappe Exporter Settings.

    :param metric_name: The 'Metric Name' of the custom metric to update.
    :param value: The numeric value for the operation (e.g., amount to increment by).
    :param labels: A dictionary of label values, e.g., {'product': 'Awesome Widget'}.
                   The keys must match the 'Label Names' defined for the metric.
    :param action: Optional. The specific action to perform ('inc', 'set', 'observe').
                   If None, a sensible default is inferred from the metric type:
                   - Counter: 'inc'
                   - Gauge: 'set'
                   - Histogram/Summary: 'observe'
    """
    metric = get_custom_metric(metric_name)
    if not metric:
        # Fail silently in logs to avoid crashing critical business logic
        logger.debug(f"Custom metric '{metric_name}' not found. Cannot update.")
        return

    metric_type = type(metric).__name__

    # Infer the default action based on metric type if not provided
    if not action:
        if metric_type == "Counter":
            action = "inc"
        elif metric_type == "Gauge":
            action = "set"
        elif metric_type in ["Histogram", "Summary"]:
            action = "observe"
        else:
            logger.warning(
                f"No default action for metric type '{metric_type}' on metric '{metric_name}'. Please specify an action."
            )
            return

    try:
        # Prepare the metric instance (with or without labels)
        target_metric = metric
        if metric._labelnames:
            if not labels or sorted(metric._labelnames) != sorted(labels.keys()):
                logger.error(
                    f"Mismatched labels for metric '{metric_name}'. Required: {metric._labelnames}, Provided: {list(labels.keys() if labels else [])}"
                )
                return
            target_metric = metric.labels(**labels)

        # Get the method for the specified action (e.g., .inc, .set)
        action_func = getattr(target_metric, action, None)
        if not callable(action_func):
            logger.error(
                f"Action '{action}' is not valid for metric type '{metric_type}'."
            )
            return

        action_func(float(value))

    except Exception as e:
        logger.error(
            f"Failed to update metric '{metric_name}' with action '{action}': {e}",
            exc_info=True,
        )
