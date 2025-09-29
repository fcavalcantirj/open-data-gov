package database

import (
	"database/sql"
	"fmt"
	"log"
	"political-network-api/internal/models"
	"time"
)

// GetPoliticians retrieves all politicians with optimized query
func GetPoliticians(limit, offset int) ([]models.Politician, error) {
	query := `
		SELECT
			p.id,
			COALESCE(p.nome_civil, p.nome_eleitoral, 'Unknown') as nome,
			COALESCE(p.cpf, '') as cpf,
			COALESCE(p.current_state, '') as uf,
			COALESCE(p.current_party, '') as sigla_partido,
			COALESCE(p.situacao, '') as ultimo_status_situacao,
			COALESCE(p.email, '') as ultimo_status_email,
			p.created_at, p.updated_at,
			0 as financial_records_count,
			COALESCE(CAST(p.corruption_risk_score AS INTEGER), 0) as corruption_score
		FROM unified_politicians p
		ORDER BY p.id
		LIMIT $1 OFFSET $2
	`

	rows, err := DB.Query(query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query politicians: %w", err)
	}
	defer rows.Close()

	var politicians []models.Politician
	for rows.Next() {
		var p models.Politician
		err := rows.Scan(
			&p.ID, &p.Nome, &p.CPF, &p.UF, &p.SiglaPartido,
			&p.UltimoStatusSituacao, &p.UltimoStatusEmail,
			&p.CreatedAt, &p.UpdatedAt, &p.FinancialRecordsCount, &p.CorruptionScore,
		)
		if err != nil {
			log.Printf("Error scanning politician: %v", err)
			continue
		}

		politicians = append(politicians, p)
	}

	return politicians, nil
}

// GetParties retrieves all political parties
func GetParties(limit, offset int) ([]models.Party, error) {
	query := `
		SELECT
			id, nome, sigla, COALESCE(numero_eleitoral, 0) as numero_eleitoral, COALESCE(status, '') as status,
			COALESCE(lider_atual, '') as lider_atual, lider_id, COALESCE(total_membros, 0) as total_membros, COALESCE(total_efetivos, 0) as total_efetivos,
			COALESCE(legislatura_id, 0) as legislatura_id, COALESCE(logo_url, '') as logo_url, created_at, updated_at
		FROM political_parties
		ORDER BY total_membros DESC
		LIMIT $1 OFFSET $2
	`

	rows, err := DB.Query(query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query parties: %w", err)
	}
	defer rows.Close()

	var parties []models.Party
	for rows.Next() {
		var p models.Party
		var liderID sql.NullInt64

		err := rows.Scan(
			&p.ID, &p.Nome, &p.Sigla, &p.NumeroEleitoral, &p.Status,
			&p.LiderAtual, &liderID, &p.TotalMembros, &p.TotalEfetivos,
			&p.LegislaturaID, &p.LogoURL, &p.CreatedAt, &p.UpdatedAt,
		)
		if err != nil {
			log.Printf("Error scanning party: %v", err)
			continue
		}

		if liderID.Valid {
			p.LiderID = int(liderID.Int64)
		}

		parties = append(parties, p)
	}

	return parties, nil
}

// GetCompanies retrieves company data with transaction aggregates
func GetCompanies(limit, offset int) ([]models.Company, error) {
	query := `
		SELECT
			fc.cnpj_cpf,
			COALESCE(fc.name, 'Unknown Company') as nome_empresa,
			COALESCE(fc.transaction_count, 0) as transaction_count,
			COALESCE(fc.total_transaction_amount, 0) as total_value,
			fc.created_at,
			fc.updated_at
		FROM financial_counterparts fc
		WHERE fc.cnpj_cpf IS NOT NULL
		  AND fc.entity_type = 'COMPANY'
		ORDER BY fc.total_transaction_amount DESC NULLS LAST
		LIMIT $1 OFFSET $2
	`

	rows, err := DB.Query(query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query companies: %w", err)
	}
	defer rows.Close()

	var companies []models.Company
	for rows.Next() {
		var c models.Company
		err := rows.Scan(
			&c.CNPJ, &c.NomeEmpresa, &c.TransactionCount,
			&c.TotalValue, &c.CreatedAt, &c.UpdatedAt,
		)
		if err != nil {
			log.Printf("Error scanning company: %v", err)
			continue
		}

		c.ID = c.CNPJ
		companies = append(companies, c)
	}

	return companies, nil
}

