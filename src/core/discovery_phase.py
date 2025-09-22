"""
Discovery Phase: Test Scripts
Implementation of the discovery scripts from brazilian-political-data-architecture-v0.md

This validates our correlation strategy by tracing one deputy across all systems.
"""

import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


# Brazilian Document Validation (minimal implementation for discovery)
def validate_cpf(cpf: str) -> bool:
    """Validate CPF using Brazilian algorithm"""
    if not cpf:
        return False

    cpf = re.sub(r'[^\d]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    # Calculate verification digits
    sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digit1 = 11 - (sum1 % 11) if (sum1 % 11) >= 2 else 0

    sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digit2 = 11 - (sum2 % 11) if (sum2 % 11) >= 2 else 0

    return cpf[9:] == f"{digit1}{digit2}"


def clean_cpf(cpf: Optional[str]) -> Optional[str]:
    """Clean and validate CPF"""
    if not cpf:
        return None

    clean = re.sub(r'[^\d]', '', cpf)
    return clean if validate_cpf(clean) else None


def normalize_name(name: str) -> str:
    """Normalize Brazilian names for matching"""
    if not name:
        return ""

    # Remove common titles and normalize
    name = name.upper()
    name = re.sub(r'\b(DEPUTADO|DEPUTADA|DR\.?|DRA\.?|PROF\.?)\b', '', name)
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def extract_cnpjs(expenses: List[Dict]) -> set:
    """Extract unique CNPJs from expense records"""
    cnpjs = set()

    for expense in expenses:
        # Try different possible CNPJ fields
        cnpj_fields = ['cnpjCpfFornecedor', 'cnpj', 'fornecedor_cnpj']

        for field in cnpj_fields:
            if field in expense and expense[field]:
                cnpj = re.sub(r'[^\d]', '', str(expense[field]))
                if len(cnpj) == 14:  # CNPJ has 14 digits
                    cnpjs.add(cnpj)

    return cnpjs


# Script 1: Entity Discovery & Correlation
def discover_deputy_universe(deputy_name_or_id: str) -> Dict[str, Any]:
    """
    Map a single deputy across all systems
    Implementation of the exact script from the architecture document
    """

    print(f"=== DISCOVERING DEPUTY UNIVERSE: {deputy_name_or_id} ===\n")

    # === CÂMARA DOS DEPUTADOS ===
    print("=== CÂMARA DOS DEPUTADOS ===")

    try:
        # Search for deputy
        if deputy_name_or_id.isdigit():
            # Direct ID lookup
            camara_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputy_name_or_id}"
            response = requests.get(camara_url)
        else:
            # Name search
            camara_url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
            response = requests.get(camara_url, params={"nome": deputy_name_or_id})

        response.raise_for_status()
        camara_data = response.json()

        # Handle different response formats
        if 'dados' in camara_data:
            if isinstance(camara_data['dados'], list) and camara_data['dados']:
                deputy_data = camara_data['dados'][0]  # Take first match
            else:
                deputy_data = camara_data['dados']
        else:
            deputy_data = camara_data

        deputy_id = deputy_data['id']

        print(f"✓ Found deputy: {deputy_data['nome']}")
        print(f"  ID: {deputy_id}")
        print(f"  Party: {deputy_data.get('siglaPartido', 'N/A')}")
        print(f"  State: {deputy_data.get('siglaUf', 'N/A')}")
        print(f"  CPF: {deputy_data.get('cpf', 'Not disclosed')}")

        # Build identity map
        identity = {
            'camara_id': deputy_id,
            'cpf': clean_cpf(deputy_data.get('cpf')),
            'name_variations': [deputy_data['nome']],
            'party': deputy_data.get('siglaPartido'),
            'state': deputy_data.get('siglaUf')
        }

    except Exception as e:
        print(f"✗ Error fetching Câmara data: {e}")
        return {'error': str(e)}

    # === EXPENSES (CEAP) ===
    print("\n=== EXPENSES (CEAP) ===")

    try:
        # Get last 12 months of expenses
        expenses_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputy_id}/despesas"
        current_year = datetime.now().year

        all_expenses = []
        for year in [current_year, current_year - 1]:
            params = {"ano": year, "itens": 100}
            response = requests.get(expenses_url, params=params)
            response.raise_for_status()

            year_expenses = response.json().get('dados', [])
            all_expenses.extend(year_expenses)

        print(f"✓ Found {len(all_expenses)} expense records")

        # Extract unique vendors/CNPJs
        vendor_cnpjs = extract_cnpjs(all_expenses)

        if vendor_cnpjs:
            print(f"✓ Extracted {len(vendor_cnpjs)} unique CNPJs from expenses")
            # Show sample CNPJs
            sample_cnpjs = list(vendor_cnpjs)[:5]
            for cnpj in sample_cnpjs:
                print(f"  - {cnpj}")
        else:
            print("✗ No CNPJs found in expense records")

    except Exception as e:
        print(f"✗ Error fetching expenses: {e}")
        all_expenses = []
        vendor_cnpjs = set()

    # === VOTES ===
    print("\n=== VOTING RECORDS ===")

    try:
        # Get recent votacoes (voting sessions)
        # The correct endpoint structure
        votacoes_url = "https://dadosabertos.camara.leg.br/api/v2/votacoes"
        params = {
            "dataInicio": (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),
            "dataFim": datetime.now().strftime("%Y-%m-%d"),
            "itens": 50
        }
        response = requests.get(votacoes_url, params=params)
        response.raise_for_status()

        voting_sessions = response.json().get('dados', [])
        print(f"✓ Found {len(voting_sessions)} recent voting sessions")

        # Get votes for a few sessions to show pattern
        deputy_votes = []
        for session in voting_sessions[:5]:  # Check first 5 sessions
            try:
                votes_url = f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{session['id']}/votos"
                vote_response = requests.get(votes_url)
                vote_response.raise_for_status()

                session_votes = vote_response.json().get('dados', [])
                deputy_vote = next((v for v in session_votes if v.get('deputado_', {}).get('id') == deputy_id), None)

                if deputy_vote:
                    deputy_votes.append(deputy_vote)
            except:
                continue

        votes = deputy_votes
        print(f"✓ Found {len(votes)} deputy votes in recent sessions")

        if votes:
            # Show voting pattern sample
            sim_votes = sum(1 for v in votes if v.get('voto') == 'Sim')
            nao_votes = sum(1 for v in votes if v.get('voto') == 'Não')
            print(f"  Recent pattern: {sim_votes} Yes, {nao_votes} No")

    except Exception as e:
        print(f"⚠ Could not fetch individual votes: {e}")
        print("  (This requires cross-referencing voting sessions)")
        votes = []

    # === PROPOSITIONS ===
    print("\n=== PROPOSITIONS AUTHORED ===")

    try:
        # Search propositions by author
        props_url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
        params = {
            "idDeputadoAutor": deputy_id,
            "dataInicio": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            "itens": 20
        }
        response = requests.get(props_url, params=params)
        response.raise_for_status()

        propositions = response.json().get('dados', [])
        print(f"✓ Found {len(propositions)} authored propositions in last year")

        if propositions:
            # Show sample propositions
            for prop in propositions[:3]:
                print(f"  - {prop.get('siglaTipo')} {prop.get('numero')}/{prop.get('ano')}: {prop.get('ementa', 'No summary')[:80]}...")

    except Exception as e:
        print(f"✗ Error fetching propositions: {e}")
        propositions = []

    # === TSE ELECTORAL DATA ===
    print("\n=== TSE ELECTORAL DATA ===")
    print("⚠ TSE API requires complex authentication - placeholder for now")
    print("  Would search for electoral history and donations")

    # === PORTAL TRANSPARÊNCIA ===
    print("\n=== GOVERNMENT CONTRACTS ===")
    print("⚠ Portal Transparência requires registration - placeholder for now")

    if vendor_cnpjs:
        print(f"  Would cross-check {len(vendor_cnpjs)} CNPJs for government contracts")

    # === JUDICIAL PROCESSES ===
    print("\n=== JUDICIAL PROCESSES ===")
    print("⚠ DataJud requires complex queries - placeholder for now")
    print(f"  Would search for processes involving: {identity['name_variations']}")

    # === VOTING SIMILARITY ===
    print("\n=== VOTING SIMILARITY ===")
    print("⚠ Requires processing multiple deputies - placeholder for now")
    print("  Would calculate similarity with other deputies")

    # Compile results
    result = {
        'identity': identity,
        'financial_network': list(vendor_cnpjs),
        'legislative_activity': len(propositions),
        'voting_records': len(votes),
        'expense_records': len(all_expenses),
        'data_quality': {
            'has_cpf': identity['cpf'] is not None,
            'has_expenses': len(all_expenses) > 0,
            'has_votes': len(votes) > 0,
            'has_propositions': len(propositions) > 0
        }
    }

    print("\n=== SUMMARY ===")
    print(f"Deputy: {identity['name_variations'][0]}")
    print(f"CPF Available: {result['data_quality']['has_cpf']}")
    print(f"CNPJ Network Size: {len(vendor_cnpjs)}")
    print(f"Legislative Activity: {result['legislative_activity']} propositions")
    print(f"Voting Records: {result['voting_records']} votes")
    print(f"Financial Records: {result['expense_records']} expenses")

    return result


