__version__ = "0.0.1"

import logging

# --- Public API ---
from .utils import update_metric

logger: logging.Logger = logging.getLogger("frappe_exporter.init")
logger.info("Frappe Prometheus Exporter App is loading...")

try:
    # Applying method overrides is safe on import as it doesn't
    # depend on site context or database connections.
    from .overrides import apply_overrides

    apply_overrides()
    logger.info("Frappe method overrides for Prometheus Exporter applied successfully.")
except Exception as e:
    # Broad exception to avoid crashing the bench during startup
    logger.error(f"Failed to apply Frappe method overrides: {e}", exc_info=True)
