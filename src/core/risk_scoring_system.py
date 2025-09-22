#!/usr/bin/env python3
"""
TRANSPARENT RISK SCORING SYSTEM
Open, adjustable, and scientifically-based metric framework

This establishes OUR methodology for calculating risk scores from 0 to 1
Every factor is weighted, documented, and adjustable
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import math


@dataclass
class RiskIndicator:
    """Single risk indicator with its properties"""
    id: str
    name: str
    description: str
    category: str
    raw_value: Any
    normalized_value: float  # 0 to 1
    weight: float
    confidence: float  # How confident we are in this data
    source: str
    verification_url: Optional[str] = None
    calculation_method: Optional[str] = None


class TransparentRiskScoring:
    """
    Transparent Risk Scoring System

    Categories:
    1. Financial Irregularities
    2. Network Patterns
    3. Legal/Compliance Issues
    4. Transparency Failures
    5. Statistical Anomalies
    """

    def __init__(self, config: Dict[str, float] = None):
        """Initialize with adjustable configuration"""

        # Default weights for each category (sum to 1.0)
        self.default_weights = {
            'financial_irregularities': 0.30,  # 30% weight
            'network_patterns': 0.25,          # 25% weight
            'legal_compliance': 0.20,          # 20% weight
            'transparency_failures': 0.15,     # 15% weight
            'statistical_anomalies': 0.10      # 10% weight
        }

        # Override with custom config if provided
        self.weights = config if config else self.default_weights

        # Ensure weights sum to 1.0
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            print(f"⚠️ Warning: Weights sum to {total_weight}, normalizing to 1.0")
            self.weights = {k: v/total_weight for k, v in self.weights.items()}

        self.indicators: List[RiskIndicator] = []

    def calculate_financial_irregularities(self, financial_data: Dict) -> List[RiskIndicator]:
        """Calculate financial irregularity indicators"""
        indicators = []

        # 1. Sanctioned Vendor Ratio
        sanctioned_ratio = financial_data.get('sanctioned_vendor_ratio', 0)
        indicators.append(RiskIndicator(
            id='fin_001',
            name='Taxa de Fornecedores Sancionados',
            description='Percentual de fornecedores que possuem sanções oficiais',
            category='financial_irregularities',
            raw_value=f"{sanctioned_ratio:.1%}",
            normalized_value=min(sanctioned_ratio * 2, 1.0),  # Double weight, cap at 1
            weight=0.4,
            confidence=1.0,
            source='Portal da Transparência',
            calculation_method='(fornecedores_sancionados / total_fornecedores) * 2'
        ))

        # 2. Money to Sanctioned Companies
        sanctioned_money_ratio = financial_data.get('sanctioned_money_ratio', 0)
        indicators.append(RiskIndicator(
            id='fin_002',
            name='Dinheiro para Empresas Sancionadas',
            description='Percentual do dinheiro que foi para empresas punidas',
            category='financial_irregularities',
            raw_value=f"R$ {financial_data.get('sanctioned_money_amount', 0):,.2f}",
            normalized_value=min(sanctioned_money_ratio * 3, 1.0),  # Triple weight
            weight=0.3,
            confidence=1.0,
            source='Câmara dos Deputados + Portal Transparência',
            calculation_method='(valor_sancionados / valor_total) * 3'
        ))

        # 3. Expense Concentration
        top_10_concentration = financial_data.get('top_10_vendor_concentration', 0)
        indicators.append(RiskIndicator(
            id='fin_003',
            name='Concentração de Fornecedores',
            description='Quanto dos gastos está concentrado nos top 10 fornecedores',
            category='financial_irregularities',
            raw_value=f"{top_10_concentration:.1%}",
            normalized_value=max(0, (top_10_concentration - 0.3) * 1.43),  # Above 30% is concerning
            weight=0.2,
            confidence=1.0,
            source='Câmara dos Deputados',
            calculation_method='max(0, (concentração - 0.3) * 1.43)'
        ))

        # 4. Unusual Spending Patterns
        spending_variance = financial_data.get('spending_variance', 0)
        indicators.append(RiskIndicator(
            id='fin_004',
            name='Padrão de Gastos Irregular',
            description='Variância nos padrões de gastos mensais',
            category='financial_irregularities',
            raw_value=f"σ² = {spending_variance:.2f}",
            normalized_value=min(spending_variance / 100, 1.0),
            weight=0.1,
            confidence=0.8,
            source='Câmara dos Deputados',
            calculation_method='variância_normalizada / 100'
        ))

        return indicators

    def calculate_network_patterns(self, network_data: Dict) -> List[RiskIndicator]:
        """Calculate network pattern indicators"""
        indicators = []

        # 1. Vendor Network Size
        unique_vendors = network_data.get('unique_vendors', 0)
        expected_vendors = 50  # Expected number for normal operations
        vendor_deviation = abs(unique_vendors - expected_vendors) / expected_vendors

        indicators.append(RiskIndicator(
            id='net_001',
            name='Tamanho da Rede de Fornecedores',
            description='Número de fornecedores únicos vs. esperado',
            category='network_patterns',
            raw_value=f"{unique_vendors} fornecedores",
            normalized_value=min(vendor_deviation, 1.0),
            weight=0.3,
            confidence=0.9,
            source='Câmara dos Deputados',
            calculation_method='|vendors - 50| / 50'
        ))

        # 2. Recurring Suspicious Vendors
        recurring_sanctioned = network_data.get('recurring_sanctioned_vendors', 0)
        indicators.append(RiskIndicator(
            id='net_002',
            name='Fornecedores Sancionados Recorrentes',
            description='Empresas sancionadas que recebem pagamentos repetidos',
            category='network_patterns',
            raw_value=f"{recurring_sanctioned} empresas",
            normalized_value=min(recurring_sanctioned / 3, 1.0),  # 3+ is maximum risk
            weight=0.4,
            confidence=1.0,
            source='Portal da Transparência',
            calculation_method='min(recorrentes / 3, 1.0)'
        ))

        # 3. Shell Company Indicators
        shell_company_signs = network_data.get('shell_company_indicators', 0)
        indicators.append(RiskIndicator(
            id='net_003',
            name='Indicadores de Empresas de Fachada',
            description='Empresas com características suspeitas (mesmo endereço, sócios, etc)',
            category='network_patterns',
            raw_value=f"{shell_company_signs} indicadores",
            normalized_value=min(shell_company_signs / 5, 1.0),
            weight=0.3,
            confidence=0.7,
            source='Análise de Padrões',
            calculation_method='min(indicadores / 5, 1.0)'
        ))

        return indicators

    def calculate_legal_compliance(self, legal_data: Dict) -> List[RiskIndicator]:
        """Calculate legal/compliance indicators"""
        indicators = []

        # 1. TCU Disqualifications
        tcu_records = legal_data.get('tcu_disqualification_records', 0)
        indicators.append(RiskIndicator(
            id='leg_001',
            name='Inabilitações no TCU',
            description='Registros de punições no Tribunal de Contas da União',
            category='legal_compliance',
            raw_value=f"{tcu_records} registros",
            normalized_value=min(tcu_records / 10, 1.0),  # 10+ is maximum
            weight=0.4,
            confidence=1.0,
            source='TCU',
            verification_url='https://contas.tcu.gov.br/pessoal/app/pessoa/listarPessoas',
            calculation_method='min(registros / 10, 1.0)'
        ))

        # 2. Active Sanctions
        active_sanctions = legal_data.get('active_sanctions', 0)
        indicators.append(RiskIndicator(
            id='leg_002',
            name='Sanções Ativas',
            description='Número de sanções atualmente vigentes',
            category='legal_compliance',
            raw_value=f"{active_sanctions} sanções",
            normalized_value=min(active_sanctions / 5, 1.0),
            weight=0.3,
            confidence=1.0,
            source='Portal da Transparência',
            calculation_method='min(sanções / 5, 1.0)'
        ))

        # 3. Nepotism Records
        nepotism_cases = legal_data.get('nepotism_records', 0)
        indicators.append(RiskIndicator(
            id='leg_003',
            name='Registros de Nepotismo',
            description='Casos registrados no Cadastro Nacional de Nepotismo',
            category='legal_compliance',
            raw_value=f"{nepotism_cases} casos",
            normalized_value=min(nepotism_cases / 5, 1.0),
            weight=0.3,
            confidence=0.9,
            source='Portal da Transparência - CNEP',
            calculation_method='min(casos / 5, 1.0)'
        ))

        return indicators

    def calculate_transparency_failures(self, transparency_data: Dict) -> List[RiskIndicator]:
        """Calculate transparency failure indicators"""
        indicators = []

        # 1. Missing Documentation
        missing_docs_ratio = transparency_data.get('missing_documentation_ratio', 0)
        indicators.append(RiskIndicator(
            id='tra_001',
            name='Documentação Faltante',
            description='Percentual de despesas sem documentação adequada',
            category='transparency_failures',
            raw_value=f"{missing_docs_ratio:.1%}",
            normalized_value=missing_docs_ratio,
            weight=0.4,
            confidence=0.9,
            source='Câmara dos Deputados',
            calculation_method='docs_faltantes / total_docs'
        ))

        # 2. Delayed Reporting
        avg_reporting_delay = transparency_data.get('avg_reporting_delay_days', 0)
        indicators.append(RiskIndicator(
            id='tra_002',
            name='Atraso na Prestação de Contas',
            description='Média de dias de atraso na apresentação de documentos',
            category='transparency_failures',
            raw_value=f"{avg_reporting_delay} dias",
            normalized_value=min(avg_reporting_delay / 30, 1.0),  # 30+ days is maximum
            weight=0.3,
            confidence=0.8,
            source='Câmara dos Deputados',
            calculation_method='min(dias_atraso / 30, 1.0)'
        ))

        # 3. Information Quality
        info_quality_score = transparency_data.get('information_quality_score', 1.0)
        indicators.append(RiskIndicator(
            id='tra_003',
            name='Qualidade da Informação',
            description='Completude e clareza das informações fornecidas',
            category='transparency_failures',
            raw_value=f"{info_quality_score:.2f}",
            normalized_value=1.0 - info_quality_score,  # Invert: low quality = high risk
            weight=0.3,
            confidence=0.7,
            source='Análise de Dados',
            calculation_method='1.0 - quality_score'
        ))

        return indicators

    def calculate_statistical_anomalies(self, stats_data: Dict) -> List[RiskIndicator]:
        """Calculate statistical anomaly indicators"""
        indicators = []

        # 1. Probability of Pattern
        pattern_probability = stats_data.get('pattern_probability', 1.0)
        indicators.append(RiskIndicator(
            id='sta_001',
            name='Probabilidade Estatística do Padrão',
            description='Chance do padrão observado ocorrer naturalmente',
            category='statistical_anomalies',
            raw_value=f"{pattern_probability:.4%}",
            normalized_value=1.0 - pattern_probability if pattern_probability < 0.05 else 0,
            weight=0.5,
            confidence=0.9,
            source='Análise Estatística',
            calculation_method='1.0 - probabilidade se p < 0.05'
        ))

        # 2. Standard Deviations from Normal
        std_deviations = stats_data.get('standard_deviations', 0)
        indicators.append(RiskIndicator(
            id='sta_002',
            name='Desvios Padrão da Normalidade',
            description='Quantos desvios padrão os dados estão da média esperada',
            category='statistical_anomalies',
            raw_value=f"{std_deviations:.2f}σ",
            normalized_value=min(abs(std_deviations) / 3, 1.0),  # 3σ is maximum
            weight=0.5,
            confidence=0.9,
            source='Análise Estatística',
            calculation_method='min(|σ| / 3, 1.0)'
        ))

        return indicators

    def calculate_composite_score(self, all_data: Dict) -> Dict[str, Any]:
        """
        Calculate the final composite risk score

        Returns a detailed breakdown of the scoring
        """

        # Calculate all indicators
        financial_indicators = self.calculate_financial_irregularities(
            all_data.get('financial_data', {})
        )
        network_indicators = self.calculate_network_patterns(
            all_data.get('network_data', {})
        )
        legal_indicators = self.calculate_legal_compliance(
            all_data.get('legal_data', {})
        )
        transparency_indicators = self.calculate_transparency_failures(
            all_data.get('transparency_data', {})
        )
        statistical_indicators = self.calculate_statistical_anomalies(
            all_data.get('statistical_data', {})
        )

        # Store all indicators
        self.indicators = (
            financial_indicators +
            network_indicators +
            legal_indicators +
            transparency_indicators +
            statistical_indicators
        )

        # Calculate category scores
        category_scores = {}

        for category, weight in self.weights.items():
            category_indicators = [i for i in self.indicators if i.category == category.replace('_', '_')]

            if category_indicators:
                # Weighted average within category
                total_weight = sum(i.weight for i in category_indicators)
                if total_weight > 0:
                    category_score = sum(
                        i.normalized_value * i.weight * i.confidence
                        for i in category_indicators
                    ) / total_weight
                else:
                    category_score = 0
            else:
                category_score = 0

            category_scores[category] = {
                'score': category_score,
                'weight': weight,
                'weighted_score': category_score * weight,
                'indicators': len(category_indicators)
            }

        # Calculate final composite score
        final_score = sum(cs['weighted_score'] for cs in category_scores.values())

        # Calculate confidence level
        if self.indicators:
            avg_confidence = sum(i.confidence for i in self.indicators) / len(self.indicators)
        else:
            avg_confidence = 0

        # Determine risk level
        if final_score >= 0.8:
            risk_level = "CRÍTICO"
            risk_color = "#d32f2f"
        elif final_score >= 0.6:
            risk_level = "ALTO"
            risk_color = "#ff6f00"
        elif final_score >= 0.4:
            risk_level = "MODERADO"
            risk_color = "#ffa000"
        elif final_score >= 0.2:
            risk_level = "BAIXO"
            risk_color = "#388e3c"
        else:
            risk_level = "MÍNIMO"
            risk_color = "#1976d2"

        return {
            'final_score': final_score,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'confidence': avg_confidence,
            'category_scores': category_scores,
            'total_indicators': len(self.indicators),
            'indicators': self.indicators,
            'weights_used': self.weights,
            'calculation_timestamp': datetime.now().isoformat()
        }

    def explain_score(self, score_result: Dict) -> str:
        """Generate human-readable explanation of the score"""

        explanation = []
        explanation.append(f"🎯 SCORE FINAL: {score_result['final_score']:.3f}")
        explanation.append(f"📊 Nível de Risco: {score_result['risk_level']}")
        explanation.append(f"🔍 Confiança na Análise: {score_result['confidence']:.1%}")
        explanation.append("")

        explanation.append("📈 BREAKDOWN POR CATEGORIA:")
        for category, data in score_result['category_scores'].items():
            category_name = category.replace('_', ' ').title()
            explanation.append(
                f"  • {category_name}: {data['score']:.3f} "
                f"(peso {data['weight']:.0%}) = {data['weighted_score']:.3f}"
            )

        explanation.append("")
        explanation.append("🔝 TOP RISK INDICATORS:")

        # Sort indicators by their contribution to risk
        sorted_indicators = sorted(
            score_result['indicators'],
            key=lambda i: i.normalized_value * i.weight,
            reverse=True
        )[:5]

        for indicator in sorted_indicators:
            explanation.append(
                f"  • {indicator.name}: {indicator.raw_value} "
                f"(risco: {indicator.normalized_value:.2f})"
            )

        return "\n".join(explanation)

    def generate_formula_documentation(self) -> str:
        """Generate complete documentation of the scoring formula"""

        doc = []
        doc.append("=" * 60)
        doc.append("TRANSPARENT RISK SCORING FORMULA")
        doc.append("=" * 60)
        doc.append("")

        doc.append("FORMULA GERAL:")
        doc.append("Risk Score = Σ(Category_Score × Category_Weight)")
        doc.append("")

        doc.append("PESOS DAS CATEGORIAS:")
        for category, weight in self.weights.items():
            doc.append(f"  • {category}: {weight:.0%}")

        doc.append("")
        doc.append("CÁLCULO POR CATEGORIA:")
        doc.append("Category_Score = Σ(Indicator_Value × Indicator_Weight × Confidence) / Σ(Indicator_Weight)")

        doc.append("")
        doc.append("INDICADORES E SEUS CÁLCULOS:")

        # Group indicators by category
        categories = {}
        for indicator in self.indicators:
            if indicator.category not in categories:
                categories[indicator.category] = []
            categories[indicator.category].append(indicator)

        for category, indicators in categories.items():
            doc.append(f"\n{category.upper()}:")
            for ind in indicators:
                doc.append(f"  {ind.id}: {ind.name}")
                doc.append(f"    Cálculo: {ind.calculation_method}")
                doc.append(f"    Peso: {ind.weight:.0%}, Confiança: {ind.confidence:.0%}")

        doc.append("")
        doc.append("INTERPRETAÇÃO:")
        doc.append("  0.0 - 0.2: Risco MÍNIMO")
        doc.append("  0.2 - 0.4: Risco BAIXO")
        doc.append("  0.4 - 0.6: Risco MODERADO")
        doc.append("  0.6 - 0.8: Risco ALTO")
        doc.append("  0.8 - 1.0: Risco CRÍTICO")

        return "\n".join(doc)


def test_scoring_system():
    """Test the scoring system with Arthur Lira data"""

    # Arthur Lira actual data
    test_data = {
        'financial_data': {
            'sanctioned_vendor_ratio': 1.0,  # 100% of checked vendors are sanctioned
            'sanctioned_money_ratio': 0.078,  # 7.8% of money to sanctioned companies
            'sanctioned_money_amount': 7823.12,
            'top_10_vendor_concentration': 0.45,  # 45% to top 10 vendors
            'spending_variance': 25.5
        },
        'network_data': {
            'unique_vendors': 67,
            'recurring_sanctioned_vendors': 5,
            'shell_company_indicators': 2
        },
        'legal_data': {
            'tcu_disqualification_records': 25,
            'active_sanctions': 5,
            'nepotism_records': 15
        },
        'transparency_data': {
            'missing_documentation_ratio': 0.05,
            'avg_reporting_delay_days': 10,
            'information_quality_score': 0.8
        },
        'statistical_data': {
            'pattern_probability': 0.0001,  # 0.01% chance
            'standard_deviations': 4.2
        }
    }

    # Initialize scoring system
    scorer = TransparentRiskScoring()

    # Calculate score
    result = scorer.calculate_composite_score(test_data)

    # Print results
    print("=" * 60)
    print("RISK SCORING SYSTEM TEST")
    print("=" * 60)
    print()
    print(scorer.explain_score(result))
    print()
    print(scorer.generate_formula_documentation())

    # Save to JSON
    with open("risk_score_test.json", "w") as f:
        # Convert indicators to dict for JSON serialization
        result_json = result.copy()
        result_json['indicators'] = [
            {
                'id': i.id,
                'name': i.name,
                'description': i.description,
                'category': i.category,
                'raw_value': str(i.raw_value),
                'normalized_value': i.normalized_value,
                'weight': i.weight,
                'confidence': i.confidence,
                'source': i.source
            }
            for i in result['indicators']
        ]
        json.dump(result_json, f, indent=2, ensure_ascii=False)

    return result


if __name__ == "__main__":
    test_scoring_system()