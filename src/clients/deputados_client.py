"""
Deputados (Câmara dos Deputados) API Client
Implementation for comprehensive Brazilian Deputies data access

Provides access to all Câmara dos Deputados API endpoints needed for
the unified political transparency database population.
"""

import requests
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime, date
import time
import re


class DeputadosClient:
    """
    Client for accessing Câmara dos Deputados open data API
    Based on API documented at dadosabertos.camara.leg.br
    """

    def __init__(self):
        self.base_url = "https://dadosabertos.camara.leg.br/api/v2/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Brazilian-Political-Transparency-Platform/1.0',
            'Accept': 'application/json'
        })
        self.rate_limit_delay = 0.5  # 500ms between requests

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with rate limiting and error handling"""
        url = f"{self.base_url}{endpoint}"

        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, params=params or {})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed for {endpoint}: {str(e)}")

    def get_all_deputies(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all deputies with basic information

        Args:
            active_only: If True, only return currently active deputies

        Returns:
            List of deputy basic information
        """
        params = {
            'ordem': 'ASC',
            'ordenarPor': 'nome'
        }

        if active_only:
            # Get current legislature deputies only
            params['idLegislatura'] = 57  # Current legislature (may need updating)

        response = self._make_request("deputados", params)
        return response.get('dados', [])

    def get_deputy_details(self, deputy_id: int) -> Dict[str, Any]:
        """
        Get complete deputy profile information

        Args:
            deputy_id: Deputy ID from the API

        Returns:
            Complete deputy profile data
        """
        response = self._make_request(f"deputados/{deputy_id}")
        return response.get('dados', {})

    def get_deputy_expenses(self, deputy_id: int, year: Optional[int] = None,
                          month: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get deputy expense records

        Args:
            deputy_id: Deputy ID
            year: Filter by specific year (optional)
            month: Filter by specific month (optional)

        Returns:
            List of expense records
        """
        params = {}
        if year:
            params['ano'] = year
        if month:
            params['mes'] = month

        response = self._make_request(f"deputados/{deputy_id}/despesas", params)
        return response.get('dados', [])

    def get_deputy_expenses_by_year_range(self, deputy_id: int,
                                        start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """
        Get deputy expenses for a range of years

        Args:
            deputy_id: Deputy ID
            start_year: Starting year (inclusive)
            end_year: Ending year (inclusive)

        Returns:
            Combined list of expense records across all years
        """
        all_expenses = []

        for year in range(start_year, end_year + 1):
            try:
                expenses = self.get_deputy_expenses(deputy_id, year)
                all_expenses.extend(expenses)
                print(f"✓ Collected {len(expenses)} expenses for {year}")
            except Exception as e:
                print(f"⚠️ Failed to get expenses for {year}: {e}")
                continue

        return all_expenses

    def get_deputy_committees(self, deputy_id: int) -> List[Dict[str, Any]]:
        """
        Get deputy committee memberships (orgãos)

        Args:
            deputy_id: Deputy ID

        Returns:
            List of committee membership records
        """
        response = self._make_request(f"deputados/{deputy_id}/orgaos")
        return response.get('dados', [])

    def get_deputy_fronts(self, deputy_id: int) -> List[Dict[str, Any]]:
        """
        Get deputy parliamentary front memberships

        Args:
            deputy_id: Deputy ID

        Returns:
            List of parliamentary front membership records
        """
        response = self._make_request(f"deputados/{deputy_id}/frentes")
        return response.get('dados', [])

    def get_deputy_external_mandates(self, deputy_id: int) -> List[Dict[str, Any]]:
        """
        Get deputy external mandate history

        Args:
            deputy_id: Deputy ID

        Returns:
            List of external mandate records
        """
        response = self._make_request(f"deputados/{deputy_id}/mandatosExternos")
        return response.get('dados', [])

    def get_deputy_events(self, deputy_id: int, start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get deputy event participation

        Args:
            deputy_id: Deputy ID
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)

        Returns:
            List of event participation records
        """
        params = {}
        if start_date:
            params['dataInicio'] = start_date
        if end_date:
            params['dataFim'] = end_date

        response = self._make_request(f"deputados/{deputy_id}/eventos", params)
        return response.get('dados', [])

    def get_deputy_professions(self, deputy_id: int) -> List[Dict[str, Any]]:
        """
        Get deputy profession classifications

        Args:
            deputy_id: Deputy ID

        Returns:
            List of profession records
        """
        response = self._make_request(f"deputados/{deputy_id}/profissoes")
        return response.get('dados', [])

    def get_deputy_occupations(self, deputy_id: int) -> List[Dict[str, Any]]:
        """
        Get deputy occupation history

        Args:
            deputy_id: Deputy ID

        Returns:
            List of occupation records
        """
        response = self._make_request(f"deputados/{deputy_id}/ocupacoes")
        return response.get('dados', [])

    def get_deputy_discourses(self, deputy_id: int, start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get deputy discourse/speech records

        Args:
            deputy_id: Deputy ID
            start_date: Start date filter (YYYY-MM-DD format)
            end_date: End date filter (YYYY-MM-DD format)

        Returns:
            List of discourse records
        """
        params = {}
        if start_date:
            params['dataInicio'] = start_date
        if end_date:
            params['dataFim'] = end_date

        response = self._make_request(f"deputados/{deputy_id}/discursos", params)
        return response.get('dados', [])

    def get_deputy_complete_profile(self, deputy_id: int,
                                  include_financial: bool = True,
                                  financial_years: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Get complete deputy profile across all endpoints

        Args:
            deputy_id: Deputy ID
            include_financial: Whether to include expense data
            financial_years: Specific years to collect financial data (defaults to last 5 years)

        Returns:
            Complete deputy profile with all available data
        """
        print(f"📊 Collecting complete profile for deputy {deputy_id}")

        profile = {
            'deputy_id': deputy_id,
            'collection_timestamp': datetime.now().isoformat(),
            'basic_info': {},
            'expenses': [],
            'committees': [],
            'fronts': [],
            'external_mandates': [],
            'events': [],
            'professions': [],
            'occupations': [],
            'summary': {
                'total_expenses': 0,
                'total_committees': 0,
                'total_fronts': 0,
                'total_events': 0
            }
        }

        try:
            # Basic information
            print("  → Basic information")
            profile['basic_info'] = self.get_deputy_details(deputy_id)

            # Financial data
            if include_financial:
                if not financial_years:
                    current_year = datetime.now().year
                    financial_years = list(range(current_year - 4, current_year + 1))

                print(f"  → Financial data for years: {financial_years}")
                for year in financial_years:
                    try:
                        year_expenses = self.get_deputy_expenses(deputy_id, year)
                        profile['expenses'].extend(year_expenses)
                    except Exception as e:
                        print(f"    ⚠️ Failed to get expenses for {year}: {e}")

            # Committee memberships
            print("  → Committee memberships")
            profile['committees'] = self.get_deputy_committees(deputy_id)

            # Parliamentary fronts
            print("  → Parliamentary fronts")
            profile['fronts'] = self.get_deputy_fronts(deputy_id)

            # External mandates
            print("  → External mandates")
            profile['external_mandates'] = self.get_deputy_external_mandates(deputy_id)

            # Events (last year only to avoid overwhelming data)
            print("  → Recent events")
            last_year = datetime.now().year - 1
            start_date = f"{last_year}-01-01"
            end_date = f"{last_year}-12-31"
            profile['events'] = self.get_deputy_events(deputy_id, start_date, end_date)

            # Professional background
            print("  → Professional background")
            profile['professions'] = self.get_deputy_professions(deputy_id)
            profile['occupations'] = self.get_deputy_occupations(deputy_id)

            # Calculate summary statistics
            profile['summary'] = {
                'total_expenses': len(profile['expenses']),
                'total_expense_amount': sum(float(e.get('valorLiquido', 0)) for e in profile['expenses']),
                'total_committees': len(profile['committees']),
                'total_fronts': len(profile['fronts']),
                'total_external_mandates': len(profile['external_mandates']),
                'total_events': len(profile['events']),
                'total_professions': len(profile['professions']),
                'total_occupations': len(profile['occupations'])
            }

            print(f"✅ Profile collection complete:")
            print(f"    💰 {profile['summary']['total_expenses']} expenses")
            print(f"    🏛️ {profile['summary']['total_committees']} committees")
            print(f"    🤝 {profile['summary']['total_fronts']} fronts")
            print(f"    📋 {profile['summary']['total_external_mandates']} external mandates")
            print(f"    📅 {profile['summary']['total_events']} events")

        except Exception as e:
            print(f"❌ Error collecting profile: {e}")
            raise

        return profile

    def search_deputies_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Search for deputies by name

        Args:
            name: Deputy name to search for

        Returns:
            List of matching deputies
        """
        response = self._make_request("deputados", {"nome": name})
        return response.get('dados', [])

    def get_current_legislature(self) -> Dict[str, Any]:
        """
        Get current legislature information

        Returns:
            Current legislature details
        """
        response = self._make_request("legislaturas/atual")
        return response.get('dados', {})

    def extract_financial_counterparts(self, expenses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract unique financial counterparts (CNPJs) from expense records

        Args:
            expenses: List of expense records

        Returns:
            List of unique counterpart information
        """
        counterparts = {}

        for expense in expenses:
            cnpj_cpf = expense.get('cnpjCpfFornecedor')
            if not cnpj_cpf:
                continue

            # Clean CNPJ/CPF
            clean_id = re.sub(r'[^\d]', '', cnpj_cpf)
            if len(clean_id) not in [11, 14]:  # CPF or CNPJ
                continue

            if clean_id not in counterparts:
                counterparts[clean_id] = {
                    'cnpj_cpf': clean_id,
                    'name': expense.get('nomeFornecedor', ''),
                    'entity_type': 'COMPANY' if len(clean_id) == 14 else 'INDIVIDUAL',
                    'transaction_count': 0,
                    'total_amount': 0.0,
                    'first_transaction': None,
                    'last_transaction': None
                }

            # Update statistics
            counterpart = counterparts[clean_id]
            counterpart['transaction_count'] += 1
            counterpart['total_amount'] += float(expense.get('valorLiquido', 0))

            transaction_date = expense.get('dataDocumento')
            if transaction_date:
                if not counterpart['first_transaction'] or transaction_date < counterpart['first_transaction']:
                    counterpart['first_transaction'] = transaction_date
                if not counterpart['last_transaction'] or transaction_date > counterpart['last_transaction']:
                    counterpart['last_transaction'] = transaction_date

        return list(counterparts.values())

    def validate_cpf(self, cpf: str) -> bool:
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

    def normalize_name(self, name: str) -> str:
        """Normalize Brazilian names for matching"""
        if not name:
            return ""

        # Remove common titles and normalize
        name = name.upper()
        name = re.sub(r'\b(DR\.?|DRA\.?|PROF\.?|PROFA\.?|SR\.?|SRA\.?)\b', '', name)
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()

        return name