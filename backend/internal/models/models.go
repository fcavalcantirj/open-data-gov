package models

import (
	"time"
)

// Politician represents a politician entity
type Politician struct {
	ID                       int       `json:"id" db:"id"`
	Nome                     string    `json:"nome" db:"nome"`
	CPF                      string    `json:"cpf" db:"cpf"`
	UF                       string    `json:"uf" db:"uf"`
	SiglaPartido             string    `json:"sigla_partido" db:"sigla_partido"`
	UltimoStatusSituacao     string    `json:"ultimo_status_situacao" db:"ultimo_status_situacao"`
	UltimoStatusEmail        string    `json:"ultimo_status_email" db:"ultimo_status_email"`
	CorruptionScore          int       `json:"corruption_score"`
	FinancialRecordsCount    int       `json:"financial_records_count"`
	CreatedAt                time.Time `json:"created_at" db:"created_at"`
	UpdatedAt                time.Time `json:"updated_at" db:"updated_at"`
}

// Party represents a political party
type Party struct {
	ID              int       `json:"id" db:"id"`
	Nome            string    `json:"nome" db:"nome"`
	Sigla           string    `json:"sigla" db:"sigla"`
	NumeroEleitoral int       `json:"numero_eleitoral" db:"numero_eleitoral"`
	Status          string    `json:"status" db:"status"`
	LiderAtual      string    `json:"lider_atual" db:"lider_atual"`
	LiderID         int       `json:"lider_id" db:"lider_id"`
	TotalMembros    int       `json:"total_membros" db:"total_membros"`
	TotalEfetivos   int       `json:"total_efetivos" db:"total_efetivos"`
	LegislaturaID   int       `json:"legislatura_id" db:"legislatura_id"`
	LogoURL         string    `json:"logo_url" db:"logo_url"`
	CreatedAt       time.Time `json:"created_at" db:"created_at"`
	UpdatedAt       time.Time `json:"updated_at" db:"updated_at"`
}

// Company represents a company/vendor entity
type Company struct {
	ID               string  `json:"id" db:"cnpj_cpf"`
	CNPJ             string  `json:"cnpj" db:"cnpj_cpf"`
	NomeEmpresa      string  `json:"nome_empresa" db:"nome_empresa"`
	TransactionCount int     `json:"transaction_count"`
	TotalValue       float64 `json:"total_value"`
	CreatedAt        time.Time `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time `json:"updated_at" db:"updated_at"`
}

// Sanction represents a government sanction
type Sanction struct {
	ID               int       `json:"id" db:"id"`
	TipoSancao       string    `json:"tipo_sancao" db:"tipo_sancao"`
	CNPJ             string    `json:"cnpj" db:"cnpj"`
	CPF              string    `json:"cpf" db:"cpf"`
	ValorMulta       float64   `json:"valor_multa" db:"valor_multa"`
	DataInicioSancao string    `json:"data_inicio_sancao" db:"data_inicio_sancao"`
	CreatedAt        time.Time `json:"created_at" db:"created_at"`
}

// Connection represents a network connection between entities
type Connection struct {
	SourceID   string  `json:"source_id"`
	TargetID   string  `json:"target_id"`
	Type       string  `json:"type"`
	Value      float64 `json:"value"`
	Strength   float64 `json:"strength"`
	Data       interface{} `json:"data,omitempty"`
}

// NetworkResponse represents the complete network data
type NetworkResponse struct {
	Nodes []interface{} `json:"nodes"`
	Links []Connection  `json:"links"`
	Stats NetworkStats  `json:"stats"`
}

// NetworkStats represents network statistics
type NetworkStats struct {
	TotalNodes      int `json:"total_nodes"`
	TotalLinks      int `json:"total_links"`
	Politicians     int `json:"politicians"`
	Parties         int `json:"parties"`
	Companies       int `json:"companies"`
	Sanctions       int `json:"sanctions"`
	LastUpdated     time.Time `json:"last_updated"`
	ProcessingTime  string    `json:"processing_time"`
}

// FinancialRecord represents a financial transaction
type FinancialRecord struct {
	ID           int     `json:"id" db:"id"`
	PoliticianID int     `json:"politician_id" db:"politician_id"`
	CNPJ         string  `json:"cnpj" db:"cnpj_cpf"`
	Valor        float64 `json:"valor" db:"valor"`
	DataDoc      string  `json:"data_doc" db:"data_doc"`
	NomeEmpresa  string  `json:"nome_empresa" db:"nome_empresa"`
	CreatedAt    time.Time `json:"created_at" db:"created_at"`
}

// PartyMembership represents party membership relationship
type PartyMembership struct {
	ID            int    `json:"id" db:"id"`
	PartyID       int    `json:"party_id" db:"party_id"`
	DeputyID      int    `json:"deputy_id" db:"deputy_id"`
	DeputyName    string `json:"deputy_name" db:"deputy_name"`
	LegislaturaID int    `json:"legislatura_id" db:"legislatura_id"`
	Status        string `json:"status" db:"status"`
	CreatedAt     time.Time `json:"created_at" db:"created_at"`
}

// NetworkNode represents a generic network node
type NetworkNode struct {
	ID              string      `json:"id"`
	Type            string      `json:"type"`
	Name            string      `json:"name"`
	Size            float64     `json:"size"`
	Color           string      `json:"color"`
	CorruptionScore int         `json:"corruption_score,omitempty"`
	Data            interface{} `json:"data"`
}

// APIResponse represents a standard API response
type APIResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
	Count   int         `json:"count,omitempty"`
	Time    string      `json:"processing_time"`
}

// HealthCheck represents health check response
type HealthCheck struct {
	Status      string    `json:"status"`
	Database    string    `json:"database"`
	Cache       string    `json:"cache"`
	Uptime      string    `json:"uptime"`
	Version     string    `json:"version"`
	Timestamp   time.Time `json:"timestamp"`
}

// QueryParams represents common query parameters
type QueryParams struct {
	Limit        int      `form:"limit" binding:"min=1,max=10000"`
	Offset       int      `form:"offset" binding:"min=0"`
	IncludeStats bool     `form:"include_stats"`
	NodeTypes    []string `form:"node_types"`
	MinScore     int      `form:"min_score" binding:"min=0,max=100"`
}