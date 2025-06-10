__version__ = "0.0.1"

import logging

logger: logging.Logger = logging.getLogger("frappe_exporter.init")
logger.info("Frappe Prometheus Exporter App is loading...")

try:
    from .overrides import apply_overrides

    apply_overrides()
    logger.info("Frappe method overrides for Prometheus Exporter applied successfully.")
except Exception as e:
    logger.error(f"Failed to apply Frappe method overrides: {e}", exc_info=True)
