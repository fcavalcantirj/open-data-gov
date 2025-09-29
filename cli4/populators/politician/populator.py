"""
CLI4 Politician Populator
Complete politician population following DATA_POPULATION_GUIDE.md
"""

import requests
import time
from typing import Dict, List, Any, Optional
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from src.clients.tse_client import TSEClient


class CLI4PoliticianPopulator:
    """Populate politicians table with Deputados + TSE correlation"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.camara_base = "https://dadosabertos.camara.leg.br/api/v2"
        self.tse_base = "https://dadosabertos.tse.jus.br"
        self.tse_client = TSEClient()  # ✅ REUSED TSE CLIENT - keeps cache between politicians

    def populate(self, limit: Optional[int] = None, start_id: Optional[int] = None,
                active_only: bool = True, resume_from: Optional[int] = None) -> List[int]:
        """Main population method"""

        print(f"🔍 Discovering active deputies...")
        deputy_ids = self._get_deputy_ids(active_only=active_only, limit=limit, start_id=start_id)

        if resume_from:
            deputy_ids = [d for d in deputy_ids if d >= resume_from]

        print(f"📋 Processing {len(deputy_ids)} deputies")

        # Pre-load TSE data for all required states
        self._preload_tse_data_for_states(deputy_ids)

        created_ids = []

        for i, deputy_id in enumerate(deputy_ids, 1):
            try:
                print(f"\n👤 [{i}/{len(deputy_ids)}] Processing deputy {deputy_id}")

                # Get deputy details
                deputy_detail = self._get_deputy_detail(deputy_id)
                if not deputy_detail:
                    continue

                # TSE correlation by CPF with state optimization
                deputy_state = deputy_detail.get('ultimoStatus', {}).get('siglaUf')
                tse_matches = self._find_tse_candidate_by_cpf(deputy_detail['cpf'], deputy_state)

                # Create politician record
                politician_data = self._build_politician_record(deputy_detail, tse_matches)
                politician_id = self._insert_politician(politician_data)

                if politician_id:
                    created_ids.append(politician_id)
                    self.logger.log_processing(
                        'politician', str(politician_id), 'success',
                        {'name': deputy_detail['nomeCivil'], 'tse_linked': len(tse_matches) > 0}
                    )

            except Exception as e:
                self.logger.log_processing('politician', str(deputy_id), 'error', {'error': str(e)})
                print(f"❌ Error processing deputy {deputy_id}: {e}")
                continue

        return created_ids

    def _preload_tse_data_for_states(self, deputy_ids: List[int]):
        """Pre-load TSE data for all states we'll need to avoid repeated downloads"""
        print("🚀 Pre-loading TSE data for all required states...")

        # Discover all states we need
        required_states = set()
        for deputy_id in deputy_ids:
            deputy_detail = self._get_deputy_detail(deputy_id)
            if deputy_detail:
                state = deputy_detail.get('ultimoStatus', {}).get('siglaUf')
                if state:
                    required_states.add(state)

        print(f"📍 Found {len(required_states)} unique states: {sorted(required_states)}")

        # Get election years we'll search
        packages = self.tse_client.get_packages()
        candidate_packages = [p for p in packages if 'candidatos-' in p and p.split('-')[-1].isdigit()]
        recent_years = []
        for package in candidate_packages:
            year = int(package.split('-')[-1])
            if year >= 2010:
                recent_years.append(year)
        recent_years = sorted(set(recent_years), reverse=True)[:3]

        # Pre-load each state for each year
        total_combinations = len(required_states) * len(recent_years)
        current = 0

        for state in sorted(required_states):
            for year in recent_years:
                current += 1
                print(f"📥 [{current}/{total_combinations}] Pre-loading {state} {year}...")
                try:
                    # This will download and cache the data
                    candidates = self.tse_client.get_candidate_data(year, state)
                    print(f"  ✓ Cached {len(candidates)} candidates for {state} {year}")
                except Exception as e:
                    print(f"  ❌ Failed to load {state} {year}: {e}")

        print("✅ TSE pre-loading complete - all politician searches will now be instant!")

    def _get_deputy_ids(self, active_only: bool = True, limit: Optional[int] = None,
                       start_id: Optional[int] = None) -> List[int]:
        """Get list of deputy IDs"""
        wait_time = self.rate_limiter.wait_if_needed('camara')

        start_time = time.time()
        url = f"{self.camara_base}/deputados"
        params = {}

        if active_only:
            params['ordem'] = 'ASC'
            params['ordenarPor'] = 'nome'
        else:
            # Get ALL deputies including inactive ones (on leave, vacant seats, etc.)
            params['idLegislatura'] = 57  # Current legislature
            params['itens'] = 1000  # Ensure we get all deputies
            params['ordem'] = 'ASC'
            params['ordenarPor'] = 'nome'

        response = requests.get(url, params=params)
        response_time = time.time() - start_time

        if response.status_code == 200:
            self.logger.log_api_call('camara', '/deputados', 'success', response_time)
            data = response.json()
            deputy_ids = [dep['id'] for dep in data['dados']]

            if start_id:
                deputy_ids = [d for d in deputy_ids if d >= start_id]
            if limit:
                deputy_ids = deputy_ids[:limit]

            return deputy_ids
        else:
            self.logger.log_api_call('camara', '/deputados', 'error', response_time)
            raise Exception(f"Failed to get deputies: {response.status_code}")

    def _get_deputy_detail(self, deputy_id: int) -> Optional[Dict]:
        """Get detailed deputy information"""
        wait_time = self.rate_limiter.wait_if_needed('camara')

        start_time = time.time()
        url = f"{self.camara_base}/deputados/{deputy_id}"

        response = requests.get(url)
        response_time = time.time() - start_time

        if response.status_code == 200:
            self.logger.log_api_call('camara', f'/deputados/{deputy_id}', 'success', response_time)
            return response.json()['dados']
        else:
            self.logger.log_api_call('camara', f'/deputados/{deputy_id}', 'error', response_time)
            return None

    def _find_tse_candidate_by_cpf(self, cpf: str, state: Optional[str] = None) -> List[Dict]:
        """Find TSE candidacy records by CPF using cached TSE client"""
        if not cpf:
            return []

        try:
            # Get available election years from packages
            packages = self.tse_client.get_packages()
            candidate_packages = [p for p in packages if 'candidatos-' in p and p.split('-')[-1].isdigit()]

            # Focus on recent election years for efficiency
            recent_years = []
            for package in candidate_packages:
                year = int(package.split('-')[-1])
                if year >= 2010:  # Search last few election cycles
                    recent_years.append(year)

            recent_years = sorted(set(recent_years), reverse=True)[:3]  # Limit to 3 most recent for speed
            state_info = f" (state: {state})" if state else " (all states)"
            print(f"  🔍 Searching {len(recent_years)} TSE election years: {recent_years}{state_info}")

            all_records = []

            for year in recent_years:
                try:
                    print(f"    → Searching TSE {year}...")

                    # Use cached TSE client with state filtering for performance
                    candidates = self.tse_client.get_candidate_data(year, state)

                    if candidates:
                        # Search by CPF
                        matching_records = [
                            candidate for candidate in candidates
                            if candidate.get('nr_cpf_candidato') == cpf or candidate.get('cpf') == cpf
                        ]

                        if matching_records:
                            print(f"      ✅ Found {len(matching_records)} records in {year}")
                            # Add year info
                            for record in matching_records:
                                record['year'] = year
                            all_records.extend(matching_records)
                        else:
                            print(f"      ❌ No CPF matches in {year}")

                except Exception as e:
                    print(f"    ⚠️ Error searching {year}: {e}")
                    continue

            print(f"  🔗 Total TSE records found: {len(all_records)}")
            return all_records

        except Exception as e:
            print(f"  ❌ Error in TSE search: {e}")
            return []

    def _load_tse_dataset_OLD_UNUSED(self, dataset_name: str):
        """Load TSE dataset from CKAN API exactly as specified in DATA_POPULATION_GUIDE.md"""
        wait_time = self.rate_limiter.wait_if_needed('tse')

        start_time = time.time()
        # Get dataset metadata
        ckan_url = f"https://dadosabertos.tse.jus.br/api/3/action/package_show?id={dataset_name}"
        response = requests.get(ckan_url)
        response_time = time.time() - start_time

        if response.status_code != 200:
            self.logger.log_api_call('tse', f'/package_show/{dataset_name}', 'error', response_time)
            return None

        self.logger.log_api_call('tse', f'/package_show/{dataset_name}', 'success', response_time)
        dataset_info = response.json()

        if not dataset_info.get('success'):
            return None

        # Find CSV resource URL
        for resource in dataset_info['result']['resources']:
            if resource['format'].upper() == 'CSV':
                csv_url = resource['url']

                wait_time = self.rate_limiter.wait_if_needed('tse')
                start_time = time.time()

                # Load with pandas exactly as guide specifies
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_url, dtype=str, low_memory=False)
                    response_time = time.time() - start_time
                    self.logger.log_api_call('tse', f'/csv_load/{dataset_name}', 'success', response_time)
                    return df
                except Exception as e:
                    response_time = time.time() - start_time
                    self.logger.log_api_call('tse', f'/csv_load/{dataset_name}', 'error', response_time)
                    print(f"    ❌ Error loading CSV: {e}")
                    return None

        print(f"    ❌ No CSV resource found for dataset: {dataset_name}")
        return None

    def _search_tse_year_by_cpf(self, year: int, cpf_clean: str) -> List[Dict]:
        """Search specific TSE year using file download approach"""
        wait_time = self.rate_limiter.wait_if_needed('tse')

        # Get package info
        start_time = time.time()
        package_url = f"{self.tse_base}/api/3/action/package_show"

        response = requests.get(package_url, params={'id': f'candidatos-{year}'})
        response_time = time.time() - start_time

        if response.status_code != 200:
            self.logger.log_api_call('tse', f'/package_show/candidatos-{year}', 'error', response_time)
            return []

        self.logger.log_api_call('tse', f'/package_show/candidatos-{year}', 'success', response_time)

        data = response.json()
        if not data.get('success'):
            return []

        # Find candidate CSV resource
        resources = data.get('result', {}).get('resources', [])
        candidate_resource = None

        for resource in resources:
            name = resource.get('name', '').lower()
            format_type = resource.get('format', '').lower()

            if format_type in ['csv', 'txt', 'zip']:
                if ('candidatos' in name and 'complementares' not in name) or 'consulta_cand' in name:
                    candidate_resource = resource
                    break

        if not candidate_resource:
            return []

        # Download and search the file
        try:
            download_url = candidate_resource.get('url')
            if not download_url.startswith('http'):
                download_url = f"{self.tse_base.rstrip('/')}/{download_url.lstrip('/')}"

            wait_time = self.rate_limiter.wait_if_needed('tse')
            start_time = time.time()

            response = requests.get(download_url, timeout=30)
            response_time = time.time() - start_time

            if response.status_code != 200:
                self.logger.log_api_call('tse', f'/download/{year}', 'error', response_time)
                return []

            self.logger.log_api_call('tse', f'/download/{year}', 'success', response_time)

            # Process the file content
            if download_url.endswith('.zip'):
                return self._search_zip_for_cpf(response.content, cpf_clean, year)
            else:
                return self._search_csv_for_cpf(response.text, cpf_clean, year)

        except Exception as e:
            print(f"    ❌ Download error for {year}: {e}")
            return []

    def _search_zip_for_cpf(self, zip_content: bytes, cpf_clean: str, year: int) -> List[Dict]:
        """Search ZIP file for CPF matches"""
        import zipfile
        import io

        matches = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                for file_name in zip_file.namelist():
                    if file_name.endswith('.csv') or file_name.endswith('.txt'):
                        if 'candidatos' in file_name.lower():
                            with zip_file.open(file_name) as csv_file:
                                content = csv_file.read().decode('utf-8', errors='ignore')
                                file_matches = self._search_csv_for_cpf(content, cpf_clean, year)
                                matches.extend(file_matches)
        except Exception as e:
            print(f"    ❌ ZIP processing error: {e}")

        return matches

    def _search_csv_for_cpf(self, csv_content: str, cpf_clean: str, year: int) -> List[Dict]:
        """Search CSV content for CPF matches"""
        import csv
        import io

        matches = []

        try:
            # Try different delimiters like original CLI
            for delimiter in [';', ',', '\t']:
                try:
                    csv_file = io.StringIO(csv_content)
                    reader = csv.DictReader(csv_file, delimiter=delimiter)

                    sample_row = next(reader, None)
                    if sample_row and len(sample_row) > 5:  # Good delimiter found
                        csv_file.seek(0)
                        reader = csv.DictReader(csv_file, delimiter=delimiter)

                        for row in reader:
                            # Check for CPF match (multiple possible field names)
                            cpf_fields = ['NR_CPF_CANDIDATO', 'CPF_CANDIDATO', 'cpf']
                            row_cpf = None

                            for field in cpf_fields:
                                if field in row and row[field]:
                                    import re
                                    row_cpf = re.sub(r'[^\d]', '', row[field])
                                    break

                            if row_cpf == cpf_clean:
                                # Convert TSE row to our format
                                match = self._normalize_tse_row(row, year)
                                if match:
                                    matches.append(match)

                        break  # Good delimiter found and processed

                except Exception:
                    continue

        except Exception as e:
            print(f"    ❌ CSV processing error: {e}")

        return matches

    def _normalize_tse_row(self, row: Dict[str, str], year: int) -> Optional[Dict]:
        """Normalize TSE row following original CLI field mapping"""
        if not row:
            return None

        # Field mappings from original CLI
        field_mappings = {
            'nm_candidato': ['NM_CANDIDATO', 'NOME_CANDIDATO'],
            'nr_cpf_candidato': ['NR_CPF_CANDIDATO', 'CPF_CANDIDATO'],
            'nr_candidato': ['NR_CANDIDATO', 'NUMERO_CANDIDATO'],
            'sq_candidato': ['SQ_CANDIDATO'],
            'nm_urna_candidato': ['NM_URNA_CANDIDATO'],
            'nm_social_candidato': ['NM_SOCIAL_CANDIDATO'],
            'nr_titulo_eleitoral_candidato': ['NR_TITULO_ELEITORAL_CANDIDATO'],
            'sg_partido': ['SG_PARTIDO', 'SIGLA_PARTIDO'],
            'nm_partido': ['NM_PARTIDO'],
            'nr_partido': ['NR_PARTIDO'],
            'cd_cargo': ['CD_CARGO'],
            'ds_cargo': ['DS_CARGO', 'CARGO'],
            'sg_uf': ['SG_UF', 'UF'],
            'ds_genero': ['DS_GENERO'],
            'cd_genero': ['CD_GENERO'],
            'ds_grau_instrucao': ['DS_GRAU_INSTRUCAO'],
            'cd_grau_instrucao': ['CD_GRAU_INSTRUCAO'],
            'ds_ocupacao': ['DS_OCUPACAO'],
            'cd_ocupacao': ['CD_OCUPACAO'],
            'ds_estado_civil': ['DS_ESTADO_CIVIL'],
            'cd_estado_civil': ['CD_ESTADO_CIVIL'],
            'ds_cor_raca': ['DS_COR_RACA'],
            'cd_cor_raca': ['CD_COR_RACA'],
            'ds_email': ['DS_EMAIL'],
            'cd_situacao_candidatura': ['CD_SITUACAO_CANDIDATURA'],
            'ds_situacao_candidatura': ['DS_SITUACAO_CANDIDATURA'],
            'cd_sit_tot_turno': ['CD_SIT_TOT_TURNO'],
            'ds_sit_tot_turno': ['DS_SIT_TOT_TURNO'],
            'sg_uf_nascimento': ['SG_UF_NASCIMENTO'],
            'sg_ue': ['SG_UE'],
            'nm_ue': ['NM_UE'],
            'nr_federacao': ['NR_FEDERACAO'],
            'sg_federacao': ['SG_FEDERACAO']
        }

        normalized = {'year': year}

        # Map all fields
        for standard_field, possible_fields in field_mappings.items():
            for field in possible_fields:
                if field in row and row[field] and row[field].strip():
                    normalized[standard_field] = row[field].strip()
                    break

        # Validate essential fields
        if not normalized.get('nm_candidato'):
            return None

        return normalized

    def _get_available_tse_candidate_years(self) -> List[int]:
        """Get available TSE candidate dataset years"""
        try:
            wait_time = self.rate_limiter.wait_if_needed('tse')

            start_time = time.time()
            url = f"{self.tse_base}/api/3/action/package_list"

            response = requests.get(url)
            response_time = time.time() - start_time

            if response.status_code == 200:
                self.logger.log_api_call('tse', '/package_list', 'success', response_time)
                data = response.json()
                packages = data.get('result', [])

                years = []
                for package in packages:
                    if package.startswith('candidatos-') and package[11:].isdigit():
                        year = int(package[11:])
                        years.append(year)

                years.sort()
                return years
            else:
                self.logger.log_api_call('tse', '/package_list', 'error', response_time)
                # Fallback to known election years
                return [2022, 2020, 2018, 2016, 2014, 2012, 2010, 2008, 2006, 2004, 2002]

        except Exception as e:
            print(f"⚠️ Could not discover TSE years: {e}")
            # Fallback to known election years
            return [2022, 2020, 2018, 2016, 2014, 2012, 2010, 2008, 2006, 2004, 2002]

    def _build_politician_record(self, deputy_detail: Dict, tse_matches: List[Dict]) -> Dict:
        """Build complete politician record following DATA_POPULATION_GUIDE.md field mapping"""

        # Get most recent TSE candidacy
        most_recent_tse = None
        if tse_matches:
            most_recent_tse = max(tse_matches, key=lambda x: x['year'])

        # Extract deputy status for cleaner access
        deputy_status = deputy_detail.get('ultimoStatus', {})
        gabinete = deputy_status.get('gabinete', {})

        record = {
            # UNIVERSAL IDENTIFIERS (following DATA_POPULATION_GUIDE.md exactly)
            'cpf': deputy_detail.get('cpf'),
            'nome_civil': deputy_detail.get('nomeCivil'),
            'nome_completo_normalizado': self._normalize_name(deputy_detail.get('nomeCivil', '')),

            # SOURCE SYSTEM LINKS
            'deputy_id': deputy_detail.get('id'),
            'sq_candidato_current': most_recent_tse['sq_candidato'] if most_recent_tse else None,
            'deputy_active': True,

            # DEPUTADOS CORE IDENTITY
            'nome_eleitoral': deputy_status.get('nomeEleitoral'),
            'url_foto': deputy_status.get('urlFoto'),  # Photo is in ultimoStatus, not deputy_detail
            'data_falecimento': deputy_detail.get('dataFalecimento'),

            # TSE CORE IDENTITY (when available)
            'electoral_number': most_recent_tse.get('nr_candidato') if most_recent_tse else None,
            'nr_titulo_eleitoral': most_recent_tse.get('nr_titulo_eleitoral_candidato') if most_recent_tse else None,
            'nome_urna_candidato': most_recent_tse.get('nm_urna_candidato') if most_recent_tse else None,
            'nome_social_candidato': most_recent_tse.get('nm_social_candidato') if most_recent_tse else None,

            # CURRENT POLITICAL STATUS
            'current_party': deputy_status.get('siglaPartido'),
            'current_state': deputy_status.get('siglaUf'),
            'current_legislature': deputy_status.get('idLegislatura'),
            'situacao': deputy_status.get('situacao'),
            'condicao_eleitoral': deputy_status.get('condicaoEleitoral'),

            # TSE POLITICAL DETAILS
            'nr_partido': most_recent_tse.get('nr_partido') if most_recent_tse else None,
            'nm_partido': most_recent_tse.get('nm_partido') if most_recent_tse else None,
            'nr_federacao': most_recent_tse.get('nr_federacao') if most_recent_tse else None,
            'sg_federacao': most_recent_tse.get('sg_federacao') if most_recent_tse else None,
            'current_position': most_recent_tse.get('ds_cargo') if most_recent_tse else None,

            # TSE ELECTORAL STATUS
            'cd_situacao_candidatura': most_recent_tse.get('cd_situacao_candidatura') if most_recent_tse else None,
            'ds_situacao_candidatura': most_recent_tse.get('ds_situacao_candidatura') if most_recent_tse else None,
            'cd_sit_tot_turno': most_recent_tse.get('cd_sit_tot_turno') if most_recent_tse else None,
            'ds_sit_tot_turno': most_recent_tse.get('ds_sit_tot_turno') if most_recent_tse else None,

            # DEMOGRAPHICS (Deputados + TSE combined)
            'birth_date': deputy_detail.get('dataNascimento'),
            'birth_state': deputy_detail.get('ufNascimento') or (most_recent_tse.get('sg_uf_nascimento') if most_recent_tse else None),
            'birth_municipality': deputy_detail.get('municipioNascimento'),
            'gender': deputy_detail.get('sexo') or (most_recent_tse.get('ds_genero') if most_recent_tse else None),
            'gender_code': most_recent_tse.get('cd_genero') if most_recent_tse else None,
            'education_level': deputy_detail.get('escolaridade') or (most_recent_tse.get('ds_grau_instrucao') if most_recent_tse else None),
            'education_code': most_recent_tse.get('cd_grau_instrucao') if most_recent_tse else None,
            'occupation': most_recent_tse.get('ds_ocupacao') if most_recent_tse else None,
            'occupation_code': most_recent_tse.get('cd_ocupacao') if most_recent_tse else None,
            'marital_status': most_recent_tse.get('ds_estado_civil') if most_recent_tse else None,
            'marital_status_code': most_recent_tse.get('cd_estado_civil') if most_recent_tse else None,
            'race_color': most_recent_tse.get('ds_cor_raca') if most_recent_tse else None,
            'race_color_code': most_recent_tse.get('cd_cor_raca') if most_recent_tse else None,

            # GEOGRAPHIC DETAILS
            'sg_ue': most_recent_tse.get('sg_ue') if most_recent_tse else None,
            'nm_ue': most_recent_tse.get('nm_ue') if most_recent_tse else None,

            # CONTACT INFORMATION
            'email': deputy_status.get('email') or (most_recent_tse.get('ds_email') if most_recent_tse else None),
            'phone': gabinete.get('telefone'),
            'website': deputy_detail.get('urlWebsite'),
            'social_networks': self._format_social_networks(deputy_detail.get('redeSocial')),

            # OFFICE DETAILS
            'office_building': gabinete.get('predio'),
            'office_room': gabinete.get('sala'),
            'office_floor': gabinete.get('andar'),
            'office_phone': gabinete.get('telefone'),
            'office_email': gabinete.get('email'),

            # VALIDATION FLAGS
            'cpf_validated': True,  # From official API
            'tse_linked': bool(most_recent_tse),
            'last_updated_date': 'CURRENT_DATE'
        }

        return record

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ''

        # Remove accents and convert to uppercase
        import unicodedata
        normalized = unicodedata.normalize('NFD', name)
        ascii_name = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return ascii_name.upper().strip()

    def _format_social_networks(self, social_data: Any) -> Optional[str]:
        """Format social networks data for JSONB storage"""
        if not social_data:
            return None

        import json

        # If it's already a string, try to parse it
        if isinstance(social_data, str):
            try:
                # If it's already JSON, return as is
                json.loads(social_data)
                return social_data
            except:
                # If it's a single URL, wrap in array
                return json.dumps([social_data])

        # If it's a list, convert to JSON
        if isinstance(social_data, list):
            return json.dumps(social_data)

        # If it's a dict, convert to JSON
        if isinstance(social_data, dict):
            return json.dumps(social_data)

        # Default fallback
        return json.dumps(str(social_data))

    def _should_update_field(self, new_value, existing_value, field_name: str) -> bool:
        """Determine if field should be updated with smart data preservation logic"""
        # Never overwrite with null/empty values
        if new_value is None or str(new_value).strip() == '':
            return False

        # No existing value - always update with new data
        if existing_value is None or str(existing_value).strip() == '':
            return True

        # Special handling for JSONB fields (social networks)
        if field_name == 'social_networks':
            # Compare normalized JSON - only update if actually different
            try:
                import json
                new_json = json.dumps(new_value, sort_keys=True) if new_value else ''
                existing_json = json.dumps(existing_value, sort_keys=True) if existing_value else ''
                return new_json != existing_json
            except:
                return str(new_value) != str(existing_value)

        # For all other fields, compare string representations
        return str(new_value).strip() != str(existing_value).strip()

    def _insert_politician(self, politician_data: Dict) -> Optional[int]:
        """Insert or update politician record with smart data preservation"""
        try:
            # Get full existing record for comparison
            existing_records = database.execute_query(
                "SELECT * FROM unified_politicians WHERE cpf = %s",
                (politician_data['cpf'],)
            )

            if existing_records:
                existing_data = existing_records[0]
                existing_id = existing_data['id']

                # Smart update logic - only update fields with meaningful changes
                update_fields = []
                update_values = []
                changes_log = []

                # Skip immutable fields
                immutable_fields = {'id', 'created_at', 'cpf'}

                for field, new_value in politician_data.items():
                    if field in immutable_fields:
                        continue

                    existing_value = existing_data.get(field)

                    if self._should_update_field(new_value, existing_value, field):
                        # Handle SQL function values properly
                        if new_value == 'NOW()':
                            update_fields.append(f"{field} = NOW()")
                        elif new_value == 'CURRENT_DATE':
                            update_fields.append(f"{field} = CURRENT_DATE")
                        else:
                            update_fields.append(f"{field} = %s")
                            update_values.append(new_value)
                        changes_log.append(f"{field}: '{existing_value}' → '{new_value}'")

                # Only execute update if there are actual changes
                if update_fields:
                    # Add updated_at timestamp
                    update_fields.append("updated_at = NOW()")

                    query = f"""
                        UPDATE unified_politicians
                        SET {', '.join(update_fields)}
                        WHERE cpf = %s
                        RETURNING id
                    """

                    update_values.append(politician_data['cpf'])
                    result = database.execute_insert_returning(query, tuple(update_values))

                    print(f"🔄 Updated politician {politician_data.get('nome_civil', 'Unknown')}")
                    for change in changes_log[:3]:  # Show first 3 changes
                        print(f"    📝 {change}")
                    if len(changes_log) > 3:
                        print(f"    📝 ... and {len(changes_log) - 3} more changes")

                    return result[0]['id'] if result else existing_id
                else:
                    print(f"⏭️ No changes for {politician_data.get('nome_civil', 'Unknown')} (CPF: {politician_data['cpf']})")
                    return existing_id

            # No existing record found - insert new politician
            print(f"➕ Creating new politician: {politician_data.get('nome_civil', 'Unknown')}")

            # Build INSERT query
            fields = []
            values = []
            placeholders = []

            for field, value in politician_data.items():
                if value is not None:
                    fields.append(field)
                    if value == 'NOW()':
                        placeholders.append('NOW()')
                    elif value == 'CURRENT_DATE':
                        placeholders.append('CURRENT_DATE')
                    else:
                        placeholders.append('%s')
                        values.append(value)

            query = f"""
                INSERT INTO unified_politicians ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """

            result = database.execute_insert_returning(query, tuple(values))

            if result:
                return result[0]['id']
            else:
                return None

        except Exception as e:
            print(f"❌ Error inserting politician: {e}")
            return None