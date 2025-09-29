package main

import (
	"log"
	"os"
	"political-network-api/internal/database"
	"political-network-api/internal/handlers"
	"political-network-api/internal/utils"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("⚠️ No .env file found, using environment variables")
	}

	// Initialize database
	if err := database.Initialize(); err != nil {
		log.Fatalf("❌ Failed to initialize database: %v", err)
	}
	defer database.Close()

	// Initialize cache
	utils.InitializeCache()

	// Setup Gin
	if os.Getenv("GIN_MODE") == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()

	// Middleware
	router.Use(gin.Logger())
	router.Use(gin.Recovery())

	// CORS configuration for frontend
	config := cors.DefaultConfig()
	config.AllowOrigins = []string{
		"http://localhost:3000",
		"http://127.0.0.1:3000",
		"https://open-data-gov.vercel.app", // Add your production domain
	}
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization"}
	config.ExposeHeaders = []string{"Content-Length"}
	config.AllowCredentials = true

	router.Use(cors.New(config))

	// Health check endpoint
	router.GET("/health", handlers.HealthCheck)

	// API routes
	api := router.Group("/api")
	{
		// Core data endpoints
		api.GET("/politicians", handlers.GetPoliticians)
		api.GET("/parties", handlers.GetParties)
		api.GET("/companies", handlers.GetCompanies)
		api.GET("/sanctions", handlers.GetSanctions)
		api.GET("/connections", handlers.GetConnections)

		// Complete network data for 3D visualization
		api.GET("/network", handlers.GetNetworkData)

		// Statistics and monitoring
		api.GET("/stats", handlers.GetStats)

		// Cache management
		api.POST("/cache/clear", handlers.ClearCache)
	}

	// Static file serving for frontend (optional)
	router.Static("/static", "./static")

	// Start server
	port := os.Getenv("SERVER_PORT")
	if port == "" {
		port = "8080"
	}

	host := os.Getenv("SERVER_HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	serverAddr := host + ":" + port

	log.Printf("🚀 Political Network API starting on %s", serverAddr)
	log.Printf("📊 API endpoints available at http://%s/api/", serverAddr)
	log.Printf("❤️ Health check at http://%s/health", serverAddr)

	if err := router.Run(serverAddr); err != nil {
		log.Fatalf("❌ Failed to start server: %v", err)
	}
}
