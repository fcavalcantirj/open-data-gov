package utils

import (
	"encoding/json"
	"log"
	"time"

	"github.com/patrickmn/go-cache"
)

var Cache *cache.Cache

// InitializeCache sets up in-memory cache for high performance
func InitializeCache() {
	// Cache with 30-minute default expiration and 5-minute cleanup interval
	Cache = cache.New(30*time.Minute, 5*time.Minute)
	log.Println("✅ Cache initialized")
}

// Get retrieves data from cache
func GetCache(key string) (interface{}, bool) {
	return Cache.Get(key)
}

// Set stores data in cache
func SetCache(key string, data interface{}, duration time.Duration) {
	Cache.Set(key, data, duration)
}

// GetOrSet retrieves from cache or executes function and caches result
func GetOrSet(key string, duration time.Duration, fn func() (interface{}, error)) (interface{}, error) {
	// Try to get from cache first
	if cached, found := Cache.Get(key); found {
		return cached, nil
	}

	// Not in cache, execute function
	result, err := fn()
	if err != nil {
		return nil, err
	}

	// Store in cache
	Cache.Set(key, result, duration)
	return result, nil
}

// Delete removes item from cache
func DeleteCache(key string) {
	Cache.Delete(key)
}

// FlushCache clears all cache
func FlushCache() {
	Cache.Flush()
	log.Println("🧹 Cache flushed")
}

// GetCacheStats returns cache statistics
func GetCacheStats() map[string]interface{} {
	return map[string]interface{}{
		"items": Cache.ItemCount(),
	}
}

// CacheKey generates consistent cache keys
func CacheKey(prefix string, params ...interface{}) string {
	key := prefix
	for _, param := range params {
		switch v := param.(type) {
		case string:
			key += "_" + v
		case int:
			key += "_" + string(rune(v))
		default:
			if b, err := json.Marshal(v); err == nil {
				key += "_" + string(b)
			}
		}
	}
	return key
}