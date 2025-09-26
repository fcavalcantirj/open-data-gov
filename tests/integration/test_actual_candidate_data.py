#!/usr/bin/env python3
"""
TEST SCRIPT: Actual TSE Candidate Data with Electoral Outcomes
Test the main TSE candidate file that should contain DS_SIT_TOT_TURNO
"""

import requests
import csv
import io
import zipfile
from typing import Dict, List
import time


class ActualCandidateDataTester:
    """Test the main TSE candidate data file for electoral outcomes"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TSE-Candidate-Electoral-Tester/1.0'
        })

    def test_main_candidate_file_2022(self):
        """Test the main 2022 candidate file for electoral outcomes"""
        print("🧪 TESTING MAIN TSE CANDIDATE FILE 2022")
        print("File: consulta_cand_2022.zip")
        print("=" * 60)

        # Direct URL to main candidate file
        url = "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2022.zip"

        try:
            print(f"📥 Downloading: {url}")
            print("⏳ This may take a while (large file)...")

            start_time = time.time()
            response = self.session.get(url, timeout=300)  # 5 minute timeout
            download_time = time.time() - start_time

            print(f"✅ Downloaded in {download_time:.1f} seconds")
            print(f"📊 File size: {len(response.content) / (1024*1024):.1f} MB")

            # Process the ZIP file
            candidates = self._process_candidate_zip(response.content, limit=1000)

            if candidates:
                print(f"✅ Successfully extracted {len(candidates)} candidates")
                self._analyze_electoral_fields(candidates)
                return candidates
            else:
                print("❌ No candidate data extracted")
                return None

        except Exception as e:
            print(f"❌ Error downloading candidate file: {e}")
            return None

    def _process_candidate_zip(self, zip_content: bytes, limit: int = 1000) -> List[Dict]:
        """Process the main candidate ZIP file"""
        candidates = []

        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                print(f"📁 ZIP contains {len(zf.namelist())} files:")

                for filename in zf.namelist():
                    print(f"  📄 {filename}")

                    if filename.endswith(('.csv', '.txt')):
                        print(f"🔍 Processing: {filename}")

                        with zf.open(filename) as csvfile:
                            # Try different encodings
                            try:
                                content = csvfile.read().decode('latin-1')
                            except UnicodeDecodeError:
                                try:
                                    content = csvfile.read().decode('utf-8')
                                except UnicodeDecodeError:
                                    content = csvfile.read().decode('cp1252')

                            # Process CSV
                            file_candidates = self._process_csv_content(content, limit)
                            candidates.extend(file_candidates)

                            if len(candidates) >= limit:
                                print(f"  ✅ Reached limit of {limit} candidates")
                                break

                        # Only process first CSV file for testing
                        break

        except Exception as e:
            print(f"❌ Error processing ZIP: {e}")

        return candidates[:limit]

    def _process_csv_content(self, content: str, limit: int) -> List[Dict]:
        """Process CSV content and extract candidate records"""
        candidates = []

        try:
            # Detect delimiter
            first_line = content.split('\n')[0]
            delimiter = ';' if ';' in first_line else ','
            print(f"  🔍 Using delimiter: '{delimiter}'")

            # Parse CSV
            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file, delimiter=delimiter)

            # Show headers
            headers = reader.fieldnames
            print(f"  📊 Found {len(headers)} columns")

            # Extract sample records
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                candidates.append(dict(row))

            print(f"  ✅ Extracted {len(candidates)} candidate records")

        except Exception as e:
            print(f"  ❌ Error parsing CSV: {e}")

        return candidates

    def _analyze_electoral_fields(self, candidates: List[Dict]):
        """Analyze candidate data for electoral outcome fields"""
        print(f"\n🔬 ANALYZING ELECTORAL OUTCOME FIELDS")
        print("=" * 50)

        if not candidates:
            print("❌ No candidates to analyze")
            return

        # Get field structure
        sample = candidates[0]
        fields = list(sample.keys())
        print(f"📊 Total fields: {len(fields)}")

        # Look for key electoral outcome fields from documentation
        key_fields = {
            'DS_SIT_TOT_TURNO': 'Electoral outcome (win/loss)',
            'QT_VOTOS_NOMINAIS': 'Votes received',
            'NM_CANDIDATO': 'Candidate name',
            'NM_URNA_CANDIDATO': 'Ballot name',
            'NR_CANDIDATO': 'Ballot number',
            'CD_CARGO': 'Office code',
            'DS_CARGO': 'Office description',
            'SG_PARTIDO': 'Party abbreviation',
            'NM_PARTIDO': 'Party name',
            'SG_UE': 'Electoral unit',
            'NM_UE': 'Electoral unit name',
            'ANO_ELEICAO': 'Election year',
            'CD_ELEICAO': 'Election code',
            'SQ_CANDIDATO': 'Candidate sequence number',
            'CPF_CANDIDATO': 'Candidate CPF'
        }

        print(f"\n🔍 SEARCHING FOR KEY ELECTORAL FIELDS:")
        found_fields = {}

        for field_name, description in key_fields.items():
            if field_name in fields:
                found_fields[field_name] = sample[field_name]
                print(f"  ✅ {field_name}: {description}")
            else:
                print(f"  ❌ {field_name}: {description} - NOT FOUND")

        # Special focus on electoral outcomes
        if 'DS_SIT_TOT_TURNO' in found_fields:
            self._analyze_electoral_outcomes(candidates)

        # Show sample data with key fields
        print(f"\n📋 SAMPLE CANDIDATE DATA:")
        for i, candidate in enumerate(candidates[:5], 1):
            print(f"\n  👤 Candidate {i}:")

            # Show key fields if found
            priority_fields = ['NM_CANDIDATO', 'DS_CARGO', 'SG_PARTIDO', 'DS_SIT_TOT_TURNO', 'QT_VOTOS_NOMINAIS']
            for field in priority_fields:
                if field in candidate:
                    value = candidate[field]
                    print(f"    {field}: {value}")

            # Show first few other fields
            other_fields = [f for f in list(candidate.keys())[:8] if f not in priority_fields]
            for field in other_fields[:3]:
                value = candidate.get(field, 'N/A')
                print(f"    {field}: {value}")

        # Show all available fields for reference
        print(f"\n📝 ALL AVAILABLE FIELDS ({len(fields)}):")
        for i, field in enumerate(sorted(fields), 1):
            print(f"  {i:2d}. {field}")

        return found_fields

    def _analyze_electoral_outcomes(self, candidates: List[Dict]):
        """Analyze the distribution of electoral outcomes"""
        print(f"\n📊 ELECTORAL OUTCOMES ANALYSIS")
        print(f"Field: DS_SIT_TOT_TURNO")
        print("=" * 40)

        outcomes = {}
        total_votes = 0
        vote_field = 'QT_VOTOS_NOMINAIS'

        for candidate in candidates:
            # Outcome analysis
            outcome = candidate.get('DS_SIT_TOT_TURNO', 'UNKNOWN')
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

            # Vote analysis
            if vote_field in candidate:
                try:
                    votes = int(candidate[vote_field] or 0)
                    total_votes += votes
                except (ValueError, TypeError):
                    pass

        total_candidates = len(candidates)
        print(f"Total candidates analyzed: {total_candidates}")

        if vote_field in candidates[0]:
            avg_votes = total_votes / total_candidates if total_candidates > 0 else 0
            print(f"Total votes: {total_votes:,}")
            print(f"Average votes per candidate: {avg_votes:.1f}")

        print(f"\nElectoral Outcomes Distribution:")
        for outcome, count in sorted(outcomes.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_candidates) * 100
            print(f"  {outcome}: {count} ({percentage:.1f}%)")


def main():
    """Run the actual candidate data test"""
    tester = ActualCandidateDataTester()

    # Test main 2022 candidate file
    candidates = tester.test_main_candidate_file_2022()

    if candidates:
        print(f"\n✅ SUCCESS: Found actual electoral outcome data!")
        print(f"   Total sample: {len(candidates)} candidates")
        print(f"   Ready to enhance TSE client with electoral fields")
    else:
        print(f"\n❌ FAILED: Could not access electoral outcome data")
        print(f"   Need to investigate alternative approaches")


if __name__ == "__main__":
    main()