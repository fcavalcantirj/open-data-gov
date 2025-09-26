#!/usr/bin/env python3
"""
TEST SCRIPT: CEPESP-FGV Data Access
Test the "gold standard" cleaned electoral data source
"""

import requests
import json
from typing import Dict, List, Any


class CepespTester:
    """Test CEPESP-FGV API access for electoral data"""

    def __init__(self):
        self.base_url = "https://cepesp.io/api/consulta/"
        self.session = requests.Session()

    def test_cepesp_api_access(self):
        """Test CEPESP API for electoral outcomes data"""
        print(f"🧪 TESTING CEPESP-FGV API ACCESS")
        print("The 'gold standard' for cleaned electoral data")
        print("=" * 60)

        try:
            # Test endpoint structure
            print("📡 Testing CEPESP API endpoints...")

            # According to the document, CEPESP covers 1998-2018
            test_params = {
                'year': 2018,
                'position': 'Deputado Federal',
                'regional_aggregation': 1,  # Candidate level
                'political_aggregation': 2,  # Candidate level
            }

            # Try the consultation endpoint
            url = f"{self.base_url}candidatos"
            print(f"🌐 Testing URL: {url}")

            response = self.session.get(url, params=test_params, timeout=30)
            print(f"📊 Response status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Successfully accessed CEPESP API")
                    print(f"📋 Response structure: {type(data)}")

                    if isinstance(data, list) and len(data) > 0:
                        sample = data[0]
                        print(f"📄 Sample record fields: {list(sample.keys())}")
                        self._analyze_cepesp_fields(data[:10])
                    elif isinstance(data, dict):
                        print(f"📄 Response keys: {list(data.keys())}")

                except json.JSONDecodeError:
                    print(f"⚠️ Response is not JSON, content type: {response.headers.get('content-type')}")
                    print(f"📄 Raw response (first 500 chars): {response.text[:500]}")

            else:
                print(f"❌ API request failed: {response.status_code}")
                print(f"📄 Response: {response.text[:500]}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")

        # Test alternative endpoints
        self._test_alternative_cepesp_endpoints()

    def _analyze_cepesp_fields(self, sample_data: List[Dict]):
        """Analyze CEPESP field structure"""
        print(f"\n🔬 ANALYZING CEPESP FIELD STRUCTURE")
        print("=" * 40)

        if not sample_data:
            print("❌ No sample data to analyze")
            return

        sample = sample_data[0]
        fields = list(sample.keys())
        print(f"📊 Found {len(fields)} fields in CEPESP data")

        # Look for key fields mentioned in the document
        key_fields = {
            'CPF_CANDIDATO': 'CPF identifier',
            'NOME_CANDIDATO': 'Candidate name',
            'NOME_URNA_CANDIDATO': 'Ballot name',
            'DESCRICAO_CARGO': 'Office description',
            'SIGLA_PARTIDO': 'Party abbreviation',
            'QTDE_VOTOS': 'Votes received',
            'DESC_SIT_TOT_TURNO': 'Electoral outcome',
            'ANO_ELEICAO': 'Election year'
        }

        print(f"\n🔍 SEARCHING FOR KEY ELECTORAL FIELDS:")
        found_fields = {}
        for field_name, description in key_fields.items():
            if field_name in fields:
                found_fields[field_name] = sample[field_name]
                print(f"  ✅ {field_name}: {description}")
            else:
                # Look for similar field names
                similar = [f for f in fields if any(part in f.upper() for part in field_name.split('_'))]
                if similar:
                    print(f"  🔍 {field_name}: NOT FOUND, similar: {similar[:3]}")
                else:
                    print(f"  ❌ {field_name}: NOT FOUND")

        # Show sample data
        print(f"\n📋 SAMPLE CANDIDATE DATA:")
        for i, record in enumerate(sample_data[:3], 1):
            print(f"\n  👤 Candidate {i}:")
            for field, value in list(record.items())[:8]:  # Show first 8 fields
                print(f"    {field}: {value}")

        # Show all available fields
        print(f"\n📝 ALL AVAILABLE FIELDS ({len(fields)}):")
        for i, field in enumerate(sorted(fields), 1):
            print(f"  {i:2d}. {field}")

        return found_fields

    def _test_alternative_cepesp_endpoints(self):
        """Test alternative CEPESP access methods"""
        print(f"\n🔄 TESTING ALTERNATIVE CEPESP ENDPOINTS")
        print("=" * 50)

        # Try different endpoints mentioned in documentation
        endpoints = [
            "candidatos",
            "votos",
            "legendas",
            "tse"
        ]

        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                print(f"\n🌐 Testing endpoint: {endpoint}")

                # Simple test request
                test_params = {'year': 2018, 'position': 1}  # Minimal params
                response = self.session.get(url, params=test_params, timeout=15)

                print(f"  📊 Status: {response.status_code}")
                if response.status_code == 200:
                    print(f"  ✅ Endpoint accessible")
                    content_type = response.headers.get('content-type', '')
                    print(f"  📄 Content-Type: {content_type}")
                else:
                    print(f"  ❌ Not accessible: {response.reason}")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    def test_github_documentation(self):
        """Test if GitHub documentation is accessible"""
        print(f"\n📚 TESTING CEPESP GITHUB DOCUMENTATION")
        print("=" * 50)

        github_repos = [
            "https://api.github.com/repos/Cepesp-Fgv/cepesp-r",
            "https://api.github.com/repos/Cepesp-Fgv/cepesp-python",
            "https://api.github.com/repos/Cepesp-Fgv/cepesp-rest"
        ]

        for repo_url in github_repos:
            try:
                response = self.session.get(repo_url, timeout=10)
                if response.status_code == 200:
                    repo_info = response.json()
                    repo_name = repo_info['name']
                    description = repo_info.get('description', 'No description')
                    stars = repo_info.get('stargazers_count', 0)
                    print(f"  ✅ {repo_name}: {stars} stars - {description}")
                else:
                    print(f"  ❌ {repo_url}: Not accessible")

            except Exception as e:
                print(f"  ❌ {repo_url}: Error - {e}")


def main():
    """Run CEPESP testing"""
    tester = CepespTester()

    # Test main API
    tester.test_cepesp_api_access()

    # Test documentation
    tester.test_github_documentation()

    print(f"\n💡 NEXT STEPS:")
    print(f"1. If CEPESP works: Use it for 1998-2018 cleaned data")
    print(f"2. If CEPESP fails: Fall back to direct TSE access")
    print(f"3. Test electionsBR R package for 2020-2024 data")
    print(f"4. Only then enhance our TSE client with outcome fields")


if __name__ == "__main__":
    main()