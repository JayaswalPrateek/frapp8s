import frappe
from frappe.model.document import Document
import re


class FrappeExporterSettings(Document):
    def validate(self):
        self.validate_custom_metrics()

    def validate_custom_metrics(self):
        metric_name_regex = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        label_name_regex = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

        for metric in self.custom_metrics:
            if not metric_name_regex.match(metric.metric_name):
                frappe.throw(
                    f"Metric name '{metric.metric_name}' is invalid. It must contain only letters, numbers, and underscores, and not start with a number."
                )

            if metric.label_names:
                labels = [label.strip() for label in metric.label_names.split(",")]
                for label in labels:
                    if not label_name_regex.match(label):
                        frappe.throw(
                            f"Label name '{label}' in metric '{metric.metric_name}' is invalid. It must contain only letters, numbers, and underscores, and not start with a number."
                        )

    def on_update(self):
        # Clear cache keys to signal that settings have changed.
        frappe.cache().delete_key("frappe_exporter_custom_metrics")
        frappe.cache().delete_key("frappe_exporter_whitelisted_doctypes")
        frappe.msgprint(
            "Frappe Exporter settings saved. Changes will apply after a server restart or on the next request.",
            title="Settings Updated",
            indicator="green",
        )
