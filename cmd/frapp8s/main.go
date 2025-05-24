package main

import (
	"flag"
	"log"
	"os"

	"frapp8s/internal/config"
)

func main() {
	log.SetOutput(os.Stdout)
	log.Println("Starting frapp8s exporter...")

	configPath := flag.String("config", "config.yaml", "Path to the configuration file")
	flag.Parse()

	log.Printf("Loading configuration from: %s", *configPath)
	cfg, err := config.LoadConfig(*configPath)
	if err != nil {
		log.Fatalf("FATAL: Failed to load config: %v", err)
	}

	log.Println("Configuration loaded successfully.")
	cfg.PrintAsJSON() // Print the final config (after defaults, file, env)
}
