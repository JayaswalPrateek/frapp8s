# **frapp8s: Frappe Prometheus Exporter**

A Frappe app to export key performance and error metrics to a Prometheus-compatible endpoint. This allows for powerful monitoring and alerting capabilities for your Frappe instances.

## **Overview**

The Frappe Prometheus Exporter provides a simple way to gain insight into the performance and health of your Frappe applications. It automatically instruments core Frappe functions to provide out-of-the-box metrics and offers a flexible framework for adding your own custom, business-specific metrics.

## **Features**

- **Built-in Metrics:** Automatically exports counters and histograms for frappe.get_doc and frappe.get_list calls, tagged by status (success/error).
- **Exception Tracking:** Captures and counts unhandled exceptions, providing visibility into application errors.
- **Custom Metrics:** Define your own custom Prometheus metrics (Counters, Gauges, Histograms, Summaries) directly from the Frappe UI.
- **Filtering Control:** Whitelist specific DocTypes to control the volume of metrics and focus only on what's important to you.
- **Simple Integration:** Provides a clean utility function to update your custom metrics from anywhere in your Frappe codebase.

## **Getting Started**

### **1\. Installation**

Install the app into your bench using the standard bench commands:

From your frappe-bench directory

<pre>
bench get-app https://github.com/JayaswalPrateek/frapp8s
bench --site [your-site-name] install-app frappe_exporter
bench --site [your-site-name] migrate
</pre>

### **2\. Configuration**

All configuration is managed through a single settings page in your Frappe Desk.

1. After installing, log in to your Frappe instance as an Administrator.
2. In the Awesome Bar, search for **"Frappe Exporter Settings"**.
3. From this page, you can:
   - **Enable / Disable** the entire exporter.
   - **Allow Unauthenticated Access** to the metrics endpoint (recommended for Prometheus scraping).
   - Configure **DocType Whitelisting**.
   - Define your own **Custom Metrics**.

## **Connecting to the Exporter**

The exporter exposes all metrics on a standard HTTP endpoint.

- **Endpoint URL:** http://[your-site-name]/api/method/frappe_exporter.api.metrics

To have Prometheus scrape these metrics, add the following job to your prometheus.yml configuration file:
scrape_configs:

- job_name: 'frappe'
  metrics_path: /api/method/frappe_exporter.api.metrics
  static_configs:
  - targets: ['your-frappe-site.com'] # Replace with your Frappe instance's hostname

## **Built-in Metrics**

The following metrics are exported automatically without any configuration required.

- frappe_get_doc_total: A Counter for every call to frappe.get_doc.
  - **Labels:** site, doctype, status (success or error).
- frappe_get_doc_duration_seconds: A Histogram tracking the latency of frappe.get_doc calls.
  - **Labels:** site, doctype.
- frappe_get_list_total: A Counter for every call to frappe.get_list.
  - **Labels:** site, doctype, status (success or error).
- frappe_get_list_duration_seconds: A Histogram tracking the latency of frappe.get_list calls.
  - **Labels:** site, doctype.
- frappe_exceptions_total: A Counter for unhandled exceptions during requests.
  - **Labels:** site, exception_type, source (get_doc, get_list, or global_hook).

## **Custom Metrics**

You can define your own metrics to track business-specific events.

1. Navigate to the **Frappe Exporter Settings** page.
2. In the **Custom Metrics** table, add a new row.
3. Fill in the fields:
   - **Metric Name:** The name for your metric (e.g., my_app_sales_invoices_total). Must follow Prometheus naming conventions.
   - **Metric Type:** Choose from Counter, Gauge, Histogram, or Summary.
   - **Help Text:** A description of what the metric represents.
   - **Label Names:** An optional, comma-separated list of labels (e.g., customer_group,item_code).
4. Click **Save**. The new metric will be available after the server restarts.

## **Using Custom Metrics in Your Code**

To update a custom metric you have defined, use the provided utility function. This is the recommended way to interact with the exporter from your other Frappe apps.
Example:
Imagine you have defined a Counter named sales_invoice_total with the label customer. You can increment it in the on_submit hook of the Sales Invoice DocType.

In your custom app's sales_invoice.py file:

from frappe_exporter.utils import update_metric

def on_submit(self):
... your existing logic ...

    # Update the custom metric
    update_metric(
        metric_name='sales_invoice_total',
        value=1,
        labels={'customer': self.customer},
        action='inc' # 'inc' is default for Counters, but can be explicit
    )

The update_metric function handles finding the metric and performing the correct action (inc, set, observe, etc.).

## **Filtering Metrics**

To reduce noise and focus only on important DocTypes, you can enable whitelisting.

1. Navigate to the **Frappe Exporter Settings** page.
2. Check the **Enable Doctype Whitelisting** box.
3. A set of buttons will appear. Click **Select All** to populate the table with all custom DocTypes in your system.
4. Manually remove any DocTypes you do _not_ want to monitor.
5. Click **Save**.

Once enabled, the built-in get_doc, get_list, and exception metrics will only be exported for the DocTypes present in this whitelist.

## **License**

This project is licensed under the GPL-3.0 License.
