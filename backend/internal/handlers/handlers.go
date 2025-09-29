package handlers

import (
	"net/http"
	"political-network-api/internal/database"
	"political-network-api/internal/models"
	"political-network-api/internal/utils"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

// GetPoliticians handles GET /api/politicians
func GetPoliticians(c *gin.Context) {
	start := time.Now()

	// Parse query parameters
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "500"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	// Validate limits
	if limit > 1000 {
		limit = 1000
	}

	// Cache key
	cacheKey := utils.CacheKey("politicians", limit, offset)

	// Try cache first
	if cached, found := utils.GetCache(cacheKey); found {
		c.JSON(http.StatusOK, models.APIResponse{
			Success: true,
			Data:    cached,
			Count:   len(cached.([]models.Politician)),
			Time:    time.Since(start).String(),
		})
		return
	}

	// Query database
	politicians, err := database.GetPoliticians(limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.APIResponse{
			Success: false,
			Error:   "Failed to fetch politicians: " + err.Error(),
			Time:    time.Since(start).String(),
		})
		return
	}

	// Cache result for 15 minutes
	utils.SetCache(cacheKey, politicians, 15*time.Minute)

	c.JSON(http.StatusOK, models.APIResponse{
		Success: true,
		Data:    politicians,
		Count:   len(politicians),
		Time:    time.Since(start).String(),
	})
}

// GetParties handles GET /api/parties
func GetParties(c *gin.Context) {
	start := time.Now()

	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	if limit > 1000 {
		limit = 1000
	}

	cacheKey := utils.CacheKey("parties", limit, offset)

	if cached, found := utils.GetCache(cacheKey); found {
		c.JSON(http.StatusOK, models.APIResponse{
			Success: true,
			Data:    cached,
			Count:   len(cached.([]models.Party)),
			Time:    time.Since(start).String(),
		})
		return
	}

	parties, err := database.GetParties(limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.APIResponse{
			Success: false,
			Error:   "Failed to fetch parties: " + err.Error(),
			Time:    time.Since(start).String(),
		})
		return
	}

	utils.SetCache(cacheKey, parties, 20*time.Minute)

	c.JSON(http.StatusOK, models.APIResponse{
		Success: true,
		Data:    parties,
		Count:   len(parties),
		Time:    time.Since(start).String(),
	})
}

// GetCompanies handles GET /api/companies
func GetCompanies(c *gin.Context) {
	start := time.Now()

	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "500"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	if limit > 1000 {
		limit = 1000
	}

	cacheKey := utils.CacheKey("companies", limit, offset)

	if cached, found := utils.GetCache(cacheKey); found {
		c.JSON(http.StatusOK, models.APIResponse{
			Success: true,
			Data:    cached,
			Count:   len(cached.([]models.Company)),
			Time:    time.Since(start).String(),
		})
		return
	}

	companies, err := database.GetCompanies(limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.APIResponse{
			Success: false,
			Error:   "Failed to fetch companies: " + err.Error(),
			Time:    time.Since(start).String(),
		})
		return
	}

	utils.SetCache(cacheKey, companies, 25*time.Minute)

	c.JSON(http.StatusOK, models.APIResponse{
		Success: true,
		Data:    companies,
		Count:   len(companies),
		Time:    time.Since(start).String(),
	})
}

// GetSanctions handles GET /api/sanctions
func GetSanctions(c *gin.Context) {
	start := time.Now()

	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "1000"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	if limit > 2000 {
		limit = 2000
	}

	cacheKey := utils.CacheKey("sanctions", limit, offset)

	if cached, found := utils.GetCache(cacheKey); found {
		c.JSON(http.StatusOK, models.APIResponse{
			Success: true,
			Data:    cached,
			Count:   len(cached.([]models.Sanction)),
			Time:    time.Since(start).String(),
		})
		return
	}

	sanctions, err := database.GetSanctions(limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.APIResponse{
			Success: false,
			Error:   "Failed to fetch sanctions: " + err.Error(),
			Time:    time.Since(start).String(),
		})
		return
	}

	utils.SetCache(cacheKey, sanctions, 30*time.Minute)

	c.JSON(http.StatusOK, models.APIResponse{
		Success: true,
		Data:    sanctions,
		Count:   len(sanctions),
		Time:    time.Since(start).String(),
	})
}

// GetConnections handles GET /api/connections
func GetConnections(c *gin.Context) {
	start := time.Now()

	cacheKey := "connections_all"

	if cached, found := utils.GetCache(cacheKey); found {
		c.JSON(http.StatusOK, models.APIResponse{
			Success: true,
			Data:    cached,
			Count:   len(cached.([]models.Connection)),
			Time:    time.Since(start).String(),
		})
		return
	}

	connections, err := database.GetConnections()
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.APIResponse{
			Success: false,
			Error:   "Failed to fetch connections: " + err.Error(),
			Time:    time.Since(start).String(),
		})
		return
	}

	// Cache connections for 20 minutes (they're expensive to compute)
	utils.SetCache(cacheKey, connections, 20*time.Minute)

	c.JSON(http.StatusOK, models.APIResponse{
		Success: true,
		Data:    connections,
		Count:   len(connections),
		Time:    time.Since(start).String(),
	})
}

