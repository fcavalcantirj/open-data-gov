#!/usr/bin/env python3
"""
TEST SCRIPT: TSE Electoral Outcomes Analysis
Test access to electoral outcome data before enhancing main TSE client
"""

import requests
import json
import csv
import io
import zipfile
from typing import Dict, List, Any
from urllib.parse import urljoin
import time


class ElectoralOutcomesTester:
    """Test access to TSE electoral outcomes data"""

    def __init__(self):
        self.base_url = "https://dadosabertos.tse.jus.br/"
        self.api_base = "https://dadosabertos.tse.jus.br/api/3/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Electoral-Outcomes-Tester/1.0'
        })

    def test_candidate_outcome_data_access(self, year: int = 2022, state: str = 'SP'):
        """Test access to candidate outcome data for a specific year/state"""
        print(f"🧪 TESTING ELECTORAL OUTCOMES DATA ACCESS")
        print(f"Year: {year}, State: {state}")
        print("=" * 60)

        try:
            # Search for candidate packages
            packages = self._get_candidate_packages(year)
            print(f"📦 Found {len(packages)} candidate packages for {year}")

            if not packages:
                print("❌ No candidate packages found")
                return

            # Test first package
            test_package = packages[0]
            print(f"🔍 Testing package: {test_package}")

            # Get package info
            package_info = self._get_package_info(test_package)
            resources = package_info.get('resources', [])
            print(f"📋 Package has {len(resources)} resources")

            # Look for actual candidate CSV files (not social media or other data)
            candidate_resources = []
            for resource in resources:
                name = resource.get('name', '').lower()
                format_ok = resource.get('format', '').lower() in ['csv', 'txt']
                state_ok = state.lower() in name.lower()

                # Look for main candidate files and exclude social media, assets, etc
                is_main_candidate_data = (
                    (name == 'candidatos' or  # Main candidate file (all states)
                     'candidatos - informações complementares' in name) and  # Supplementary info
                    'rede' not in name and      # Exclude social media
                    'redes' not in name and     # Exclude social networks
                    'bens' not in name and      # Exclude assets
                    'bem' not in name and       # Exclude assets
                    'cassacao' not in name and  # Exclude sanctions
                    'motivo' not in name and    # Exclude rejection reasons
                    'coligacao' not in name     # Exclude coalitions
                )

                # Main candidate files contain all states, so don't filter by state for them
                if format_ok and ((name == 'candidatos' and is_main_candidate_data) or
                                 (state_ok and is_main_candidate_data)):
                    candidate_resources.append(resource)
                    print(f"      ✅ Found candidate file: {resource.get('name')}")

            print(f"🎯 Found {len(candidate_resources)} candidate resources for {state}")

            if not candidate_resources:
                print(f"❌ No candidate resources found for {state}")
                return

            # Test download and analysis
            test_resource = candidate_resources[0]
            print(f"📥 Testing resource: {test_resource.get('name')}")

            # Download sample
            candidates = self._download_and_analyze_candidates(test_resource, limit=1000)
            print(f"✅ Successfully analyzed {len(candidates)} candidates")

            # Analyze electoral outcomes
            self._analyze_electoral_outcomes(candidates)

            return candidates

        except Exception as e:
            print(f"❌ Error testing electoral outcomes: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_candidate_packages(self, year: int) -> List[str]:
        """Get candidate packages for a specific year"""
        url = urljoin(self.api_base, "action/package_search")
        params = {
            'q': f'candidato {year}',
            'rows': 100
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        packages = []
        for result in data.get('result', {}).get('results', []):
            name = result.get('name', '')
            if 'candidato' in name.lower() and str(year) in name:
                packages.append(name)

        return packages

    def _get_package_info(self, package_name: str) -> Dict:
        """Get detailed package information"""
        url = urljoin(self.api_base, f"action/package_show")
        params = {'id': package_name}

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json().get('result', {})

    def _download_and_analyze_candidates(self, resource: Dict, limit: int = 1000) -> List[Dict]:
        """Download and analyze candidate data with retry logic"""
        download_url = resource.get('url')

        # Fix malformed URLs
        if download_url.startswith('URL: '):
            download_url = download_url[5:]
        if not download_url.startswith('http'):
            download_url = urljoin(self.base_url, download_url)

        print(f"📥 Downloading from: {download_url}")

        # Add retry logic for connection issues
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                print(f"    Attempt {attempt + 1}/{max_retries}...")
                response = self.session.get(download_url, timeout=120)  # Longer timeout
                response.raise_for_status()
                break
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10  # Progressive delay: 10s, 20s, 30s
                    print(f"    ⚠️ Connection failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"    ❌ All connection attempts failed: {e}")
                    raise e

        # Process based on file type
        if download_url.endswith('.zip'):
            return self._process_zip_candidates(response.content, limit)
        else:
            return self._process_csv_candidates(response.text, limit)

    def _process_zip_candidates(self, zip_content: bytes, limit: int) -> List[Dict]:
        """Process ZIP file containing candidate data"""
        candidates = []

        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            for filename in zf.namelist():
                if filename.endswith(('.csv', '.txt')):
                    print(f"  📄 Processing file: {filename}")

                    with zf.open(filename) as csvfile:
                        # Read with Latin-1 encoding
                        content = csvfile.read().decode('latin-1')
                        file_candidates = self._process_csv_candidates(content, limit)
                        candidates.extend(file_candidates)

                        if len(candidates) >= limit:
                            break

        return candidates[:limit]

    def _process_csv_candidates(self, csv_content: str, limit: int) -> List[Dict]:
        """Process CSV candidate data"""
        candidates = []

        # Handle potential encoding issues
        csv_file = io.StringIO(csv_content)

        # Try different delimiters
        delimiter = self._detect_delimiter(csv_content)
        print(f"  🔍 Detected delimiter: '{delimiter}'")

        try:
            reader = csv.DictReader(csv_file, delimiter=delimiter)

            for i, row in enumerate(reader):
                if i >= limit:
                    break

                # Store raw row data
                candidates.append(dict(row))

        except Exception as e:
            print(f"  ⚠️ Error processing CSV: {e}")

        return candidates

    def _detect_delimiter(self, content: str) -> str:
        """Detect CSV delimiter"""
        first_line = content.split('\n')[0]

        if ';' in first_line:
            return ';'
        elif ',' in first_line:
            return ','
        elif '\t' in first_line:
            return '\t'
        else:
            return ';'  # Default to semicolon for TSE

    def _analyze_electoral_outcomes(self, candidates: List[Dict]):
        """Analyze electoral outcome fields in candidate data"""
        print(f"\n🔬 ANALYZING ELECTORAL OUTCOMES")
        print("=" * 50)

        if not candidates:
            print("❌ No candidates to analyze")
            return

        # Get field names
        sample_candidate = candidates[0]
        fields = list(sample_candidate.keys())
        print(f"📊 Found {len(fields)} fields in candidate data")

        # Look for key electoral outcome fields
        outcome_fields = {}

        field_patterns = {
            'electoral_outcome': ['sit_tot_turno', 'situacao', 'resultado', 'eleito'],
            'votes_received': ['votos_nominais', 'votos', 'qt_votos'],
            'candidate_id': ['sq_candidato', 'id_candidato', 'candidato'],
            'candidate_name': ['nm_candidato', 'nome_candidato', 'candidato'],
            'office': ['cargo', 'cd_cargo', 'ds_cargo'],
            'party': ['partido', 'sg_partido', 'nm_partido'],
            'state': ['uf', 'sg_uf', 'estado'],
            'election_year': ['ano_eleicao', 'ano', 'year']
        }

        print(f"\n🔍 SEARCHING FOR KEY FIELDS:")
        for category, patterns in field_patterns.items():
            found_fields = []
            for field in fields:
                field_lower = field.lower()
                for pattern in patterns:
                    if pattern in field_lower:
                        found_fields.append(field)
                        break

            if found_fields:
                outcome_fields[category] = found_fields[0]  # Take first match
                print(f"  ✅ {category}: {found_fields[0]}")
            else:
                print(f"  ❌ {category}: NOT FOUND")

        # Analyze sample data
        print(f"\n📋 SAMPLE DATA ANALYSIS:")
        print(f"Analyzing first 10 candidates:")

        for i, candidate in enumerate(candidates[:10]):
            print(f"\n  👤 Candidate {i+1}:")

            for category, field_name in outcome_fields.items():
                value = candidate.get(field_name, 'N/A')
                print(f"    {category}: {value}")

        # Analyze electoral outcomes distribution
        if 'electoral_outcome' in outcome_fields:
            self._analyze_outcome_distribution(candidates, outcome_fields['electoral_outcome'])

        # Show all available fields for reference
        print(f"\n📝 ALL AVAILABLE FIELDS ({len(fields)}):")
        for i, field in enumerate(sorted(fields), 1):
            print(f"  {i:2d}. {field}")

        return outcome_fields

    def _analyze_outcome_distribution(self, candidates: List[Dict], outcome_field: str):
        """Analyze distribution of electoral outcomes"""
        print(f"\n📊 ELECTORAL OUTCOMES DISTRIBUTION:")
        print(f"Field: {outcome_field}")

        outcomes = {}
        for candidate in candidates:
            outcome = candidate.get(outcome_field, 'UNKNOWN')
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

        total = len(candidates)
        print(f"Total candidates: {total}")

        for outcome, count in sorted(outcomes.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"  {outcome}: {count} ({percentage:.1f}%)")


def main():
    """Run electoral outcomes test"""
    tester = ElectoralOutcomesTester()

    # Test recent election data
    print("🧪 TESTING 2022 ELECTION DATA")
    candidates_2022 = tester.test_candidate_outcome_data_access(2022, 'SP')

    if candidates_2022:
        print(f"\n✅ SUCCESS: Found electoral outcome data!")
        print(f"   Sample size: {len(candidates_2022)} candidates")
    else:
        print(f"\n❌ FAILED: Could not access electoral outcome data")

    # Test historical data
    print(f"\n" + "="*60)
    print("🧪 TESTING 2018 ELECTION DATA")
    candidates_2018 = tester.test_candidate_outcome_data_access(2018, 'RJ')


if __name__ == "__main__":
    main()