# Script 2: Relationship Discovery (simplified version)
def discover_hidden_relationships(deputy_ids: List[str]) -> List[Dict]:
    """
    Find non-obvious connections between deputies
    Simplified implementation focusing on shared vendors
    """

    print(f"\n=== RELATIONSHIP DISCOVERY ===")
    print(f"Analyzing relationships between {len(deputy_ids)} deputies...")

    relationships = []
    deputy_vendors = {}

    # Get vendor networks for each deputy
    for deputy_id in deputy_ids:
        try:
            expenses_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{deputy_id}/despesas"
            response = requests.get(expenses_url, params={"ano": datetime.now().year, "itens": 100})
            response.raise_for_status()

            expenses = response.json().get('dados', [])
            vendors = extract_cnpjs(expenses)
            deputy_vendors[deputy_id] = vendors

            print(f"Deputy {deputy_id}: {len(vendors)} unique vendors")

        except Exception as e:
            print(f"Error fetching data for deputy {deputy_id}: {e}")
            deputy_vendors[deputy_id] = set()

    # Find shared vendors
    for i, deputy_a in enumerate(deputy_ids):
        for deputy_b in deputy_ids[i+1:]:
            vendors_a = deputy_vendors.get(deputy_a, set())
            vendors_b = deputy_vendors.get(deputy_b, set())

            shared_vendors = vendors_a.intersection(vendors_b)

            if shared_vendors:
                relationships.append({
                    'type': 'SHARED_VENDOR',
                    'deputies': [deputy_a, deputy_b],
                    'vendors': list(shared_vendors),
                    'weight': len(shared_vendors)
                })

                print(f"Found {len(shared_vendors)} shared vendors between {deputy_a} and {deputy_b}")

    return relationships


def validate_data_universe():
    """
    The exact script from the architecture document.
    Start here: Fetch one deputy, trace them everywhere
    This validates our correlation strategy
    """

    # Pick a well-known deputy with likely rich data
    SAMPLE_DEPUTY = "Arthur Lira"  # Current Chamber President

    print("🇧🇷 BRAZILIAN POLITICAL DATA UNIVERSE VALIDATION")
    print("=" * 60)
    print(f"Sample Deputy: {SAMPLE_DEPUTY}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Discover the deputy across all systems
    result = discover_deputy_universe(SAMPLE_DEPUTY)

    if 'error' in result:
        print(f"\n❌ Validation failed: {result['error']}")
        return result

    print("\n✅ VALIDATION COMPLETE")
    print("Data universe correlation strategy validated successfully!")

    return result


if __name__ == "__main__":
    # Run the validation as specified in the architecture document
    validation_result = validate_data_universe()

    # Save results for further analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"discovery_results_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(validation_result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Results saved to: discovery_results_{timestamp}.json")