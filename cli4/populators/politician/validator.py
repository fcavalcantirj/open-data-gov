"""
CLI4 Politician Validator
Comprehensive validation based on DATA_POPULATION_GUIDE.md specification
"""

from typing import Dict, List, Any, Optional
from cli4.modules import database


class CLI4PoliticianValidator:
    """Comprehensive politician data validation following DATA_POPULATION_GUIDE.md"""

    def __init__(self):
        self.validation_results = {
            'total_politicians': 0,
            'validation_categories': {},
            'critical_issues': [],
            'warnings': [],
            'summary': {},
            'compliance_score': 0.0
        }

    def validate_all_politicians(self, limit: Optional[int] = None, detailed: bool = False) -> Dict[str, Any]:
        """Run comprehensive validation on all politician records"""
        print("🔍 COMPREHENSIVE POLITICIAN VALIDATION")
        print("=" * 60)
        print("Based on DATA_POPULATION_GUIDE.md field specifications")
        print("=" * 60)

        # Get politicians with optional limit
        query = "SELECT * FROM unified_politicians"
        if limit:
            query += f" LIMIT {limit}"

        politicians = database.execute_query(query)
        self.validation_results['total_politicians'] = len(politicians)

        if not politicians:
            print("⚠️ No politicians found in database")
            return self.validation_results

        limit_text = f" (limited to {limit})" if limit else ""
        print(f"📊 Validating {len(politicians)} politician records{limit_text}...")

        # Run validation categories - ALL FIELDS FROM DATA_POPULATION_GUIDE.md
        self._validate_universal_identifiers(politicians)
        self._validate_source_system_links(politicians)
        self._validate_deputados_core_identity(politicians)
        self._validate_current_political_status(politicians)
        self._validate_demographics(politicians)
        self._validate_education_profession(politicians)
        self._validate_electoral_information(politicians)
        self._validate_contact_information(politicians)
        self._validate_office_details(politicians)
        self._validate_career_timeline(politicians)
        self._validate_tse_correlation_metadata(politicians)
        self._validate_system_metadata(politicians)
        self._validate_validation_flags(politicians)

        # Calculate compliance score
        self._calculate_compliance_score()

        # Print results
        self._print_validation_summary()

        return self.validation_results

    def _validate_universal_identifiers(self, politicians: List[Dict]):
        """Validate Universal Identifiers (critical fields)"""
        category = "Universal Identifiers"
        issues = []
        total_fields = len(politicians) * 4  # 4 required fields per DATA_POPULATION_GUIDE.md

        # ID validation (primary key)
        missing_id = [p for p in politicians if not p.get('id')]

        # CPF validation
        missing_cpf = [p for p in politicians if not p.get('cpf')]
        invalid_cpf_length = [p for p in politicians if p.get('cpf') and len(str(p['cpf'])) != 11]

        # Nome Civil validation
        missing_nome_civil = [p for p in politicians if not p.get('nome_civil')]

        # Normalized name validation
        missing_normalized = [p for p in politicians if not p.get('nome_completo_normalizado')]

        valid_fields = total_fields - len(missing_id) - len(missing_cpf) - len(invalid_cpf_length) - len(missing_nome_civil) - len(missing_normalized)

        if missing_id:
            issues.append(f"❌ {len(missing_id)} politicians missing id")
        if missing_cpf:
            issues.append(f"❌ {len(missing_cpf)} politicians missing CPF")
        if invalid_cpf_length:
            issues.append(f"❌ {len(invalid_cpf_length)} politicians with invalid CPF length")
        if missing_nome_civil:
            issues.append(f"❌ {len(missing_nome_civil)} politicians missing nome_civil")
        if missing_normalized:
            issues.append(f"❌ {len(missing_normalized)} politicians missing normalized name")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': True
        }

    def _validate_source_system_links(self, politicians: List[Dict]):
        """Validate Source System Links"""
        category = "Source System Links"
        issues = []
        total_fields = len(politicians) * 4  # Updated for 4 fields

        missing_deputy_id = [p for p in politicians if not p.get('deputy_id')]
        missing_deputy_uri = [p for p in politicians if not p.get('deputy_uri')]
        missing_sq_candidato = [p for p in politicians if not p.get('sq_candidato_current')]
        missing_active_flag = [p for p in politicians if p.get('deputy_active') is None]

        # TSE linking rate
        tse_linked_count = len([p for p in politicians if p.get('tse_linked')])
        tse_link_rate = (tse_linked_count / len(politicians)) * 100

        valid_fields = total_fields - len(missing_deputy_id) - len(missing_deputy_uri) - len(missing_sq_candidato) - len(missing_active_flag)

        if missing_deputy_id:
            issues.append(f"❌ {len(missing_deputy_id)} politicians missing deputy_id")
        if missing_deputy_uri:
            issues.append(f"⚠️ {len(missing_deputy_uri)} politicians missing deputy_uri")
        if missing_sq_candidato:
            issues.append(f"⚠️ {len(missing_sq_candidato)} politicians missing sq_candidato_current")
        if missing_active_flag:
            issues.append(f"❌ {len(missing_active_flag)} politicians missing deputy_active flag")
        if tse_link_rate < 80:
            issues.append(f"⚠️ TSE linking rate: {tse_link_rate:.1f}% (expected >80%)")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'tse_link_rate': tse_link_rate,
            'issues': issues,
            'critical': True
        }

    def _validate_deputados_core_identity(self, politicians: List[Dict]):
        """Validate Deputados Core Identity fields - ALL FIELDS"""
        category = "Deputados Core Identity"
        issues = []

        # Check ALL deputados identity fields from DATA_POPULATION_GUIDE.md
        missing_nome_eleitoral = [p for p in politicians if not p.get('nome_eleitoral')]
        missing_url_foto = [p for p in politicians if not p.get('url_foto')]
        missing_death_date = [p for p in politicians if not p.get('death_date')]

        total_fields = len(politicians) * 3  # 3 deputados identity fields
        valid_fields = total_fields - len(missing_nome_eleitoral) - len(missing_url_foto)
        # data_falecimento is optional (most politicians are alive)

        if missing_nome_eleitoral:
            issues.append(f"⚠️ {len(missing_nome_eleitoral)} politicians missing nome_eleitoral")
        if missing_url_foto:
            issues.append(f"⚠️ {len(missing_url_foto)} politicians missing photo URL")

        # Report death date as info only (not penalizing)
        politicians_with_death_date = len(politicians) - len(missing_death_date)
        if politicians_with_death_date > 0:
            issues.append(f"ℹ️ {politicians_with_death_date} politicians have death date recorded")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }


    def _validate_current_political_status(self, politicians: List[Dict]):
        """Validate Current Political Status fields - ALL FIELDS"""
        category = "Current Political Status"
        issues = []

        # Check ALL current political status fields from DATA_POPULATION_GUIDE.md
        missing_party = [p for p in politicians if not p.get('current_party')]
        missing_party_id = [p for p in politicians if not p.get('current_party_id')]
        missing_state = [p for p in politicians if not p.get('current_state')]
        missing_legislature = [p for p in politicians if not p.get('current_legislature')]
        missing_situacao = [p for p in politicians if not p.get('situacao')]
        missing_condicao_eleitoral = [p for p in politicians if not p.get('condicao_eleitoral')]

        total_fields = len(politicians) * 6  # 6 political status fields
        valid_fields = total_fields - len(missing_party) - len(missing_party_id) - len(missing_state) - len(missing_legislature) - len(missing_situacao) - len(missing_condicao_eleitoral)

        if missing_party:
            issues.append(f"❌ {len(missing_party)} politicians missing current_party")
        if missing_party_id:
            issues.append(f"⚠️ {len(missing_party_id)} politicians missing current_party_id")
        if missing_state:
            issues.append(f"❌ {len(missing_state)} politicians missing current_state")
        if missing_legislature:
            issues.append(f"⚠️ {len(missing_legislature)} politicians missing current_legislature")
        if missing_situacao:
            issues.append(f"⚠️ {len(missing_situacao)} politicians missing situacao")
        if missing_condicao_eleitoral:
            issues.append(f"⚠️ {len(missing_condicao_eleitoral)} politicians missing condicao_eleitoral")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': True
        }



    def _validate_demographics(self, politicians: List[Dict]):
        """Validate Personal Demographics fields - EXACT 6 FIELDS FROM DATA_POPULATION_GUIDE.md"""
        category = "Personal Demographics"
        issues = []

        # Check ONLY the 6 demographic fields from DATA_POPULATION_GUIDE.md
        missing_birth_date = [p for p in politicians if not p.get('birth_date')]
        missing_death_date = [p for p in politicians if not p.get('death_date')]  # Usually null but should be in schema
        missing_gender = [p for p in politicians if not p.get('gender')]
        missing_gender_code = [p for p in politicians if not p.get('gender_code')]
        missing_birth_state = [p for p in politicians if not p.get('birth_state')]
        missing_birth_municipality = [p for p in politicians if not p.get('birth_municipality')]

        total_fields = len(politicians) * 6  # EXACTLY 6 demographic fields per DATA_POPULATION_GUIDE.md
        valid_fields = (total_fields - len(missing_birth_date) - len(missing_death_date) - len(missing_gender)
                       - len(missing_gender_code) - len(missing_birth_state) - len(missing_birth_municipality))

        if missing_birth_date:
            issues.append(f"⚠️ {len(missing_birth_date)} politicians missing birth_date")
        if missing_death_date:
            issues.append(f"ℹ️ {len(missing_death_date)} politicians missing death_date (expected - most are alive)")
        if missing_gender:
            issues.append(f"⚠️ {len(missing_gender)} politicians missing gender")
        if missing_gender_code:
            issues.append(f"⚠️ {len(missing_gender_code)} politicians missing gender_code")
        if missing_birth_state:
            issues.append(f"⚠️ {len(missing_birth_state)} politicians missing birth_state")
        if missing_birth_municipality:
            issues.append(f"⚠️ {len(missing_birth_municipality)} politicians missing birth_municipality")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_education_profession(self, politicians: List[Dict]):
        """Validate Education & Profession fields - EXACT 4 FIELDS FROM DATA_POPULATION_GUIDE.md"""
        category = "Education & Profession"
        issues = []

        # Check ONLY the 4 education & profession fields from DATA_POPULATION_GUIDE.md
        missing_education_level = [p for p in politicians if not p.get('education_level')]
        missing_education_code = [p for p in politicians if not p.get('education_code')]
        missing_occupation = [p for p in politicians if not p.get('occupation')]
        missing_occupation_code = [p for p in politicians if not p.get('occupation_code')]

        total_fields = len(politicians) * 4  # EXACTLY 4 education/profession fields per DATA_POPULATION_GUIDE.md
        valid_fields = total_fields - len(missing_education_level) - len(missing_education_code) - len(missing_occupation) - len(missing_occupation_code)

        if missing_education_level:
            issues.append(f"⚠️ {len(missing_education_level)} politicians missing education_level")
        if missing_education_code:
            issues.append(f"⚠️ {len(missing_education_code)} politicians missing education_code")
        if missing_occupation:
            issues.append(f"⚠️ {len(missing_occupation)} politicians missing occupation")
        if missing_occupation_code:
            issues.append(f"⚠️ {len(missing_occupation_code)} politicians missing occupation_code")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_electoral_information(self, politicians: List[Dict]):
        """Validate Electoral Information fields - EXACT 4 FIELDS FROM DATA_POPULATION_GUIDE.md"""
        category = "Electoral Information"
        issues = []

        # Check ONLY the 4 electoral information fields from DATA_POPULATION_GUIDE.md
        missing_nome_eleitoral = [p for p in politicians if not p.get('nome_eleitoral')]
        missing_electoral_number = [p for p in politicians if not p.get('electoral_number')]
        missing_nr_titulo_eleitoral = [p for p in politicians if not p.get('nr_titulo_eleitoral')]
        missing_nome_social_candidato = [p for p in politicians if not p.get('nome_social_candidato')]

        total_fields = len(politicians) * 4  # EXACTLY 4 electoral information fields per DATA_POPULATION_GUIDE.md
        valid_fields = total_fields - len(missing_nome_eleitoral) - len(missing_electoral_number) - len(missing_nr_titulo_eleitoral) - len(missing_nome_social_candidato)

        if missing_nome_eleitoral:
            issues.append(f"⚠️ {len(missing_nome_eleitoral)} politicians missing nome_eleitoral")
        if missing_electoral_number:
            issues.append(f"⚠️ {len(missing_electoral_number)} politicians missing electoral_number")
        if missing_nr_titulo_eleitoral:
            issues.append(f"⚠️ {len(missing_nr_titulo_eleitoral)} politicians missing nr_titulo_eleitoral")
        if missing_nome_social_candidato:
            issues.append(f"⚠️ {len(missing_nome_social_candidato)} politicians missing nome_social_candidato")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_system_metadata(self, politicians: List[Dict]):
        """Validate System Metadata fields - EXACT 2 FIELDS FROM DATA_POPULATION_GUIDE.md"""
        category = "System Metadata"
        issues = []

        # Check ONLY the 2 system metadata fields from DATA_POPULATION_GUIDE.md
        missing_created_at = [p for p in politicians if not p.get('created_at')]
        missing_updated_at = [p for p in politicians if not p.get('updated_at')]

        total_fields = len(politicians) * 2  # EXACTLY 2 system metadata fields per DATA_POPULATION_GUIDE.md
        valid_fields = total_fields - len(missing_created_at) - len(missing_updated_at)

        if missing_created_at:
            issues.append(f"⚠️ {len(missing_created_at)} politicians missing created_at")
        if missing_updated_at:
            issues.append(f"⚠️ {len(missing_updated_at)} politicians missing updated_at")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }


    def _validate_contact_information(self, politicians: List[Dict]):
        """Validate Contact Information - EXACT 3 FIELDS FROM DATA_POPULATION_GUIDE.md"""
        category = "Contact Information"
        issues = []

        # Check ONLY the 3 contact fields from DATA_POPULATION_GUIDE.md: email, website, url_foto
        missing_email = [p for p in politicians if not p.get('email')]
        missing_website = [p for p in politicians if not p.get('website')]
        missing_url_foto = [p for p in politicians if not p.get('url_foto')]

        total_fields = len(politicians) * 3  # EXACTLY 3 contact fields per DATA_POPULATION_GUIDE.md
        valid_fields = total_fields - len(missing_email) - len(missing_website) - len(missing_url_foto)

        if missing_email:
            issues.append(f"⚠️ {len(missing_email)} politicians missing email")
        if missing_website:
            issues.append(f"⚠️ {len(missing_website)} politicians missing website")
        if missing_url_foto:
            issues.append(f"⚠️ {len(missing_url_foto)} politicians missing url_foto")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_office_details(self, politicians: List[Dict]):
        """Validate Office Details - ALL FIELDS"""
        category = "Office Details"
        issues = []

        # Check ALL office detail fields from DATA_POPULATION_GUIDE.md
        missing_office_building = [p for p in politicians if not p.get('office_building')]
        missing_office_room = [p for p in politicians if not p.get('office_room')]
        missing_office_floor = [p for p in politicians if not p.get('office_floor')]
        missing_office_phone = [p for p in politicians if not p.get('office_phone')]
        missing_office_email = [p for p in politicians if not p.get('office_email')]

        total_fields = len(politicians) * 5  # 5 office fields
        valid_fields = total_fields - len(missing_office_building) - len(missing_office_room) - len(missing_office_floor) - len(missing_office_phone) - len(missing_office_email)

        if missing_office_building:
            issues.append(f"⚠️ {len(missing_office_building)} politicians missing office_building")
        if missing_office_room:
            issues.append(f"⚠️ {len(missing_office_room)} politicians missing office_room")
        if missing_office_floor:
            issues.append(f"⚠️ {len(missing_office_floor)} politicians missing office_floor")
        if missing_office_phone:
            issues.append(f"⚠️ {len(missing_office_phone)} politicians missing office_phone")
        if missing_office_email:
            issues.append(f"⚠️ {len(missing_office_email)} politicians missing office_email")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_career_timeline(self, politicians: List[Dict]):
        """Validate Career Timeline fields - EXACT 3 FIELDS FROM DATA_POPULATION_GUIDE.md"""
        category = "Career Timeline"
        issues = []

        # Check ONLY the 3 career timeline fields from DATA_POPULATION_GUIDE.md
        missing_first_election_year = [p for p in politicians if not p.get('first_election_year')]
        missing_last_election_year = [p for p in politicians if not p.get('last_election_year')]
        missing_number_of_elections = [p for p in politicians if not p.get('number_of_elections')]

        total_fields = len(politicians) * 3  # EXACTLY 3 career timeline fields per DATA_POPULATION_GUIDE.md
        valid_fields = total_fields - len(missing_first_election_year) - len(missing_last_election_year) - len(missing_number_of_elections)

        if missing_first_election_year:
            issues.append(f"⚠️ {len(missing_first_election_year)} politicians missing first_election_year")
        if missing_last_election_year:
            issues.append(f"⚠️ {len(missing_last_election_year)} politicians missing last_election_year")
        if missing_number_of_elections:
            issues.append(f"⚠️ {len(missing_number_of_elections)} politicians missing number_of_elections")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_tse_correlation_metadata(self, politicians: List[Dict]):
        """Validate TSE Correlation Metadata fields - ALL FIELDS"""
        category = "TSE Correlation Metadata"
        issues = []

        tse_linked = [p for p in politicians if p.get('tse_linked')]

        if not tse_linked:
            self.validation_results['validation_categories'][category] = {
                'completion_rate': 0,
                'issues': ["⚠️ No TSE-linked politicians for correlation metadata validation"],
                'critical': False
            }
            return

        # Check ALL TSE correlation metadata fields from DATA_POPULATION_GUIDE.md
        missing_correlation_confidence = [p for p in tse_linked if not p.get('tse_correlation_confidence')]
        missing_electoral_success_rate = [p for p in tse_linked if not p.get('electoral_success_rate')]

        total_fields = len(tse_linked) * 2  # 2 TSE correlation metadata fields
        valid_fields = total_fields - len(missing_correlation_confidence) - len(missing_electoral_success_rate)

        if missing_correlation_confidence:
            issues.append(f"⚠️ {len(missing_correlation_confidence)} TSE-linked politicians missing tse_correlation_confidence")
        if missing_electoral_success_rate:
            issues.append(f"⚠️ {len(missing_electoral_success_rate)} TSE-linked politicians missing electoral_success_rate")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_validation_flags(self, politicians: List[Dict]):
        """Validate TSE Linked Flag - EXACT 1 FIELD FROM DATA_POPULATION_GUIDE.md"""
        category = "TSE Linked Flag"
        issues = []

        # Check ONLY the tse_linked field from DATA_POPULATION_GUIDE.md
        missing_tse_linked = [p for p in politicians if p.get('tse_linked') is None]

        total_fields = len(politicians) * 1  # EXACTLY 1 validation field per DATA_POPULATION_GUIDE.md
        valid_fields = total_fields - len(missing_tse_linked)

        if missing_tse_linked:
            issues.append(f"❌ {len(missing_tse_linked)} politicians missing tse_linked flag")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': True
        }

    def _calculate_compliance_score(self):
        """Calculate overall compliance score"""
        total_categories = len(self.validation_results['validation_categories'])

        if total_categories == 0:
            self.validation_results['compliance_score'] = 0.0
            return

        # Weight critical categories more heavily
        total_score = 0
        total_weight = 0

        for category, data in self.validation_results['validation_categories'].items():
            weight = 2 if data.get('critical', False) else 1
            total_score += data['completion_rate'] * weight
            total_weight += weight

        self.validation_results['compliance_score'] = total_score / total_weight if total_weight > 0 else 0

    def _print_validation_summary(self):
        """Print comprehensive validation summary"""
        print(f"\n📊 VALIDATION SUMMARY")
        print("=" * 60)

        for category, data in self.validation_results['validation_categories'].items():
            critical_mark = "🔴" if data.get('critical', False) else "🟡"
            completion = data['completion_rate']

            if completion >= 90:
                status_emoji = "✅"
            elif completion >= 70:
                status_emoji = "⚠️"
            else:
                status_emoji = "❌"

            print(f"{critical_mark} {status_emoji} {category}: {completion:.1f}%")

            for issue in data['issues']:
                print(f"    {issue}")

            # Special metrics
            if 'tse_link_rate' in data:
                print(f"    🔗 TSE Link Rate: {data['tse_link_rate']:.1f}%")
            if 'tse_linked_count' in data:
                print(f"    👥 TSE Linked Politicians: {data['tse_linked_count']}")

        print("=" * 60)
        print(f"🎯 OVERALL COMPLIANCE SCORE: {self.validation_results['compliance_score']:.1f}%")

        if self.validation_results['compliance_score'] >= 90:
            print("🏆 EXCELLENT - DATA_POPULATION_GUIDE.md compliance")
        elif self.validation_results['compliance_score'] >= 70:
            print("👍 GOOD - Minor improvements needed")
        else:
            print("⚠️ NEEDS IMPROVEMENT - Significant gaps in field coverage")

        print("=" * 60)

        return self.validation_results

    def export_results(self, filepath: str, results: Dict[str, Any]):
        """Export validation results to file"""
        import json
        import csv
        from pathlib import Path

        if filepath.endswith('.json'):
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        elif filepath.endswith('.csv'):
            # Create summary CSV
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Category', 'Score', 'Status', 'Issues'])
                for category, data in results['summary'].items():
                    status = "✅" if data['score'] == 100 else "⚠️" if data['score'] >= 80 else "❌"
                    issues = "; ".join(data.get('issues', []))
                    writer.writerow([category, f"{data['score']:.1f}%", status, issues])
        else:
            # Default to JSON
            filepath += '.json'
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)