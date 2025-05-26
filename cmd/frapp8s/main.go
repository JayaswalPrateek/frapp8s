package main

import (
	"flag"
	"log"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"frapp8s/internal/config"
	"frapp8s/internal/exporter"
	"frapp8s/internal/logger"
)

func main() {
	configPath := flag.String(
		"config",
		"config.yaml",
		"Path to the configuration file",
	)
	flag.Parse()

	cfg, err := config.LoadConfig(*configPath)
	if err != nil {
		log.Fatalf("FATAL: Failed to load config: %v", err)
	}

	logger.SetupSlog(cfg)

	slog.Info("Effective Configuration Loaded:")
	if slog.Default().Enabled(nil, slog.LevelDebug) {
		if configJSON, err := cfg.ToFormattedJSON(); err == nil {
			slog.Debug("Loaded configuration:", "config", configJSON)
		} else {
			slog.Warn("Could not marshal config to JSON for debugging", "error", err)
		}
	}

	go exporter.StartMetricsServer(cfg.Prometheus.ListenAddress, cfg.Prometheus.MetricsPath, slog.Default())
	slog.Info("frapp8s is running. Press Ctrl+C to exit.")

	quitChannel := make(chan os.Signal, 1)
	signal.Notify(quitChannel, syscall.SIGINT, syscall.SIGTERM)
	<-quitChannel

	slog.Info("Shutting down frapp8s exporter...")
}
