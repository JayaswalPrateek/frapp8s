package logger

import (
	"log"
	"log/slog"
	"os"
	"strings"

	"frapp8s/internal/config"
)

func SetupSlog(cfg *config.Config) {
	var logLevel slog.Level
	switch strings.ToLower(cfg.ExporterLogging.Level) {
	case "debug":
		logLevel = slog.LevelDebug
	case "info":
		logLevel = slog.LevelInfo
	case "warn":
		logLevel = slog.LevelWarn
	case "error":
		logLevel = slog.LevelError
	default:
		log.Printf("Warning: Invalid ExporterLogging Level '%s', defaulting to 'info'",
			cfg.ExporterLogging.Level)
		logLevel = slog.LevelInfo
	}

	handlerOpts := &slog.HandlerOptions{
		Level:     logLevel,
		AddSource: true,
	}

	var handler slog.Handler
	switch strings.ToLower(cfg.ExporterLogging.Format) {
	case "json":
		handler = slog.NewJSONHandler(os.Stdout, handlerOpts)
	case "text":
		handler = slog.NewTextHandler(os.Stdout, handlerOpts)
	default:
		log.Printf("Warning: Invalid ExporterLogging Format '%s', defaulting to 'text'",
			cfg.ExporterLogging.Format)
		handler = slog.NewTextHandler(os.Stdout, handlerOpts)
	}

	logger := slog.New(handler)
	slog.SetDefault(logger)

	slog.Info("Application logger initialized successfully",
		"configured_level", cfg.ExporterLogging.Level,
		"actual_level", logLevel.String(),
		"format", cfg.ExporterLogging.Format,
	)
}
