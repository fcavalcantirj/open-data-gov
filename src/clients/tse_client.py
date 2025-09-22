"""
TSE (Tribunal Superior Eleitoral) API Client
Implementation based on research of https://dadosabertos.tse.jus.br/

Provides access to Brazilian electoral data for political network correlation.
"""

import requests
import json
import csv
import io
import zipfile
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import re
from urllib.parse import urljoin
import time


class TSEClient:
    """
    Client for accessing TSE open data portal
    Based on CKAN API structure discovered at dadosabertos.tse.jus.br
    """

    def __init__(self):
        self.base_url = "https://dadosabertos.tse.jus.br/"
        self.api_base = "https://dadosabertos.tse.jus.br/api/3/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Brazilian-Political-Network-Analyzer/1.0'
        })
        # Cache for candidate data to avoid repeated downloads
        self._candidate_cache = {}

    def get_packages(self) -> List[str]:
        """Get list of all available packages/datasets"""
        url = urljoin(self.api_base, "action/package_list")
        response = self.session.get(url)
        response.raise_for_status()

        data = response.json()
        if data['success']:
            return data['result']
        else:
            raise Exception(f"Failed to get packages: {data}")

    def get_package_info(self, package_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific package"""
        url = urljoin(self.api_base, "action/package_show")
        params = {'id': package_id}

        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        if data['success']:
            return data['result']
        else:
            raise Exception(f"Failed to get package info for {package_id}: {data}")

    def search_candidates_packages(self, year: Optional[int] = None) -> List[str]:
        """Search for candidate-related packages"""
        packages = self.get_packages()

        candidate_packages = []
        for package in packages:
            if 'candidatos' in package.lower():
                if year is None or str(year) in package:
                    candidate_packages.append(package)

        return candidate_packages

    def search_finance_packages(self, year: Optional[int] = None) -> List[str]:
        """Search for campaign finance packages"""
        packages = self.get_packages()

        finance_packages = []
        search_terms = ['prestacao-contas', 'financiamento', 'doadores', 'receitas']

        for package in packages:
            if any(term in package.lower() for term in search_terms):
                if year is None or str(year) in package:
                    finance_packages.append(package)

        return finance_packages

    def get_candidate_data(self, year: int = 2022, state: Optional[str] = None) -> List[Dict]:
        """
        Get candidate data for a specific year
        This is the key function for correlating with Câmara deputies
        """
        # Check cache first
        cache_key = f"{year}_{state or 'ALL'}"
        if cache_key in self._candidate_cache:
            print(f"  ✓ Using cached TSE data for {year}")
            return self._candidate_cache[cache_key]

        print(f"=== TSE CANDIDATE DATA SEARCH ===")
        print(f"Year: {year}, State: {state or 'ALL'}")

        # Find candidate packages for the year
        candidate_packages = self.search_candidates_packages(year)

        if not candidate_packages:
            print(f"No candidate packages found for {year}")
            return []

        print(f"Found {len(candidate_packages)} candidate packages:")
        for pkg in candidate_packages[:5]:  # Show first 5
            print(f"  - {pkg}")

        # Get the main candidates package
        main_package = None
        for pkg in candidate_packages:
            if f'candidatos-{year}' == pkg:
                main_package = pkg
                break

        if not main_package:
            main_package = candidate_packages[0]  # Use first available

        print(f"Using package: {main_package}")

        # Get package details
        try:
            package_info = self.get_package_info(main_package)
            resources = package_info.get('resources', [])

            print(f"Package has {len(resources)} resources")

            # Look for CSV resources (candidate data)
            candidate_resources = []
            for resource in resources:
                if resource.get('format', '').lower() in ['csv', 'txt']:
                    name = resource.get('name', '')
                    if 'candidatos' in name.lower() or 'consulta_cand' in name.lower():
                        candidate_resources.append(resource)

            if not candidate_resources:
                print("No candidate CSV resources found")
                return []

            print(f"Found {len(candidate_resources)} candidate resources")

            # Download and parse candidate data
            all_candidates = []

            for resource in candidate_resources[:3]:  # Limit to first 3 resources
                try:
                    print(f"Downloading: {resource.get('name', 'Unknown')}")

                    # Handle different URL formats
                    download_url = resource.get('url')

                    # Fix malformed URLs with "URL: " prefix from TSE API
                    if download_url.startswith('URL: '):
                        download_url = download_url[5:]  # Remove "URL: " prefix

                    if not download_url.startswith('http'):
                        download_url = urljoin(self.base_url, download_url)

                    # Add retry logic for connection errors
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            response = self.session.get(download_url, timeout=60)
                            response.raise_for_status()
                            break
                        except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError,
                                requests.exceptions.HTTPError) as conn_err:
                            if retry < max_retries - 1:
                                wait_time = (retry + 1) * 10  # Longer delays: 10s, 20s, 30s
                                print(f"  ⚠️ Connection error (attempt {retry + 1}/{max_retries}), retrying in {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                print(f"  ❌ Failed after {max_retries} attempts: {conn_err}")
                                raise conn_err

                    # Handle ZIP files
                    if download_url.endswith('.zip'):
                        candidates = self._process_zip_candidate_data(response.content, state)
                    else:
                        candidates = self._process_csv_candidate_data(response.text, state)

                    all_candidates.extend(candidates)
                    print(f"  ✓ Extracted {len(candidates)} candidates")

                except Exception as e:
                    print(f"  ✗ Error processing resource: {e}")
                    print(f"     Resource URL: {download_url}")
                    print(f"     Resource name: {resource.get('name', 'Unknown')}")
                    continue

            print(f"Total candidates extracted: {len(all_candidates)}")

            # Cache the results
            cache_key = f"{year}_{state or 'ALL'}"
            self._candidate_cache[cache_key] = all_candidates
            print(f"  ✓ Cached {len(all_candidates)} candidates for future searches")

            return all_candidates

        except Exception as e:
            print(f"Error getting candidate data: {e}")
            # Return empty list but don't crash - let other years succeed
            return []

    def get_asset_data(self, year: int = 2022) -> List[Dict]:
        """Get asset data for a specific year"""
        # Check cache first
        cache_key = f"assets_{year}"
        if cache_key in self._candidate_cache:
            print(f"  ✓ Using cached TSE asset data for {year}")
            return self._candidate_cache[cache_key]

        print(f"=== TSE ASSET DATA SEARCH ===")
        print(f"Year: {year}")

        # Find candidate packages for the year
        candidate_packages = self.search_candidates_packages(year)

        if not candidate_packages:
            print(f"No candidate packages found for {year}")
            return []

        # Get the main candidates package
        main_package = None
        for pkg in candidate_packages:
            if f'candidatos-{year}' == pkg:
                main_package = pkg
                break

        if not main_package:
            print("No main candidate package found")
            return []

        print(f"Using package: {main_package}")

        # Get package details
        try:
            package_info = self.get_package_info(main_package)
            resources = package_info.get('resources', [])

            # Look for asset resources (Bens de candidatos)
            asset_resources = []
            print(f"DEBUG: Searching for asset resources in {len(resources)} total resources")
            for resource in resources:
                name = resource.get('name', '')
                format_type = resource.get('format', '').lower()
                print(f"DEBUG: Resource '{name}' (format: {format_type})")

                if format_type in ['csv', 'txt']:
                    # Try multiple patterns for asset resources
                    name_lower = name.lower()
                    if ('bens' in name_lower) or ('asset' in name_lower) or ('patrimonio' in name_lower):
                        asset_resources.append(resource)
                        print(f"DEBUG: Added asset resource: {name}")

            if not asset_resources:
                print("No asset CSV resources found")
                print("DEBUG: Available CSV/TXT resources:")
                for resource in resources:
                    if resource.get('format', '').lower() in ['csv', 'txt']:
                        print(f"  - {resource.get('name', 'Unknown')}")
                return []

            print(f"Found {len(asset_resources)} asset resources")

            # Download and parse asset data
            all_assets = []

            for resource in asset_resources:
                try:
                    print(f"Downloading: {resource.get('name', 'Unknown')}")

                    # Handle different URL formats
                    download_url = resource.get('url')

                    # Fix malformed URLs with "URL: " prefix from TSE API
                    if download_url.startswith('URL: '):
                        download_url = download_url[5:]  # Remove "URL: " prefix

                    if not download_url.startswith('http'):
                        download_url = urljoin(self.base_url, download_url)

                    # Add retry logic for connection errors
                    max_retries = 3
                    for retry in range(max_retries):
                        try:
                            response = self.session.get(download_url, timeout=60)
                            response.raise_for_status()
                            break
                        except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError,
                                requests.exceptions.HTTPError) as conn_err:
                            if retry < max_retries - 1:
                                wait_time = (retry + 1) * 10  # Longer delays: 10s, 20s, 30s
                                print(f"  ⚠️ Connection error (attempt {retry + 1}/{max_retries}), retrying in {wait_time}s...")
                                time.sleep(wait_time)
                            else:
                                print(f"  ❌ Failed after {max_retries} attempts: {conn_err}")
                                raise conn_err

                    # Handle ZIP files and CSV files
                    if download_url.endswith('.zip'):
                        assets = self._process_zip_asset_data(response.content)
                    else:
                        assets = self._process_csv_asset_data(response.text)

                    all_assets.extend(assets)
                    print(f"  ✓ Extracted {len(assets)} assets")

                except Exception as e:
                    print(f"  ✗ Error processing resource: {e}")
                    print(f"     Resource URL: {download_url}")
                    print(f"     Resource name: {resource.get('name', 'Unknown')}")
                    continue

            print(f"Total assets extracted: {len(all_assets)}")

            # Cache the results
            cache_key = f"assets_{year}"
            self._candidate_cache[cache_key] = all_assets
            print(f"  ✓ Cached {len(all_assets)} assets for future searches")

            return all_assets

        except Exception as e:
            print(f"Error getting package info: {e}")
            return []

    def _process_zip_candidate_data(self, zip_content: bytes, state_filter: Optional[str] = None) -> List[Dict]:
        """Process ZIP file containing candidate CSV data"""
        candidates = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                for file_name in zip_file.namelist():
                    if file_name.endswith('.csv') or file_name.endswith('.txt'):
                        if 'candidatos' in file_name.lower() or 'consulta_cand' in file_name.lower():
                            with zip_file.open(file_name) as csv_file:
                                content = csv_file.read().decode('utf-8', errors='ignore')
                                file_candidates = self._process_csv_candidate_data(content, state_filter)
                                candidates.extend(file_candidates)
        except Exception as e:
            print(f"Error processing ZIP: {e}")

        return candidates

    def _process_csv_candidate_data(self, csv_content: str, state_filter: Optional[str] = None) -> List[Dict]:
        """Process CSV candidate data"""
        candidates = []

        try:
            # Try different delimiters
            for delimiter in [';', ',', '\t']:
                try:
                    csv_file = io.StringIO(csv_content)
                    reader = csv.DictReader(csv_file, delimiter=delimiter)

                    sample_row = next(reader, None)
                    if sample_row and len(sample_row) > 5:  # Good delimiter found
                        csv_file.seek(0)
                        reader = csv.DictReader(csv_file, delimiter=delimiter)

                        for row in reader:
                            candidate = self._normalize_candidate_data(row)
                            if candidate:
                                # Filter by state if specified
                                if state_filter is None or candidate.get('state') == state_filter:
                                    candidates.append(candidate)
                        break

                except Exception:
                    continue

        except Exception as e:
            print(f"Error processing CSV: {e}")

        return candidates

    def _process_csv_asset_data(self, csv_content: str) -> List[Dict]:
        """Process CSV asset data"""
        assets = []

        try:
            # Try different delimiters
            for delimiter in [';', ',', '\t']:
                try:
                    csv_file = io.StringIO(csv_content)
                    reader = csv.DictReader(csv_file, delimiter=delimiter)

                    sample_row = next(reader, None)
                    if sample_row and len(sample_row) > 3:  # Good delimiter found
                        csv_file.seek(0)
                        reader = csv.DictReader(csv_file, delimiter=delimiter)

                        for row in reader:
                            # Just return raw asset data - no normalization needed for now
                            if row:
                                assets.append(row)
                        break

                except Exception:
                    continue

        except Exception as e:
            print(f"Error processing asset CSV: {e}")

        return assets

    def _process_zip_asset_data(self, zip_content: bytes) -> List[Dict]:
        """Process ZIP file containing asset CSV data"""
        assets = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                for file_name in zip_file.namelist():
                    if file_name.endswith('.csv') or file_name.endswith('.txt'):
                        with zip_file.open(file_name) as csv_file:
                            csv_content = csv_file.read().decode('utf-8', errors='ignore')
                            file_assets = self._process_csv_asset_data(csv_content)
                            assets.extend(file_assets)

        except Exception as e:
            print(f"Error processing ZIP: {e}")

        return assets

    def _normalize_candidate_data(self, raw_row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Normalize candidate data to standard format"""
        if not raw_row:
            return None

        # Common field mappings for TSE data
        field_mappings = {
            'name': ['NM_CANDIDATO', 'NOME_CANDIDATO', 'nome', 'name'],
            'cpf': ['NR_CPF_CANDIDATO', 'CPF_CANDIDATO', 'cpf'],
            'electoral_number': ['NR_CANDIDATO', 'NUMERO_CANDIDATO', 'numero'],
            'party': ['SG_PARTIDO', 'SIGLA_PARTIDO', 'partido'],
            'state': ['SG_UF', 'UF', 'estado'],
            'position': ['DS_CARGO', 'CARGO', 'cargo'],
            'election_year': ['ANO_ELEICAO', 'ano', 'year'],
            'status': ['DS_SITUACAO_CANDIDATURA', 'situacao'],
            'coalition': ['NM_COLIGACAO', 'coligacao']
        }

        candidate = {}

        # First, preserve ALL original TSE fields
        for original_field, value in raw_row.items():
            if value and value.strip():
                candidate[original_field.lower()] = value.strip()

        # Then add normalized fields for convenience
        for standard_field, possible_fields in field_mappings.items():
            value = None
            for field in possible_fields:
                if field in raw_row and raw_row[field]:
                    value = raw_row[field].strip()
                    break

            candidate[standard_field] = value

        # Validate essential fields
        if not candidate.get('name'):
            return None

        # Clean and validate CPF
        if candidate.get('cpf'):
            cpf_clean = re.sub(r'[^\d]', '', candidate['cpf'])
            candidate['cpf'] = cpf_clean if len(cpf_clean) == 11 else None

        # Normalize name
        if candidate.get('name'):
            candidate['name_normalized'] = self._normalize_name(candidate['name'])

        return candidate

    def _normalize_name(self, name: str) -> str:
        """Normalize Brazilian candidate names for matching"""
        if not name:
            return ""

        name = name.upper()
        # Remove common titles
        name = re.sub(r'\b(DR\.?|DRA\.?|PROF\.?|DEPUTADO|DEPUTADA)\b', '', name)
        # Remove special characters
        name = re.sub(r'[^\w\s]', '', name)
        # Normalize whitespace
        name = re.sub(r'\s+', ' ', name).strip()

        return name

    def find_candidate_by_name(self, search_name: str, year: int = 2022, position: str = 'DEPUTADO FEDERAL') -> List[Dict]:
        """
        Find candidates by name - key function for correlation with Câmara deputies
        """
        print(f"\n=== TSE NAME SEARCH ===")
        print(f"Searching for: {search_name}")
        print(f"Year: {year}, Position: {position}")

        candidates = self.get_candidate_data(year)

        if not candidates:
            print("No candidate data available")
            return []

        # Normalize search name
        search_normalized = self._normalize_name(search_name)

        matches = []

        for candidate in candidates:
            # Filter by position if specified
            if position and candidate.get('position'):
                if position.upper() not in candidate['position'].upper():
                    continue

            # Name matching
            candidate_name = candidate.get('name_normalized', '')
            if candidate_name and search_normalized:
                # Exact match
                if search_normalized == candidate_name:
                    matches.append({**candidate, 'match_type': 'exact'})
                # Partial match (contains all words)
                elif all(word in candidate_name for word in search_normalized.split()):
                    matches.append({**candidate, 'match_type': 'partial'})

        print(f"Found {len(matches)} matches")

        for match in matches:
            print(f"  {match['match_type']}: {match.get('name')} - {match.get('party')} - {match.get('state')}")

        return matches

    def get_deputy_electoral_history(self, deputy_name: str, deputy_state: str) -> Dict[str, Any]:
        """
        Get complete electoral history for a deputy - implements correlation strategy
        """
        print(f"\n=== DEPUTY ELECTORAL HISTORY ===")
        print(f"Deputy: {deputy_name} ({deputy_state})")

        history = {
            'deputy_name': deputy_name,
            'deputy_state': deputy_state,
            'elections': {},
            'correlation_confidence': 0.0
        }

        # Search recent elections
        election_years = [2022, 2018, 2014, 2010]

        for year in election_years:
            try:
                matches = self.find_candidate_by_name(deputy_name, year, 'DEPUTADO FEDERAL')

                # Filter by state
                state_matches = [m for m in matches if m.get('state') == deputy_state]

                if state_matches:
                    # Take best match (exact over partial)
                    best_match = None
                    for match in state_matches:
                        if match['match_type'] == 'exact':
                            best_match = match
                            break

                    if not best_match:
                        best_match = state_matches[0]

                    history['elections'][year] = {
                        'candidate_data': best_match,
                        'electoral_number': best_match.get('electoral_number'),
                        'party': best_match.get('party'),
                        'cpf': best_match.get('cpf')
                    }

                    print(f"  {year}: ✓ Found - {best_match.get('party')} - #{best_match.get('electoral_number')}")

                else:
                    print(f"  {year}: ✗ Not found")

            except Exception as e:
                print(f"  {year}: ✗ Error - {e}")

        # Calculate correlation confidence
        elections_found = len(history['elections'])
        if elections_found >= 2:
            history['correlation_confidence'] = min(elections_found / 4.0, 1.0)

        print(f"Electoral history confidence: {history['correlation_confidence']:.2f}")

        return history


def test_tse_integration():
    """Test TSE integration with Arthur Lira as specified in the architecture"""
    print("🗳️ TSE INTEGRATION TEST")
    print("=" * 50)

    client = TSEClient()

    # Test with Arthur Lira (from our Câmara discovery)
    arthur_history = client.get_deputy_electoral_history("Arthur Lira", "AL")

    return arthur_history


if __name__ == "__main__":
    # Run the test
    result = test_tse_integration()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"tse_integration_test_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Results saved to: tse_integration_test_{timestamp}.json")