# Political Network API Makefile

# Variables
BINARY_NAME=political-network-api
MAIN_FILE=cmd/main.go
BUILD_DIR=bin

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOCLEAN=$(GOCMD) clean
GOTEST=$(GOCMD) test
GOGET=$(GOCMD) get
GOMOD=$(GOCMD) mod

# Build flags for optimization
BUILD_FLAGS=-ldflags="-w -s" -trimpath

.PHONY: all build clean test deps run dev docker-build docker-run help

# Default target
all: clean deps build

# Build the application
build:
	@echo "🔨 Building $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) $(BUILD_FLAGS) -o $(BUILD_DIR)/$(BINARY_NAME) $(MAIN_FILE)
	@echo "✅ Build complete: $(BUILD_DIR)/$(BINARY_NAME)"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning..."
	$(GOCLEAN)
	@rm -rf $(BUILD_DIR)
	@echo "✅ Clean complete"

# Download dependencies
deps:
	@echo "📦 Downloading dependencies..."
	$(GOMOD) download
	$(GOMOD) tidy
	@echo "✅ Dependencies ready"

# Run tests
test:
	@echo "🧪 Running tests..."
	$(GOTEST) -v ./...

# Run the application in development mode
dev:
	@echo "🚀 Starting development server..."
	@export GIN_MODE=debug && $(GOCMD) run $(MAIN_FILE)

# Run the built binary
run: build
	@echo "🚀 Starting $(BINARY_NAME)..."
	@cd $(BUILD_DIR) && ./$(BINARY_NAME)

# Initialize project (first time setup)
init:
	@echo "🏗️ Initializing project..."
	$(GOMOD) init political-network-api || true
	$(GOMOD) tidy
	@cp .env.example .env
	@echo "✅ Project initialized. Edit .env file with your configuration."

# Build for production (optimized)
build-prod:
	@echo "🏭 Building for production..."
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOBUILD) $(BUILD_FLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-linux $(MAIN_FILE)
	@echo "✅ Production build complete: $(BUILD_DIR)/$(BINARY_NAME)-linux"

# Build for multiple platforms
build-all:
	@echo "🌍 Building for multiple platforms..."
	@mkdir -p $(BUILD_DIR)
	# Linux
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOBUILD) $(BUILD_FLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-linux-amd64 $(MAIN_FILE)
	# macOS
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 $(GOBUILD) $(BUILD_FLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-darwin-amd64 $(MAIN_FILE)
	# Windows
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 $(GOBUILD) $(BUILD_FLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-windows-amd64.exe $(MAIN_FILE)
	@echo "✅ Multi-platform build complete"

# Check code quality
lint:
	@echo "🔍 Checking code quality..."
	@command -v golangci-lint >/dev/null 2>&1 || { echo "Installing golangci-lint..."; go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest; }
	golangci-lint run

# Format code
fmt:
	@echo "🎨 Formatting code..."
	$(GOCMD) fmt ./...
	@echo "✅ Code formatted"

# Security check
security:
	@echo "🔒 Running security checks..."
	@command -v gosec >/dev/null 2>&1 || { echo "Installing gosec..."; go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest; }
	gosec ./...

# Performance benchmarks
bench:
	@echo "⚡ Running benchmarks..."
	$(GOTEST) -bench=. -benchmem ./...

# Docker build
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t $(BINARY_NAME):latest .
	@echo "✅ Docker image built: $(BINARY_NAME):latest"

# Docker run
docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 8080:8080 --env-file .env $(BINARY_NAME):latest

# Quick start (development)
start: deps
	@echo "🚀 Quick starting development server..."
	@export POSTGRES_POOL_URL="postgresql://doadmin:AVNS_8IrH5dX8G8spzIEL6I9@weedpedia-prod-postgres-do-user-13240977-0.b.db.ondigitalocean.com:25061/open-data-gov-pool?sslmode=require" && \
	export GIN_MODE=debug && \
	export SERVER_PORT=8080 && \
	$(GOCMD) run $(MAIN_FILE)

# Production deployment helper
deploy: build-prod
	@echo "🚀 Deployment build ready!"
	@echo "Upload $(BUILD_DIR)/$(BINARY_NAME)-linux to your server"
	@echo "Set environment variables and run: ./$(BINARY_NAME)-linux"

# Generate API documentation
docs:
	@echo "📚 Generating API documentation..."
	@echo "API Endpoints:"
	@echo "GET /health - Health check"
	@echo "GET /api/politicians - Get politicians data"
	@echo "GET /api/parties - Get political parties"
	@echo "GET /api/companies - Get companies data"
	@echo "GET /api/sanctions - Get sanctions data"
	@echo "GET /api/connections - Get network connections"
	@echo "GET /api/network - Get complete network data for 3D visualization"
	@echo "GET /api/stats - Get network statistics"
	@echo "POST /api/cache/clear - Clear cache"

# Show help
help:
	@echo "Political Network API - Available commands:"
	@echo ""
	@echo "🏗️  Setup & Dependencies:"
	@echo "  init          - Initialize project (first time)"
	@echo "  deps          - Download dependencies"
	@echo ""
	@echo "🔨 Building:"
	@echo "  build         - Build application"
	@echo "  build-prod    - Build for production (Linux)"
	@echo "  build-all     - Build for multiple platforms"
	@echo "  clean         - Clean build artifacts"
	@echo ""
	@echo "🚀 Running:"
	@echo "  dev           - Run in development mode"
	@echo "  run           - Run built binary"
	@echo "  start         - Quick start with database"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  test          - Run tests"
	@echo "  lint          - Check code quality"
	@echo "  fmt           - Format code"
	@echo "  security      - Security checks"
	@echo "  bench         - Performance benchmarks"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  docs          - Show API endpoints"
	@echo "  help          - Show this help"
	@echo ""
	@echo "🚀 Quick Commands:"
	@echo "  make start    - Start development server with database"
	@echo "  make deploy   - Build for production deployment"