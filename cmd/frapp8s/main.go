package main

import (
	"flag"
	"fmt"
	"log"
	"log/slog"

	"frapp8s/internal/config"
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
	configJSON, err := cfg.ToFormattedJSON()
	if err == nil {
		fmt.Println(configJSON)
	} else {
		slog.Warn("Could not marshal config to JSON for printing", "error", err)
	}
}
