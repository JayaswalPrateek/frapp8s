package exporter

import (
	"log/slog"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	// Exporter's own 'up' metric
	up = promauto.NewGauge(prometheus.GaugeOpts{
		Name: "frapp8s_up",
		Help: "Indicates if the frapp8s exporter is running (1 for up, 0 for down)",
	})

	// --- Frappe SQL Metrics ---

	// SQLQueriesTotal counts the number of SQL queries processed.
	SQLQueriesTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "frappe_sql_queries_total",
			Help: "Total number of SQL queries executed, categorized by bench, site, doctype, method, and SQL type.",
		},
		[]string{"bench", "site", "doctype", "method", "sql_type", "status"}, // status: "success" or "error"
	)

	// SQLQueryDurationSeconds records the distribution of SQL query durations.
	SQLQueryDurationSeconds = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name: "frappe_sql_query_duration_seconds",
			Help: "Histogram of SQL query execution durations in seconds.",
			// Buckets are examples, tune them based on observed query times
			Buckets: prometheus.ExponentialBuckets(0.001, 2, 15), // 1ms to ~16s
		},
		[]string{"bench", "site", "doctype", "method", "sql_type"},
	)

	// --- Exporter Internal Metrics ---
	// Example: Count of recorder dump files processed
	RecorderDumpsProcessedTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "frapp8s_recorder_dumps_processed_total",
			Help: "Total number of Frappe Recorder dump files processed.",
		},
		[]string{"bench", "status"}, // status: "success", "error_read", "error_parse"
	)

	// Add more metrics as needed (e.g., events_parsed, errors_parsing)
)

func StartMetricsServer(listenAddress, metricsPath string, logger *slog.Logger) {
	up.Set(1)

	mux := http.NewServeMux()
	mux.Handle(metricsPath, promhttp.Handler())
	server := &http.Server{
		Addr:         listenAddress,
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	logger.Info("Prometheus metrics server starting", "address", listenAddress, "path", metricsPath)

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		logger.Error("Prometheus metrics server failed to start", "error", err)
		up.Set(0)
	}

	logger.Info("Prometheus metrics server shut down.")
}

// --- Functions to update metrics ---

// RecordQuery records metrics for a single parsed SQL query.
func RecordQuery(bench, site, doctype, method, sqlType, status string, durationSeconds float64) {
	SQLQueriesTotal.WithLabelValues(bench, site, doctype, method, sqlType, status).Inc()
	if status == "success" && durationSeconds >= 0 {
		SQLQueryDurationSeconds.WithLabelValues(bench, site, doctype, method, sqlType).Observe(durationSeconds)
	}
}

// IncRecorderDumpsProcessed records that a recorder dump file has been processed.
func IncRecorderDumpsProcessed(bench, status string) {
	RecorderDumpsProcessedTotal.WithLabelValues(bench, status).Inc()
}
