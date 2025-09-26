#!/usr/bin/env python3
"""
TEST SCRIPT: Direct TSE Candidate Outcome Data
Find the actual candidate data with electoral outcomes
"""

import requests
import json
import csv
import io
import zipfile
from typing import Dict, List, Any
from urllib.parse import urljoin


class TSECandidateDataTester:
    """Test direct TSE access for candidate outcome data"""

    def __init__(self):
        self.base_url = "https://dadosabertos.tse.jus.br/"
        self.api_base = "https://dadosabertos.tse.jus.br/api/3/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TSE-Candidate-Tester/1.0'
        })

    def find_candidate_outcome_packages(self, year: int = 2022):
        """Find packages containing candidate outcome data"""
        print(f"🔍 SEARCHING FOR CANDIDATE OUTCOME PACKAGES - {year}")
        print("=" * 60)

        try:
            # Search for candidate-related packages
            search_terms = [
                f'candidato {year}',
                f'consulta_cand {year}',
                f'consulta_candidato {year}',
                f'resultado {year}',
                f'votacao {year}'
            ]

            all_packages = set()

            for search_term in search_terms:
                print(f"🔍 Searching: '{search_term}'")
                packages = self._search_packages(search_term)
                all_packages.update(packages)
                print(f"  Found {len(packages)} packages")

            print(f"\n📦 TOTAL UNIQUE PACKAGES FOUND: {len(all_packages)}")

            # Analyze each package
            candidate_packages = {}
            for package_name in sorted(all_packages):
                print(f"\n📋 Analyzing package: {package_name}")
                package_info = self._get_package_info(package_name)

                resources = package_info.get('resources', [])
                candidate_resources = []

                for resource in resources:
                    name = resource.get('name', '').lower()
                    if ('candidato' in name and
                        ('consulta' in name or 'resultado' in name or 'eleicao' in name) and
                        resource.get('format', '').lower() in ['csv', 'txt']):
                        candidate_resources.append(resource)

                if candidate_resources:
                    candidate_packages[package_name] = candidate_resources
                    print(f"  ✅ {len(candidate_resources)} candidate resources found")
                else:
                    print(f"  ❌ No candidate resources")

            print(f"\n🎯 PACKAGES WITH CANDIDATE DATA: {len(candidate_packages)}")

            # Test the most promising package
            if candidate_packages:
                test_package = list(candidate_packages.keys())[0]
                print(f"\n🧪 TESTING PACKAGE: {test_package}")
                self._test_candidate_package(test_package, candidate_packages[test_package])

            return candidate_packages

        except Exception as e:
            print(f"❌ Error searching packages: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _search_packages(self, query: str) -> List[str]:
        """Search for packages with specific query"""
        url = urljoin(self.api_base, "action/package_search")
        params = {
            'q': query,
            'rows': 50
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        packages = []
        for result in data.get('result', {}).get('results', []):
            packages.append(result.get('name', ''))

        return packages

    def _get_package_info(self, package_name: str) -> Dict:
        """Get detailed package information"""
        url = urljoin(self.api_base, f"action/package_show")
        params = {'id': package_name}

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json().get('result', {})

    def _test_candidate_package(self, package_name: str, resources: List[Dict]):
        """Test a specific candidate package"""
        print(f"🧪 TESTING CANDIDATE PACKAGE: {package_name}")
        print("=" * 50)

        # Test first resource
        test_resource = resources[0]
        resource_name = test_resource.get('name', 'Unknown')
        print(f"📥 Testing resource: {resource_name}")

        # Look for a small state file first
        small_states = ['RR', 'AC', 'AP', 'RO', 'TO']  # Smaller states for testing
        test_resource_found = None

        for resource in resources:
            name = resource.get('name', '').upper()
            for state in small_states:
                if state in name:
                    test_resource_found = resource
                    print(f"  🎯 Found small state file: {resource.get('name')}")
                    break
            if test_resource_found:
                break

        if not test_resource_found:
            test_resource_found = test_resource

        # Download and analyze
        try:
            candidates = self._download_candidate_sample(test_resource_found, limit=100)
            if candidates:
                print(f"✅ Successfully downloaded {len(candidates)} candidates")
                self._analyze_candidate_fields(candidates)
                return candidates
            else:
                print("❌ No candidate data found")
                return []

        except Exception as e:
            print(f"❌ Error testing package: {e}")
            return []

    def _download_candidate_sample(self, resource: Dict, limit: int = 100) -> List[Dict]:
        """Download a sample of candidate data"""
        download_url = resource.get('url')

        # Fix malformed URLs
        if download_url.startswith('URL: '):
            download_url = download_url[5:]
        if not download_url.startswith('http'):
            download_url = urljoin(self.base_url, download_url)

        print(f"📥 Downloading from: {download_url}")

        # Download with timeout
        response = self.session.get(download_url, timeout=60)
        response.raise_for_status()

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

        csv_file = io.StringIO(csv_content)

        # TSE typically uses semicolon delimiter
        try:
            reader = csv.DictReader(csv_file, delimiter=';')

            for i, row in enumerate(reader):
                if i >= limit:
                    break
                candidates.append(dict(row))

        except Exception as e:
            print(f"  ⚠️ Error processing CSV: {e}")

        return candidates

    def _analyze_candidate_fields(self, candidates: List[Dict]):
        """Analyze candidate data fields for electoral outcomes"""
        print(f"\n🔬 ANALYZING CANDIDATE FIELDS")
        print("=" * 40)

        if not candidates:
            print("❌ No candidates to analyze")
            return

        sample = candidates[0]
        fields = list(sample.keys())
        print(f"📊 Found {len(fields)} fields in candidate data")

        # Look for electoral outcome indicators
        outcome_indicators = {
            'electoral_result': ['sit_tot_turno', 'ds_sit_tot_turno', 'situacao_turno', 'resultado'],
            'votes_received': ['qt_votos_nominais', 'votos_nominais', 'total_votos', 'votos'],
            'candidate_info': ['nm_candidato', 'nome_candidato', 'sq_candidato'],
            'office_info': ['ds_cargo', 'cd_cargo', 'cargo'],
            'party_info': ['sg_partido', 'nm_partido', 'partido'],
            'election_info': ['ano_eleicao', 'cd_eleicao', 'turno']
        }

        print(f"\n🔍 SEARCHING FOR ELECTORAL OUTCOME FIELDS:")
        found_indicators = {}

        for category, field_patterns in outcome_indicators.items():
            found_fields = []

            for field in fields:
                field_lower = field.lower()
                for pattern in field_patterns:
                    if pattern.lower() in field_lower:
                        found_fields.append(field)
                        break

            if found_fields:
                found_indicators[category] = found_fields[0]
                print(f"  ✅ {category}: {found_fields[0]}")
            else:
                print(f"  ❌ {category}: NOT FOUND")

        # Show sample records with key fields
        print(f"\n📋 SAMPLE CANDIDATE RECORDS:")
        for i, candidate in enumerate(candidates[:5], 1):
            print(f"\n  👤 Candidate {i}:")

            # Show found indicator fields
            for category, field_name in found_indicators.items():
                value = candidate.get(field_name, 'N/A')
                print(f"    {category}: {value}")

            # Show a few other interesting fields
            other_fields = [f for f in list(candidate.keys())[:5] if f not in found_indicators.values()]
            for field in other_fields[:3]:
                value = candidate.get(field, 'N/A')
                print(f"    {field}: {value}")

        # Analyze electoral outcomes if found
        if 'electoral_result' in found_indicators:
            self._analyze_electoral_results(candidates, found_indicators['electoral_result'])

        # Show all fields for reference
        print(f"\n📝 ALL AVAILABLE FIELDS ({len(fields)}):")
        for i, field in enumerate(sorted(fields), 1):
            print(f"  {i:2d}. {field}")

        return found_indicators

    def _analyze_electoral_results(self, candidates: List[Dict], result_field: str):
        """Analyze electoral results distribution"""
        print(f"\n📊 ELECTORAL RESULTS ANALYSIS")
        print(f"Field: {result_field}")
        print("=" * 30)

        results = {}
        for candidate in candidates:
            result = candidate.get(result_field, 'UNKNOWN')
            results[result] = results.get(result, 0) + 1

        total = len(candidates)
        print(f"Total candidates analyzed: {total}")

        for result, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"  {result}: {count} ({percentage:.1f}%)")


def main():
    """Run TSE candidate data testing"""
    tester = TSECandidateDataTester()

    # Search for 2022 candidate outcome data
    packages = tester.find_candidate_outcome_packages(2022)

    if packages:
        print(f"\n✅ SUCCESS: Found candidate packages with electoral outcomes!")
        print(f"   Packages: {list(packages.keys())}")
    else:
        print(f"\n❌ No candidate packages with electoral outcomes found")

    # Test 2018 as well
    print(f"\n" + "="*60)
    print("TESTING 2018 DATA")
    packages_2018 = tester.find_candidate_outcome_packages(2018)


if __name__ == "__main__":
    main()