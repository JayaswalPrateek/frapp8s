package config

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"github.com/spf13/viper"
)

type Config struct {
	Prometheus struct {
		ListenAddress string `mapstructure:"listen_address"`
		MetricsPath   string `mapstructure:"metrics_path"`
	} `mapstructure:"prometheus"`

	Frappe struct {
		Benches   []string `mapstructure:"benches"`
		LogFiles  []string `mapstructure:"log_files"`
		LogFormat string   `mapstructure:"log_format"`
	} `mapstructure:"frappe"`

	Pipeline struct {
		ChannelBufferSize int `mapstructure:"channel_buffer_size"`
		ConsumerWorkers   int `mapstructure:"consumer_workers"`
	} `mapstructure:"pipeline"`

	Parser struct {
		MinSQLDurationMs int      `mapstructure:"min_sql_duration_ms"`
		ExcludeSites     []string `mapstructure:"exclude_sites"`
		ExcludeMethods   []string `mapstructure:"exclude_methods"`
		ExcludeDoctypes  []string `mapstructure:"exclude_doctypes"`
	} `mapstructure:"parser"`

	ExporterLogging struct {
		Level  string `mapstructure:"level"`
		Format string `mapstructure:"format"`
	} `mapstructure:"exporter_logging"`
}

func (c *Config) ToFormattedJSON() (string, error) {
	out, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return "", fmt.Errorf("error marshaling config to JSON: %w", err)
	}
	return string(out), nil
}

func LoadConfig(configPath string) (*Config, error) {
	v := viper.New()

	v.SetDefault("prometheus.listen_address", ":9876")
	v.SetDefault("prometheus.metrics_path", "/metrics")
	v.SetDefault("frappe.log_files", []string{"frappe.log", "database.log"})
	v.SetDefault("frappe.log_format", "text")
	v.SetDefault("pipeline.channel_buffer_size", 10000)
	v.SetDefault("pipeline.consumer_workers", 4)
	v.SetDefault("parser.min_sql_duration_ms", 0)
	v.SetDefault("parser.exclude_sites", []string{})
	v.SetDefault("parser.exclude_methods", []string{})
	v.SetDefault("parser.exclude_doctypes", []string{})
	v.SetDefault("exporter_logging.level", "info")
	v.SetDefault("exporter_logging.format", "text")

	v.SetConfigFile(configPath)
	v.SetConfigType("yaml")

	v.SetEnvPrefix("FRAPP8S")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	v.AutomaticEnv()

	if err := v.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			log.Printf("Warning: Config file '%s' not found. Using defaults and environment variables", configPath)
		} else {
			return nil, fmt.Errorf("failed to read config file '%s': %w", configPath, err)
		}
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	if err := cfg.Validate(); err != nil {
		return nil, err
	}

	return &cfg, nil
}
