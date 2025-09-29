package database

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	_ "github.com/lib/pq"
)

var DB *sql.DB

// Config holds database configuration
type Config struct {
	Host         string
	Port         int
	User         string
	Password     string
	DBName       string
	SSLMode      string
	MaxOpenConns int
	MaxIdleConns int
	MaxLifetime  time.Duration
}

// LoadConfig loads database configuration from environment
func LoadConfig() *Config {
	port, _ := strconv.Atoi(getEnv("DB_PORT", "5432"))
	maxConns, _ := strconv.Atoi(getEnv("MAX_DB_CONNECTIONS", "50"))

	return &Config{
		Host:         getEnv("DB_HOST", "localhost"),
		Port:         port,
		User:         getEnv("DB_USER", "postgres"),
		Password:     getEnv("DB_PASSWORD", ""),
		DBName:       getEnv("DB_NAME", "political_transparency"),
		SSLMode:      getEnv("DB_SSLMODE", "disable"),
		MaxOpenConns: maxConns,
		MaxIdleConns: maxConns / 2,
		MaxLifetime:  5 * time.Minute,
	}
}

// Initialize establishes database connection with optimized settings
func Initialize() error {
	// Check for POSTGRES_POOL_URL first (for production)
	poolURL := os.Getenv("POSTGRES_POOL_URL")

	var connStr string
	var maxConns int

	if poolURL != "" {
		// Use pool URL directly
		connStr = poolURL
		maxConns = 25 // Conservative for shared pool
		log.Println("🔗 Using PostgreSQL Pool URL")
	} else {
		// Build from individual environment variables
		config := LoadConfig()
		connStr = fmt.Sprintf(
			"host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
			config.Host, config.Port, config.User, config.Password, config.DBName, config.SSLMode,
		)
		maxConns = config.MaxOpenConns
		log.Println("🔗 Using individual DB config")
	}

	var err error
	DB, err = sql.Open("postgres", connStr)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool for high performance
	DB.SetMaxOpenConns(maxConns)
	DB.SetMaxIdleConns(maxConns / 2)
	DB.SetConnMaxLifetime(5 * time.Minute)

	// Test connection
	if err := DB.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	log.Printf("✅ Database connected successfully (max_conns: %d)", maxConns)
	return nil
}

// Close closes the database connection
func Close() error {
	if DB != nil {
		return DB.Close()
	}
	return nil
}

// Health checks database connection health
func Health() error {
	if DB == nil {
		return fmt.Errorf("database not initialized")
	}
	return DB.Ping()
}

// GetStats returns database connection statistics
func GetStats() sql.DBStats {
	if DB == nil {
		return sql.DBStats{}
	}
	return DB.Stats()
}

// getEnv gets environment variable with default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}