// GetSanctions retrieves sanctions data
func GetSanctions(limit, offset int) ([]models.Sanction, error) {
	query := `
		SELECT
			id,
			COALESCE(sanction_type, '') as tipo_sancao,
			COALESCE(cnpj_cpf, '') as cnpj,
			'' as cpf,
			COALESCE(penalty_amount, 0) as valor_multa,
			COALESCE(sanction_start_date::text, '') as data_inicio_sancao,
			created_at
		FROM vendor_sanctions
		WHERE cnpj_cpf IS NOT NULL AND cnpj_cpf != ''
		  AND is_active = true
		ORDER BY penalty_amount DESC NULLS LAST
		LIMIT $1 OFFSET $2
	`

	rows, err := DB.Query(query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query sanctions: %w", err)
	}
	defer rows.Close()

	var sanctions []models.Sanction
	for rows.Next() {
		var s models.Sanction
		var cnpj, cpf sql.NullString
		var valorMulta sql.NullFloat64

		err := rows.Scan(
			&s.ID, &s.TipoSancao, &cnpj, &cpf, &valorMulta,
			&s.DataInicioSancao, &s.CreatedAt,
		)
		if err != nil {
			log.Printf("Error scanning sanction: %v", err)
			continue
		}

		if cnpj.Valid {
			s.CNPJ = cnpj.String
		}
		if cpf.Valid {
			s.CPF = cpf.String
		}
		if valorMulta.Valid {
			s.ValorMulta = valorMulta.Float64
		}

		sanctions = append(sanctions, s)
	}

	return sanctions, nil
}

// GetConnections builds network connections between entities
func GetConnections() ([]models.Connection, error) {
	var connections []models.Connection

	// 1. Party memberships (politicians -> parties)
	partyConnections, err := getPartyMembershipConnections()
	if err != nil {
		log.Printf("Error getting party connections: %v", err)
	} else {
		connections = append(connections, partyConnections...)
	}

	// 2. Financial connections (politicians -> companies)
	financialConnections, err := getFinancialConnections()
	if err != nil {
		log.Printf("Error getting financial connections: %v", err)
	} else {
		connections = append(connections, financialConnections...)
	}

	// 3. Sanction connections (companies/politicians -> sanctions)
	sanctionConnections, err := getSanctionConnections()
	if err != nil {
		log.Printf("Error getting sanction connections: %v", err)
	} else {
		connections = append(connections, sanctionConnections...)
	}

	log.Printf("✅ Generated %d total connections", len(connections))
	return connections, nil
}

// getPartyMembershipConnections creates politician-party connections
func getPartyMembershipConnections() ([]models.Connection, error) {
	query := `
		SELECT
			up.id as politician_id,
			pm.party_id,
			COUNT(*) as strength
		FROM party_memberships pm
		JOIN unified_politicians up ON pm.deputy_id = up.deputy_id
		WHERE pm.status = 'Ativo'
		GROUP BY up.id, pm.party_id
	`

	rows, err := DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var connections []models.Connection
	for rows.Next() {
		var politicianID, partyID int
		var strength int

		err := rows.Scan(&politicianID, &partyID, &strength)
		if err != nil {
			continue
		}

		connections = append(connections, models.Connection{
			SourceID: fmt.Sprintf("politician_%d", politicianID),
			TargetID: fmt.Sprintf("party_%d", partyID),
			Type:     "party_membership",
			Value:    1.0,
			Strength: 1.0,
		})
	}

	return connections, nil
}

