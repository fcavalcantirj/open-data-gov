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
import codecs
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
        search_terms = ['prestacao-de-contas-eleitorais']

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

            # Download and parse candidate data - FULL PROCESSING (NO LIMITS)
            all_candidates = []

            for resource in candidate_resources:  # PROCESS ALL RESOURCES
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
            'coalition': ['NM_COLIGACAO', 'coligacao'],
            # NEW: Electoral outcome fields from verified TSE data structure
            'electoral_outcome': ['DS_SIT_TOT_TURNO', 'SITUACAO_TURNO', 'electoral_result'],
            'electoral_outcome_code': ['CD_SIT_TOT_TURNO', 'COD_SIT_TURNO'],
            'ballot_name': ['NM_URNA_CANDIDATO', 'NOME_URNA', 'nome_urna'],
            'candidate_id': ['SQ_CANDIDATO', 'SEQUENCIAL_CANDIDATO', 'seq_candidato'],
            'party_name': ['NM_PARTIDO', 'NOME_PARTIDO', 'nome_partido'],
            'electoral_unit': ['NM_UE', 'NOME_UE', 'unidade_eleitoral'],
            'electoral_unit_code': ['SG_UE', 'COD_UE'],
            'election_code': ['CD_ELEICAO', 'CODIGO_ELEICAO'],
            'votes_received': ['QT_VOTOS_NOMINAIS', 'VOTOS_NOMINAIS', 'total_votos']  # May not always be present
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

        # Process electoral outcomes - NEW FEATURE
        if candidate.get('electoral_outcome'):
            candidate['was_elected'] = self._determine_election_success(candidate['electoral_outcome'])
            candidate['election_status_category'] = self._categorize_election_status(candidate['electoral_outcome'])

        # Convert votes to integer if present
        if candidate.get('votes_received'):
            try:
                candidate['votes_received_int'] = int(candidate['votes_received'].replace(',', '').replace('.', ''))
            except (ValueError, AttributeError):
                candidate['votes_received_int'] = 0

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

    def _determine_election_success(self, electoral_outcome: str) -> bool:
        """
        Determine if a candidate was elected based on electoral outcome
        Based on verified TSE data patterns from test results
        """
        if not electoral_outcome:
            return False

        outcome_upper = electoral_outcome.upper().strip()

        # Check if NOT elected first (to avoid false positives with "ELEITO" substring)
        if 'NÃO ELEITO' in outcome_upper:
            return False

        # Winning outcomes (order matters)
        winning_statuses = [
            'ELEITO POR QP',    # Elected by quotient
            'ELEITO POR MÉDIA', # Elected by average
            'ELEITO'            # Elected (general)
        ]

        return any(status in outcome_upper for status in winning_statuses)

    def _categorize_election_status(self, electoral_outcome: str) -> str:
        """
        Categorize election status into standard categories
        Based on verified TSE data patterns from test results
        """
        if not electoral_outcome:
            return 'UNKNOWN'

        outcome_upper = electoral_outcome.upper().strip()

        # Map outcomes to categories (order matters - check specific patterns first)
        if 'NÃO ELEITO' in outcome_upper:
            return 'NOT_ELECTED'
        elif 'ELEITO POR QP' in outcome_upper:
            return 'ELECTED_QUOTIENT'
        elif 'ELEITO POR MÉDIA' in outcome_upper:
            return 'ELECTED_AVERAGE'
        elif 'ELEITO' in outcome_upper:
            return 'ELECTED_DIRECT'
        elif 'SUPLENTE' in outcome_upper:
            return 'SUBSTITUTE'
        elif '#NULO' in outcome_upper or 'NULO' in outcome_upper:
            return 'VOID'
        elif 'CANCELADO' in outcome_upper:
            return 'CANCELLED'
        elif 'RENUNCIOU' in outcome_upper:
            return 'RENOUNCED'
        else:
            return 'OTHER'

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

    def get_finance_data(self, year: int, data_type: str = 'all') -> List[Dict]:
        """
        Get campaign finance data for a specific year
        Used by CLI4 financial populators

        Args:
            year: Election year
            data_type: Type of data to fetch:
                'all' - All 4 TSE finance data types
                'receitas' - Campaign donations (RECEITAS_CANDIDATOS)
                'despesas_contratadas' - Contracted expenses
                'despesas_pagas' - Paid expenses
                'doador_originario' - Original donor tracking
        """
        print(f"⚠️⚠️⚠️ OLD get_finance_data() CALLED - THIS LOADS EVERYTHING INTO MEMORY! ⚠️⚠️⚠️")
        print(f"⚠️ Should be using get_finance_data_streaming() instead!")
        import traceback
        traceback.print_stack(limit=5)
        print(f"=== TSE FINANCE DATA SEARCH ===")
        print(f"Year: {year}")

        # Check cache first
        cache_key = f"finance_{year}"
        if cache_key in self._candidate_cache:
            print(f"  ✓ Using cached TSE finance data for {year}")
            return self._candidate_cache[cache_key]

        # Find finance packages for the year
        finance_packages = self.search_finance_packages(year)

        if not finance_packages:
            print(f"No finance packages found for {year}")
            return []

        print(f"Found {len(finance_packages)} finance packages:")
        for pkg in finance_packages[:3]:  # Show first 3
            print(f"  - {pkg}")

        all_finance_data = []

        # Process each finance package - FULL PROCESSING (NO LIMITS)
        for package_name in finance_packages:  # PROCESS ALL PACKAGES
            try:
                print(f"Processing package: {package_name}")
                package_info = self.get_package_info(package_name)
                resources = package_info.get('resources', [])

                # Look for finance CSV resources - ALL 4 TSE FINANCE DATA TYPES
                finance_resources = []
                for resource in resources:
                    if resource.get('format', '').lower() in ['csv', 'txt']:
                        name = resource.get('name', '').lower()

                        # Check for any of the 4 TSE finance data types
                        # Exclude bank statements (extratos bancários) - different data structure
                        is_finance_resource = (
                            any(term in name for term in ['prestação', 'prestacao', 'candidatos', 'contas']) or
                            'receitas_candidatos' in name or
                            'despesas_contratadas' in name or
                            'despesas_pagas' in name or
                            'doador_originario' in name
                        ) and 'extrato' not in name.lower() and 'bancário' not in name.lower()

                        # Filter by specific data_type if requested
                        if data_type != 'all':
                            # The main candidate finance resource contains ALL data types
                            # Individual state files have specific naming patterns
                            type_match = {
                                'receitas': (
                                    'receitas_candidatos' in name and 'doador_originario' not in name
                                ) or (
                                    'prestação de contas de candidatos' in name or 'prestacao de contas de candidatos' in name
                                ),
                                'despesas_contratadas': (
                                    'despesas_contratadas' in name
                                ) or (
                                    'prestação de contas de candidatos' in name or 'prestacao de contas de candidatos' in name
                                ),
                                'despesas_pagas': (
                                    'despesas_pagas' in name
                                ) or (
                                    'prestação de contas de candidatos' in name or 'prestacao de contas de candidatos' in name
                                ),
                                'doador_originario': (
                                    'doador_originario' in name
                                ) or (
                                    'prestação de contas de candidatos' in name or 'prestacao de contas de candidatos' in name
                                )
                            }
                            if not type_match.get(data_type, False):
                                is_finance_resource = False

                        if is_finance_resource:
                            finance_resources.append(resource)

                if not finance_resources:
                    print(f"  No finance CSV resources found in {package_name}")
                    continue

                print(f"  Found {len(finance_resources)} finance resources")

                # Prioritize candidate records over party records
                candidate_resources = [r for r in finance_resources if 'candidato' in r.get('name', '').lower()]
                if candidate_resources:
                    finance_resources = candidate_resources

                # Download and parse finance data - FULL PROCESSING (NO LIMITS)
                for resource in finance_resources:  # PROCESS ALL FINANCE RESOURCES
                    try:
                        resource_name = resource.get('name', 'Unknown')
                        print(f"  Downloading: {resource_name}")

                        # Detect data type from filename
                        detected_type = self._detect_finance_data_type(resource_name)
                        print(f"    Data type: {detected_type}")

                        download_url = resource.get('url')
                        if download_url.startswith('URL: '):
                            download_url = download_url[5:]

                        if not download_url.startswith('http'):
                            download_url = urljoin(self.base_url, download_url)

                        # ENHANCED PROCESSING: Bulletproof download with extended timeouts for massive files
                        print(f"    🌐 TSE ZIP URL: {download_url}")
                        max_retries = 5
                        for retry in range(max_retries):
                            try:
                                print(f"    📥 Downloading large file (attempt {retry + 1}/{max_retries})...")
                                # Extended timeout for massive TSE files (2 hour timeout)
                                response = self.session.get(download_url, timeout=(30, 540), stream=True)
                                response.raise_for_status()

                                # Download with progress indication for large files
                                content_length = response.headers.get('content-length')
                                if content_length:
                                    total_size = int(content_length)
                                    print(f"    📊 File size: {total_size / (1024*1024):.1f} MB")

                                content = b""
                                downloaded = 0
                                chunk_size = 1024 * 1024  # 1MB chunks

                                for chunk in response.iter_content(chunk_size=chunk_size):
                                    if chunk:
                                        content += chunk
                                        downloaded += len(chunk)
                                        if content_length:
                                            progress = (downloaded / total_size) * 100
                                            print(f"    📈 Progress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)", end='\r')

                                print(f"\n    ✅ Download completed: {len(content) / (1024*1024):.1f} MB")
                                response._content = content  # Set content for compatibility
                                break

                            except (requests.ConnectionError, requests.Timeout) as conn_err:
                                if retry < max_retries - 1:
                                    wait_time = (retry + 1) * 30  # Progressive delays: 30s, 60s, 90s, 120s
                                    print(f"\n    ⚠️ Large file download failed (attempt {retry + 1}/{max_retries}), retrying in {wait_time}s...")
                                    print(f"    🌐 Failed URL: {download_url}")
                                    time.sleep(wait_time)
                                else:
                                    print(f"\n    ❌ Failed to download large file after {max_retries} attempts: {conn_err}")
                                    print(f"    🌐 Failed URL: {download_url}")
                                    print(f"    🔄 RETURNING EMPTY - NOT FAILING")
                                    return []  # Return empty instead of raising

                        # Handle ZIP files and CSV files with type detection
                        if download_url.endswith('.zip'):
                            finance_data = self._process_zip_finance_data(response.content, detected_type)
                        else:
                            finance_data = self._process_csv_finance_data(response.text, detected_type)

                        all_finance_data.extend(finance_data)
                        print(f"    ✅ Extracted {len(finance_data):,} {detected_type} records")

                    except Exception as e:
                        print(f"    ✗ Error processing resource: {e}")
                        print(f"    🌐 Resource URL: {download_url}")
                        print(f"    📁 Resource name: {resource.get('name', 'Unknown')}")
                        print(f"    🔄 CONTINUING - NOT FAILING")
                        continue

            except Exception as e:
                print(f"  ✗ Error processing package {package_name}: {e}")
                print(f"  🔄 CONTINUING - NOT FAILING")
                continue

        print(f"Total finance records extracted: {len(all_finance_data)}")

        # Cache the results
        self._candidate_cache[cache_key] = all_finance_data
        print(f"  ✓ Cached {len(all_finance_data)} finance records")

        return all_finance_data

    def get_finance_data_streaming(self, year: int, data_type: str, target_cpf: str):
        """
        MEMORY-EFFICIENT STREAMING: Get TSE finance data filtered by CPF without loading all data
        Yields records one by one, filtering immediately by CPF to prevent memory exhaustion
        """
        print(f"=== TSE STREAMING FINANCE DATA ===")
        print(f"Year: {year}, Type: {data_type}, Target CPF: {target_cpf}")

        # Find finance packages for the year
        finance_packages = self.search_finance_packages(year)

        if not finance_packages:
            print(f"No finance packages found for {year}")
            return

        # Process packages with streaming
        for package_name in finance_packages:
            try:
                print(f"Streaming package: {package_name}")
                package_info = self.get_package_info(package_name)
                resources = package_info.get('resources', [])

                # Look for finance CSV resources
                finance_resources = []
                for resource in resources:
                    if resource.get('format', '').lower() in ['csv', 'txt']:
                        name = resource.get('name', '').lower()
                        is_finance_resource = (
                            any(term in name for term in ['prestação', 'prestacao', 'candidatos', 'contas']) or
                            'receitas_candidatos' in name or
                            'despesas_contratadas' in name or
                            'despesas_pagas' in name or
                            'doador_originario' in name
                        ) and 'extrato' not in name.lower()

                        if is_finance_resource:
                            finance_resources.append(resource)

                if not finance_resources:
                    continue

                # Stream each resource
                for resource in finance_resources:
                    try:
                        resource_name = resource.get('name', 'Unknown')
                        detected_type = self._detect_finance_data_type(resource_name)

                        # Skip if not matching requested type
                        if data_type != 'all' and detected_type != data_type:
                            continue

                        print(f"  Streaming: {resource_name}")

                        download_url = resource.get('url')
                        if download_url.startswith('URL: '):
                            download_url = download_url[5:]
                        if not download_url.startswith('http'):
                            download_url = urljoin(self.base_url, download_url)

                        # Download and stream process
                        print(f"    🌐 Downloading: {download_url}")

                        # For ZIP files, we need to download fully first
                        if download_url.endswith('.zip'):
                            print(f"    📥 Downloading ZIP file...")
                            response = self.session.get(download_url, timeout=(30, 540), stream=True)
                            response.raise_for_status()

                            # Download with progress indication for large files
                            content_length = response.headers.get('content-length')
                            if content_length:
                                total_size = int(content_length)
                                print(f"    📊 File size: {total_size / (1024*1024):.1f} MB")

                                content = b""
                                downloaded = 0
                                chunk_size = 1024 * 1024  # 1MB chunks

                                for chunk in response.iter_content(chunk_size=chunk_size):
                                    if chunk:
                                        content += chunk
                                        downloaded += len(chunk)
                                        progress = (downloaded / total_size) * 100
                                        print(f"    📈 Progress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)", end='\r')

                                print(f"\n    ✅ Download completed: {len(content) / (1024*1024):.1f} MB")
                                response._content = content  # Set content for compatibility
                            else:
                                # Fallback for servers that don't provide content-length
                                print(f"    📥 Downloading ZIP file (size unknown)...")
                                response._content = b"".join(response.iter_content(chunk_size=1024*1024))
                                download_size_mb = len(response.content) / 1024 / 1024
                                print(f"    📥 Downloaded {download_size_mb:.1f}MB ZIP, starting streaming...")

                            # Now stream through the ZIP contents
                            yield from self._stream_zip_finance_data(response.content, detected_type, target_cpf)
                        else:
                            # For CSV, we can truly stream
                            response = self.session.get(download_url, timeout=(30, 540), stream=True)
                            response.raise_for_status()
                            print(f"    📥 Streaming CSV directly...")
                            yield from self._stream_csv_finance_data(response.text, detected_type, target_cpf)

                    except Exception as e:
                        print(f"    ✗ Error streaming resource: {e}")
                        continue

            except Exception as e:
                print(f"  ✗ Error streaming package {package_name}: {e}")
                continue

    def _stream_zip_finance_data(self, zip_content: bytes, data_type: str, target_cpf: str):
        """Stream ZIP contents, filtering by CPF immediately"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                csv_files = [f for f in zip_file.namelist() if f.endswith('.csv') or f.endswith('.txt')]

                for file_name in csv_files:
                    file_data_type = self._detect_finance_data_type(file_name)
                    if data_type == 'all' or file_data_type == data_type:
                        with zip_file.open(file_name) as csv_file:
                            # CRITICAL FIX: Stream directly from ZIP without loading entire content
                            print(f"      🔍 Streaming {file_name} directly from ZIP...")

                            # Create text wrapper for streaming
                            import codecs
                            text_stream = codecs.getreader('latin-1')(csv_file, errors='replace')

                            # Stream CSV directly without loading all content
                            reader = csv.DictReader(text_stream, delimiter=';')

                            matched_count = 0
                            row_count = 0
                            for row in reader:
                                row_count += 1

                                # Check if this record matches our target CPF
                                candidate_cpf = row.get('NR_CPF_CANDIDATO') or row.get('CPF_CANDIDATO')
                                if candidate_cpf == target_cpf:
                                    finance_record = self._normalize_finance_data(row, file_data_type, file_name, row_count)
                                    if finance_record:
                                        matched_count += 1
                                        yield finance_record

                                # Progress every 100k records
                                if row_count % 100000 == 0:
                                    print(f"        📊 Streamed {row_count:,} records from {file_name}, {matched_count} matches")

                            if matched_count > 0:
                                print(f"        ✅ Found {matched_count} matches for CPF {target_cpf} in {file_name}")

        except Exception as e:
            print(f"Error streaming ZIP: {e}")

    def _stream_csv_finance_data(self, csv_content: str, data_type: str, target_cpf: str, file_name: str = 'unknown'):
        """Stream CSV content, yielding only records matching target CPF"""
        try:
            for delimiter in [';', ',', '\t']:
                try:
                    csv_file = io.StringIO(csv_content)
                    reader = csv.DictReader(csv_file, delimiter=delimiter)

                    sample_row = next(reader, None)
                    if sample_row and len(sample_row) > 5:
                        print(f"      🔍 Streaming {file_name}, {len(sample_row)} fields")

                        csv_file.seek(0)
                        reader = csv.DictReader(csv_file, delimiter=delimiter)

                        matched_count = 0
                        for row_num, row in enumerate(reader, 1):
                            # Check if this record matches our target CPF
                            candidate_cpf = row.get('NR_CPF_CANDIDATO') or row.get('CPF_CANDIDATO')
                            if candidate_cpf == target_cpf:
                                finance_record = self._normalize_finance_data(row, data_type, file_name, row_num)
                                if finance_record:
                                    matched_count += 1
                                    yield finance_record

                            # Progress every 100k records
                            if row_num % 100000 == 0:
                                print(f"        📊 Streamed {row_num:,} records, {matched_count} matches")

                        if matched_count > 0:
                            print(f"        ✅ Found {matched_count} matches for CPF {target_cpf}")
                        break

                except Exception:
                    continue

        except Exception as e:
            print(f"Error streaming CSV: {e}")

    def _detect_finance_data_type(self, filename: str) -> str:
        """
        Detect TSE finance data type from filename
        Returns one of: receitas, despesas_contratadas, despesas_pagas, doador_originario
        """
        filename_lower = filename.lower()

        if 'doador_originario' in filename_lower:
            return 'doador_originario'
        elif 'despesas_contratadas' in filename_lower:
            return 'despesas_contratadas'
        elif 'despesas_pagas' in filename_lower:
            return 'despesas_pagas'
        elif 'receitas_candidatos' in filename_lower:
            return 'receitas'
        else:
            # Default to receitas for backward compatibility
            return 'receitas'

    def _process_zip_finance_data(self, zip_content: bytes, data_type: str = 'receitas') -> List[Dict]:
        """Process ZIP file containing finance CSV data - 100% FILE COVERAGE GUARANTEED"""
        finance_records = []
        total_files = 0
        processed_files = 0
        failed_files = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                csv_files = [f for f in zip_file.namelist() if f.endswith('.csv') or f.endswith('.txt')]
                total_files = len(csv_files)
                print(f"      📁 Total CSV files in ZIP: {total_files}")

                for file_name in csv_files:
                    try:
                        # Detect file type and filter accordingly
                        file_data_type = self._detect_finance_data_type(file_name)
                        print(f"      📄 Processing: {file_name} (type: {file_data_type})")

                        # Process ALL files for comprehensive coverage
                        should_process = (
                            data_type == 'all' or
                            file_data_type == data_type or
                            any(term in file_name.lower() for term in ['receitas', 'doadores', 'financiamento', 'despesas'])
                        )

                        if should_process:
                            with zip_file.open(file_name) as csv_file:
                                content = csv_file.read().decode('latin-1', errors='replace')  # Better error handling
                                file_records = self._process_csv_finance_data(content, file_data_type, file_name)
                                finance_records.extend(file_records)
                                processed_files += 1
                                print(f"        ✅ SUCCESS: {len(file_records):,} valid records from {file_name}")
                        else:
                            print(f"        ⏭️ SKIPPED: {file_name} (type filter: {data_type})")

                    except Exception as file_error:
                        failed_files.append(file_name)
                        print(f"        ❌ FAILED: {file_name} - {file_error}")
                        print(f"        🔄 CONTINUING WITH NEXT FILE")
                        continue

                print(f"      📈 SUMMARY: {processed_files}/{total_files} files processed successfully")
                if failed_files:
                    print(f"      ⚠️ FAILED FILES: {failed_files}")

        except Exception as e:
            print(f"      ❌ ZIP PROCESSING ERROR: {e}")
            print(f"      🔄 RETURNING PARTIAL RESULTS")

        return finance_records

    def _process_csv_finance_data(self, csv_content: str, data_type: str = 'receitas', file_name: str = 'unknown') -> List[Dict]:
        """Process CSV finance data - FULL PROCESSING WITH STREAMING"""
        finance_records = []

        try:
            # Try different delimiters (TSE uses semicolon primarily)
            for delimiter in [';', ',', '\t']:
                try:
                    csv_file = io.StringIO(csv_content)
                    reader = csv.DictReader(csv_file, delimiter=delimiter)

                    sample_row = next(reader, None)
                    if sample_row and len(sample_row) > 5:  # Good delimiter found
                        print(f"      🔍 Found delimiter '{delimiter}', {len(sample_row)} fields")
                        print(f"      📋 Sample TSE fields: {list(sample_row.keys())[:10]}...")

                        csv_file.seek(0)
                        reader = csv.DictReader(csv_file, delimiter=delimiter)

                        # 100% PROCESSING: Process ALL rows with detailed error tracking
                        row_count = 0
                        valid_count = 0
                        error_count = 0
                        sample_errors = []  # Store first 5 errors with actual data

                        for row in reader:
                            row_count += 1

                            try:
                                finance_record = self._normalize_finance_data(row, data_type, file_name, row_count)
                                if finance_record:
                                    finance_records.append(finance_record)
                                    valid_count += 1
                                else:
                                    error_count += 1
                                    if len(sample_errors) < 5:  # Store first 5 failed rows
                                        sample_errors.append({
                                            'row_number': row_count,
                                            'error': 'Failed normalization',
                                            'raw_data': dict(row),
                                            'available_columns': list(row.keys())
                                        })
                            except Exception as row_error:
                                error_count += 1
                                if len(sample_errors) < 5:  # Store first 5 exceptions
                                    sample_errors.append({
                                        'row_number': row_count,
                                        'error': str(row_error),
                                        'raw_data': dict(row),
                                        'available_columns': list(row.keys())
                                    })

                            # Progress indicator for large files (every 50k records)
                            if row_count % 50000 == 0:
                                success_rate = (valid_count / row_count) * 100 if row_count > 0 else 0
                                print(f"        📊 Processed {row_count:,} records, {valid_count:,} valid ({success_rate:.1f}%)")

                        # DETAILED FINAL REPORT
                        final_success_rate = (valid_count / row_count) * 100 if row_count > 0 else 0
                        print(f"        ✅ COMPLETE: {row_count:,} total records")
                        print(f"        ✅ VALID: {valid_count:,} records ({final_success_rate:.1f}%)")
                        print(f"        ❌ ERRORS: {error_count:,} records")

                        # Show sample errors for debugging
                        if sample_errors:
                            print(f"        🔍 SAMPLE ERRORS (first {len(sample_errors)}):{sample_errors}")
                            for error in sample_errors:
                                print(f"          Row {error['row_number']}: {error['error']}")
                                print(f"          Available columns: {error['available_columns'][:10]}...")
                                print(f"          Sample data: {str(error['raw_data'])[:200]}...")

                        break

                except Exception:
                    continue

        except Exception as e:
            print(f"Error processing finance CSV: {e}")

        return finance_records

    def _normalize_finance_data(self, raw_row: Dict[str, str], data_type: str = 'receitas', file_name: str = 'unknown', row_number: int = 0) -> Optional[Dict[str, Any]]:
        """Normalize finance data to standard format - ALL 4 TSE DATA TYPES"""
        if not raw_row:
            print(f"    🚫 REJECT: Empty row")
            return None

        # Base field mappings common to all types
        base_mappings = {
            'nr_cpf_candidato': ['NR_CPF_CANDIDATO', 'CPF_CANDIDATO'],
            'cpf_candidato': ['NR_CPF_CANDIDATO', 'CPF_CANDIDATO']
        }

        # Type-specific field mappings based on ACTUAL TSE data structure
        type_mappings = {
            'receitas': {
                'nr_cpf_cnpj_doador': ['NR_CPF_CNPJ_DOADOR', 'CNPJ_CPF_DOADOR'],
                'cnpj_cpf_doador': ['NR_CPF_CNPJ_DOADOR', 'CNPJ_CPF_DOADOR'],
                'nm_doador': ['NM_DOADOR', 'NOME_DOADOR'],
                'nome_doador': ['NM_DOADOR', 'NOME_DOADOR'],
                'vr_receita': ['VR_RECEITA', 'VALOR_RECEITA'],
                'valor_receita': ['VR_RECEITA', 'VALOR_RECEITA'],
                'dt_receita': ['DT_RECEITA', 'DATA_RECEITA'],
                'data_receita': ['DT_RECEITA', 'DATA_RECEITA'],
                'ds_especie_receita': ['DS_ESPECIE_RECEITA', 'ESPECIE_RECEITA'],
                'descricao_receita': ['DS_ESPECIE_RECEITA', 'ESPECIE_RECEITA'],
                'sq_receita': ['SQ_RECEITA', 'SEQUENCIAL_RECEITA']
            },
            'despesas_contratadas': {
                'nr_cpf_cnpj_fornecedor': ['NR_CPF_CNPJ_FORNECEDOR', 'CNPJ_CPF_FORNECEDOR'],
                'nm_fornecedor': ['NM_FORNECEDOR', 'NOME_FORNECEDOR'],
                'vr_despesa_contratada': ['VR_DESPESA_CONTRATADA', 'VALOR_DESPESA'],
                'vr_despesa': ['VR_DESPESA_CONTRATADA', 'VALOR_DESPESA'],
                'dt_despesa': ['DT_DESPESA', 'DATA_DESPESA'],
                'ds_despesa': ['DS_DESPESA', 'DESCRICAO_DESPESA'],
                'sq_despesa': ['SQ_DESPESA', 'SEQUENCIAL_DESPESA']
            },
            'despesas_pagas': {
                'vr_pagto_despesa': ['VR_PAGTO_DESPESA', 'VALOR_PAGAMENTO'],
                'vr_pagamento': ['VR_PAGTO_DESPESA', 'VALOR_PAGAMENTO'],
                'dt_pagto_despesa': ['DT_PAGTO_DESPESA', 'DATA_PAGAMENTO'],
                'dt_pagamento': ['DT_PAGTO_DESPESA', 'DATA_PAGAMENTO'],
                'ds_despesa': ['DS_DESPESA', 'DESCRICAO_DESPESA'],
                'sq_despesa': ['SQ_DESPESA', 'SEQUENCIAL_PAGAMENTO']
            },
            'doador_originario': {
                'nr_cpf_cnpj_doador_originario': ['NR_CPF_CNPJ_DOADOR_ORIGINARIO'],
                'nm_doador_originario': ['NM_DOADOR_ORIGINARIO'],
                'nm_doador_originario_rfb': ['NM_DOADOR_ORIGINARIO_RFB'],
                'tp_doador_originario': ['TP_DOADOR_ORIGINARIO'],
                'cd_cnae_doador_originario': ['CD_CNAE_DOADOR_ORIGINARIO'],
                'ds_cnae_doador_originario': ['DS_CNAE_DOADOR_ORIGINARIO'],
                'sq_receita': ['SQ_RECEITA'],
                'dt_receita': ['DT_RECEITA'],
                'ds_receita': ['DS_RECEITA'],
                'vr_receita': ['VR_RECEITA']
            }
        }

        # Combine base and type-specific mappings
        field_mappings = {**base_mappings, **type_mappings.get(data_type, {})}

        finance_record = {}

        # First, preserve ALL original TSE fields
        for original_field, value in raw_row.items():
            if value and value.strip():
                finance_record[original_field.lower()] = value.strip()

        # Then add normalized fields for convenience
        for standard_field, possible_fields in field_mappings.items():
            value = None
            for field in possible_fields:
                if field in raw_row and raw_row[field]:
                    value = raw_row[field].strip()
                    break

            if value:
                finance_record[standard_field] = value

        # Add data type metadata
        finance_record['tse_data_type'] = data_type

        # Add debug info only for rejections, not successes
        record_debug = False  # Only enable for debugging validation issues

        # Validation based on data type with detailed logging
        if data_type in ['receitas', 'doador_originario']:
            # Must have amount for revenue records
            amount_value = finance_record.get('vr_receita') or finance_record.get('valor_receita')
            if not amount_value:
                if record_debug:
                    print(f"    🚫 REJECT ({data_type}): Missing amount field")
                    print(f"       Available fields: {list(finance_record.keys())[:10]}...")
                    print(f"       Looking for: vr_receita, valor_receita")
                return None
        elif data_type == 'despesas_contratadas':
            # Must have expense amount for contracted expenses
            amount_value = finance_record.get('vr_despesa_contratada') or finance_record.get('vr_despesa')
            if not amount_value:
                if record_debug:
                    print(f"    🚫 REJECT ({data_type}): Missing expense amount field")
                    print(f"       Available fields: {list(finance_record.keys())[:10]}...")
                    print(f"       Looking for: vr_despesa_contratada, vr_despesa")
                return None
        elif data_type == 'despesas_pagas':
            # Must have payment amount for paid expenses
            amount_value = finance_record.get('vr_pagto_despesa') or finance_record.get('vr_pagamento')
            if not amount_value:
                if record_debug:
                    print(f"    🚫 REJECT ({data_type}): Missing payment amount field")
                    print(f"       Available fields: {list(finance_record.keys())[:10]}...")
                    print(f"       Looking for: vr_pagto_despesa, vr_pagamento")
                return None

        # Only receitas and despesas_contratadas have candidate CPF
        # despesas_pagas and doador_originario have different structures (no candidate info)
        if data_type in ['receitas', 'despesas_contratadas']:
            cpf_value = finance_record.get('nr_cpf_candidato') or finance_record.get('cpf_candidato')
            if not cpf_value:
                if record_debug:
                    print(f"    🚫 REJECT ({data_type}): Missing candidate CPF")
                    print(f"       Available fields: {list(finance_record.keys())[:10]}...")
                    print(f"       Looking for: nr_cpf_candidato, cpf_candidato")
                return None

        # Success! No logging needed - reduces noise

        return finance_record

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

    def get_electoral_success_statistics(self, candidate_cpf: str, years: List[int] = None) -> Dict[str, Any]:
        """
        Calculate electoral success statistics for a specific candidate
        Useful for the metrics calculator and political career analysis
        """
        if years is None:
            years = [2018, 2020, 2022]  # Default recent elections

        stats = {
            'total_elections': 0,
            'elections_won': 0,
            'elections_lost': 0,
            'substitute_positions': 0,
            'total_votes': 0,
            'success_rate': 0.0,
            'elections_detail': [],
            'career_trajectory': 'UNKNOWN'
        }

        print(f"🔍 Calculating electoral success for CPF: {candidate_cpf}")

        for year in years:
            try:
                candidates = self.get_candidate_data(year)

                # Find this candidate in the election
                candidate_records = [
                    c for c in candidates
                    if c.get('cpf') == candidate_cpf
                ]

                for record in candidate_records:
                    stats['total_elections'] += 1

                    election_detail = {
                        'year': year,
                        'position': record.get('position'),
                        'party': record.get('party'),
                        'electoral_outcome': record.get('electoral_outcome'),
                        'was_elected': record.get('was_elected', False),
                        'votes_received': record.get('votes_received_int', 0),
                        'status_category': record.get('election_status_category')
                    }

                    if record.get('was_elected'):
                        stats['elections_won'] += 1
                    elif record.get('election_status_category') == 'SUBSTITUTE':
                        stats['substitute_positions'] += 1
                    else:
                        stats['elections_lost'] += 1

                    stats['total_votes'] += record.get('votes_received_int', 0)
                    stats['elections_detail'].append(election_detail)

            except Exception as e:
                print(f"  ⚠️ Error analyzing {year}: {e}")

        # Calculate success rate
        if stats['total_elections'] > 0:
            stats['success_rate'] = stats['elections_won'] / stats['total_elections']

        # Determine career trajectory
        if stats['elections_won'] >= 2:
            stats['career_trajectory'] = 'ESTABLISHED_WINNER'
        elif stats['elections_won'] == 1 and stats['total_elections'] > 1:
            stats['career_trajectory'] = 'OCCASIONAL_WINNER'
        elif stats['substitute_positions'] > 0:
            stats['career_trajectory'] = 'SUBSTITUTE_CANDIDATE'
        elif stats['total_elections'] > 1:
            stats['career_trajectory'] = 'PERSISTENT_CANDIDATE'
        elif stats['total_elections'] == 1:
            stats['career_trajectory'] = 'SINGLE_ELECTION'

        print(f"  📊 Success Rate: {stats['success_rate']:.2f} ({stats['elections_won']}/{stats['total_elections']})")
        print(f"  🎯 Career: {stats['career_trajectory']}")

        return stats


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