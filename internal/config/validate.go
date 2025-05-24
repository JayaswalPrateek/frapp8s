package config

import (
	"errors"
	"fmt"
	"net"
	"os"
	"strings"
)

func (c *Config) Validate() error {
	var errs []string

	if c.Prometheus.ListenAddress == "" {
		errs = append(errs, "prometheus.listen_address is required")
	} else {
		// Check if it's a valid [host]:port or :port format
		// For just ":port", net.SplitHostPort will error but it's a valid listen address.
		if strings.Count(c.Prometheus.ListenAddress, ":") == 0 { // e.g., "9876"
			errs = append(errs, fmt.Sprintf("prometheus.listen_address ('%s') must be in [host]:port or :port format", c.Prometheus.ListenAddress))
		} else if strings.Count(c.Prometheus.ListenAddress, ":") > 1 && !strings.Contains(c.Prometheus.ListenAddress, "[") { // e.g. "1:2:3" but not "[::1]:80"
			_, _, err := net.SplitHostPort(c.Prometheus.ListenAddress) // This will likely fail correctly here
			if err != nil {
				errs = append(errs, fmt.Sprintf("prometheus.listen_address ('%s') is not a valid [host]:port format: %v", c.Prometheus.ListenAddress, err))
			}
		}
	}

	if c.Prometheus.MetricsPath == "" {
		errs = append(errs, "prometheus.metrics_path is required")
	} else if !strings.HasPrefix(c.Prometheus.MetricsPath, "/") {
		errs = append(errs, "prometheus.metrics_path must start with '/'")
	}

	if len(c.Frappe.Benches) == 0 {
		errs = append(errs, "frappe.benches must contain at least one path")
	}
	for i, benchPath := range c.Frappe.Benches {
		if strings.TrimSpace(benchPath) == "" {
			errs = append(errs, fmt.Sprintf("frappe.benches[%d]: path cannot be empty", i))
			continue
		}
		if info, err := os.Stat(benchPath); os.IsNotExist(err) {
			errs = append(errs, fmt.Sprintf("frappe.benches: path '%s' does not exist", benchPath))
		} else if err != nil {
			errs = append(errs, fmt.Sprintf("frappe.benches: error accessing path '%s': %v", benchPath, err))
		} else if !info.IsDir() {
			errs = append(errs, fmt.Sprintf("frappe.benches: path '%s' is not a directory", benchPath))
		}
	}

	if len(c.Frappe.LogFiles) == 0 {
		errs = append(errs, "frappe.log_files must contain at least one file name")
	}
	for i, logFile := range c.Frappe.LogFiles {
		if strings.TrimSpace(logFile) == "" {
			errs = append(errs, fmt.Sprintf("frappe.log_files[%d]: file name cannot be empty", i))
		} else if strings.ContainsAny(logFile, "/\\") {
			errs = append(errs, fmt.Sprintf("frappe.log_files[%d]: '%s' should be a file name, not a path", i, logFile))
		}
	}

	logFormat := strings.ToLower(c.Frappe.LogFormat)
	if logFormat != "json" && logFormat != "text" {
		errs = append(errs, "frappe.log_format must be 'json' or 'text'")
	}

	if c.Pipeline.ChannelBufferSize <= 0 {
		errs = append(errs, "pipeline.channel_buffer_size must be a positive integer")
	}
	if c.Pipeline.ConsumerWorkers <= 0 {
		errs = append(errs, "pipeline.consumer_workers must be a positive integer")
	}

	if c.Parser.MinSQLDurationMs < 0 {
		errs = append(errs, "parser.min_sql_duration_ms cannot be negative")
	}

	for i, site := range c.Parser.ExcludeSites {
		if strings.TrimSpace(site) == "" {
			errs = append(errs, fmt.Sprintf("parser.exclude_sites[%d] contains an empty value", i))
		}
	}
	for i, method := range c.Parser.ExcludeMethods {
		if strings.TrimSpace(method) == "" {
			errs = append(errs, fmt.Sprintf("parser.exclude_methods[%d] contains an empty value", i))
		}
	}
	for i, doctype := range c.Parser.ExcludeDoctypes {
		if strings.TrimSpace(doctype) == "" {
			errs = append(errs, fmt.Sprintf("parser.exclude_doctypes[%d] contains an empty value", i))
		}
	}

	logLevel := strings.ToLower(c.ExporterLogging.Level)
	allowedLevels := map[string]bool{"debug": true, "info": true, "warn": true, "error": true}
	if !allowedLevels[logLevel] {
		errs = append(errs, "exporter_logging.level must be one of 'debug', 'info', 'warn', or 'error'")
	}

	expLogFormat := strings.ToLower(c.ExporterLogging.Format)
	if expLogFormat != "json" && expLogFormat != "text" {
		errs = append(errs, "exporter_logging.format must be 'json' or 'text'")
	}

	if len(errs) > 0 {
		return errors.New("configuration validation failed:\n - " + strings.Join(errs, "\n - "))
	}

	return nil
}