// getFinancialConnections creates politician-company financial connections
func getFinancialConnections() ([]models.Connection, error) {
	query := `
		SELECT
			fr.politician_id,
			fr.counterpart_cnpj_cpf as cnpj_cpf,
			COUNT(*) as transaction_count,
			SUM(fr.amount) as total_value
		FROM unified_financial_records fr
		WHERE fr.counterpart_cnpj_cpf IS NOT NULL
		  AND fr.counterpart_cnpj_cpf != ''
		  AND fr.amount > 0
		GROUP BY fr.politician_id, fr.counterpart_cnpj_cpf
		HAVING COUNT(*) >= 2 OR SUM(fr.amount) > 50000
		ORDER BY total_value DESC
		LIMIT 5000
	`

	rows, err := DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var connections []models.Connection
	for rows.Next() {
		var politicianID int
		var cnpj string
		var transactionCount int
		var totalValue float64

		err := rows.Scan(&politicianID, &cnpj, &transactionCount, &totalValue)
		if err != nil {
			continue
		}

		// Calculate connection strength (0.1 to 1.0)
		strength := 0.1 + (float64(transactionCount)/50.0)*0.9
		if strength > 1.0 {
			strength = 1.0
		}

		connections = append(connections, models.Connection{
			SourceID: fmt.Sprintf("politician_%d", politicianID),
			TargetID: fmt.Sprintf("company_%s", cnpj),
			Type:     "financial",
			Value:    totalValue,
			Strength: strength,
		})
	}

	return connections, nil
}

// getSanctionConnections creates sanction connections
func getSanctionConnections() ([]models.Connection, error) {
	query := `
		SELECT
			vs.id,
			vs.cnpj_cpf,
			vs.penalty_amount
		FROM vendor_sanctions vs
		WHERE vs.cnpj_cpf IS NOT NULL AND vs.cnpj_cpf != ''
		  AND vs.is_active = true
		LIMIT 2000
	`

	rows, err := DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var connections []models.Connection
	for rows.Next() {
		var sanctionID int
		var cnpjCpf string
		var valorMulta sql.NullFloat64

		err := rows.Scan(&sanctionID, &cnpjCpf, &valorMulta)
		if err != nil {
			continue
		}

		value := 0.0
		if valorMulta.Valid {
			value = valorMulta.Float64
		}

		// Connect to companies by CNPJ (assuming CNPJ if length > 11)
		if len(cnpjCpf) > 11 {
			connections = append(connections, models.Connection{
				SourceID: fmt.Sprintf("company_%s", cnpjCpf),
				TargetID: fmt.Sprintf("sanction_%d", sanctionID),
				Type:     "sanction",
				Value:    value,
				Strength: 1.0,
			})
		} else {
			// Connect to politicians by CPF (assuming CPF if length <= 11)
			var politicianID int
			cpfQuery := "SELECT id FROM unified_politicians WHERE cpf = $1 LIMIT 1"
			if err := DB.QueryRow(cpfQuery, cnpjCpf).Scan(&politicianID); err == nil {
				connections = append(connections, models.Connection{
					SourceID: fmt.Sprintf("politician_%d", politicianID),
					TargetID: fmt.Sprintf("sanction_%d", sanctionID),
					Type:     "sanction",
					Value:    value,
					Strength: 1.0,
				})
			}
		}
	}

	return connections, nil
}

// calculateCorruptionScore calculates corruption risk score for a politician (now using pre-calculated field)
func calculateCorruptionScore(politicianID int, cpf string) int {
	// This function is no longer used since we use the pre-calculated corruption_risk_score field
	// from the unified_politicians table. Kept for compatibility.
	return 0
}

// GetNetworkStats calculates network statistics
func GetNetworkStats() (models.NetworkStats, error) {
	var stats models.NetworkStats
	start := time.Now()

	// Count entities
	queries := map[string]*int{
		"SELECT COUNT(*) FROM unified_politicians":     &stats.Politicians,
		"SELECT COUNT(*) FROM political_parties":                                 &stats.Parties,
		"SELECT COUNT(*) FROM financial_counterparts": &stats.Companies,
		"SELECT COUNT(*) FROM vendor_sanctions WHERE is_active = true": &stats.Sanctions,
	}

	for query, target := range queries {
		if err := DB.QueryRow(query).Scan(target); err != nil {
			log.Printf("Error executing stats query: %v", err)
		}
	}

	stats.TotalNodes = stats.Politicians + stats.Parties + stats.Companies + stats.Sanctions
	stats.TotalLinks = 0 // Will be calculated by connections

	stats.LastUpdated = time.Now()
	stats.ProcessingTime = time.Since(start).String()

	return stats, nil
}

// GetCount returns total count for a table
func GetCount(table string) (int, error) {
	var count int
	query := fmt.Sprintf("SELECT COUNT(*) FROM %s", table)
	err := DB.QueryRow(query).Scan(&count)
	return count, err
}