// GetNetworkData handles GET /api/network - returns complete network for 3D visualization
func GetNetworkData(c *gin.Context) {
	start := time.Now()

	cacheKey := "network_complete"

	// Check cache first (this is an expensive operation)
	if cached, found := utils.GetCache(cacheKey); found {
		c.JSON(http.StatusOK, models.APIResponse{
			Success: true,
			Data:    cached,
			Time:    time.Since(start).String(),
		})
		return
	}

	// Build complete network data
	networkData, err := buildNetworkData()
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.APIResponse{
			Success: false,
			Error:   "Failed to build network data: " + err.Error(),
			Time:    time.Since(start).String(),
		})
		return
	}

	// Cache for 10 minutes (balance between performance and freshness)
	utils.SetCache(cacheKey, networkData, 10*time.Minute)

	c.JSON(http.StatusOK, models.APIResponse{
		Success: true,
		Data:    networkData,
		Time:    time.Since(start).String(),
	})
}

// buildNetworkData assembles complete network for 3D visualization
func buildNetworkData() (*models.NetworkResponse, error) {
	var nodes []interface{}

	// Get politicians (limit to active ones for performance)
	politicians, err := database.GetPoliticians(500, 0)
	if err != nil {
		return nil, err
	}

	// Transform politicians to network nodes
	for _, p := range politicians {
		node := models.NetworkNode{
			ID:              "politician_" + strconv.Itoa(p.ID),
			Type:            "politician",
			Name:            p.Nome,
			Size:            8.0 + float64(p.FinancialRecordsCount)*0.1,
			Color:           getPoliticianColor(p.CorruptionScore),
			CorruptionScore: p.CorruptionScore,
			Data:            p,
		}
		nodes = append(nodes, node)
	}

	// Get parties
	parties, err := database.GetParties(50, 0)
	if err != nil {
		return nil, err
	}

	for _, p := range parties {
		node := models.NetworkNode{
			ID:   "party_" + strconv.Itoa(p.ID),
			Type: "party",
			Name: p.Nome,
			Size: 12.0 + float64(p.TotalMembros)*0.2,
			Color: "#4ecdc4",
			Data:  p,
		}
		nodes = append(nodes, node)
	}

	// Get top companies (limit for performance)
	companies, err := database.GetCompanies(200, 0)
	if err != nil {
		return nil, err
	}

	for _, c := range companies {
		node := models.NetworkNode{
			ID:   "company_" + c.CNPJ,
			Type: "company",
			Name: c.NomeEmpresa,
			Size: 6.0 + (c.TotalValue/1000000)*2, // Scale by millions
			Color: "#ffe66d",
			Data:  c,
		}
		nodes = append(nodes, node)
	}

	// Get sanctions (limited set)
	sanctions, err := database.GetSanctions(300, 0)
	if err != nil {
		return nil, err
	}

	for _, s := range sanctions {
		node := models.NetworkNode{
			ID:   "sanction_" + strconv.Itoa(s.ID),
			Type: "sanction",
			Name: "Sanção: " + s.TipoSancao,
			Size: 4.0 + (s.ValorMulta/100000)*1, // Scale by value
			Color: "#ff8b94",
			Data:  s,
		}
		nodes = append(nodes, node)
	}

	// Get connections
	connections, err := database.GetConnections()
	if err != nil {
		return nil, err
	}

	// Get network stats
	stats, err := database.GetNetworkStats()
	if err != nil {
		return nil, err
	}

	stats.TotalNodes = len(nodes)
	stats.TotalLinks = len(connections)

	response := &models.NetworkResponse{
		Nodes: nodes,
		Links: connections,
		Stats: stats,
	}

	return response, nil
}

// getPoliticianColor returns color based on corruption score
func getPoliticianColor(score int) string {
	if score > 50 {
		return "#ff4757" // High corruption - red
	} else if score > 20 {
		return "#ffa502" // Medium corruption - orange
	}
	return "#ff6b6b" // Low corruption - light red
}

// HealthCheck handles GET /health
func HealthCheck(c *gin.Context) {
	start := time.Now()

	// Check database
	dbStatus := "healthy"
	if err := database.Health(); err != nil {
		dbStatus = "unhealthy: " + err.Error()
	}

	// Check cache
	cacheStatus := "healthy"
	cacheStats := utils.GetCacheStats()

	health := models.HealthCheck{
		Status:    "healthy",
		Database:  dbStatus,
		Cache:     cacheStatus,
		Uptime:    time.Since(start).String(),
		Version:   "1.0.0",
		Timestamp: time.Now(),
	}

	// Add cache stats
	if stats, ok := cacheStats["items"].(int); ok {
		health.Cache = "healthy (" + strconv.Itoa(stats) + " items)"
	}

	c.JSON(http.StatusOK, health)
}

// ClearCache handles POST /api/cache/clear
func ClearCache(c *gin.Context) {
	utils.FlushCache()
	c.JSON(http.StatusOK, models.APIResponse{
		Success: true,
		Data:    "Cache cleared successfully",
		Time:    "0ms",
	})
}

// GetStats handles GET /api/stats
func GetStats(c *gin.Context) {
	start := time.Now()

	cacheKey := "stats_network"

	if cached, found := utils.GetCache(cacheKey); found {
		c.JSON(http.StatusOK, models.APIResponse{
			Success: true,
			Data:    cached,
			Time:    time.Since(start).String(),
		})
		return
	}

	stats, err := database.GetNetworkStats()
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.APIResponse{
			Success: false,
			Error:   "Failed to get stats: " + err.Error(),
			Time:    time.Since(start).String(),
		})
		return
	}

	// Cache stats for 5 minutes
	utils.SetCache(cacheKey, stats, 5*time.Minute)

	c.JSON(http.StatusOK, models.APIResponse{
		Success: true,
		Data:    stats,
		Time:    time.Since(start).String(),
	})
}