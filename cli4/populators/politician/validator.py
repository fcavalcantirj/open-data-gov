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

        # Run validation categories
        self._validate_universal_identifiers(politicians)
        self._validate_source_system_links(politicians)
        self._validate_deputados_core_identity(politicians)
        self._validate_tse_core_identity(politicians)
        self._validate_current_political_status(politicians)
        self._validate_tse_political_details(politicians)
        self._validate_tse_electoral_status(politicians)
        self._validate_demographics(politicians)
        self._validate_geographic_details(politicians)
        self._validate_contact_information(politicians)
        self._validate_office_details(politicians)
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
        total_fields = len(politicians) * 3  # 3 required fields

        # CPF validation
        missing_cpf = [p for p in politicians if not p.get('cpf')]
        invalid_cpf_length = [p for p in politicians if p.get('cpf') and len(str(p['cpf'])) != 11]

        # Nome Civil validation
        missing_nome_civil = [p for p in politicians if not p.get('nome_civil')]

        # Normalized name validation
        missing_normalized = [p for p in politicians if not p.get('nome_completo_normalizado')]

        valid_fields = total_fields - len(missing_cpf) - len(invalid_cpf_length) - len(missing_nome_civil) - len(missing_normalized)

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
        total_fields = len(politicians) * 3

        missing_deputy_id = [p for p in politicians if not p.get('deputy_id')]
        missing_active_flag = [p for p in politicians if p.get('deputy_active') is None]

        # TSE linking rate
        tse_linked_count = len([p for p in politicians if p.get('tse_linked')])
        tse_link_rate = (tse_linked_count / len(politicians)) * 100

        valid_fields = total_fields - len(missing_deputy_id) - len(missing_active_flag)

        if missing_deputy_id:
            issues.append(f"❌ {len(missing_deputy_id)} politicians missing deputy_id")
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
        """Validate Deputados Core Identity fields"""
        category = "Deputados Core Identity"
        issues = []

        # Check key identity fields
        missing_nome_eleitoral = [p for p in politicians if not p.get('nome_eleitoral')]
        missing_url_foto = [p for p in politicians if not p.get('url_foto')]

        total_fields = len(politicians) * 3  # 3 core identity fields
        valid_fields = total_fields - len(missing_nome_eleitoral) - len(missing_url_foto)

        if missing_nome_eleitoral:
            issues.append(f"⚠️ {len(missing_nome_eleitoral)} politicians missing nome_eleitoral")
        if missing_url_foto:
            issues.append(f"⚠️ {len(missing_url_foto)} politicians missing photo URL")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_tse_core_identity(self, politicians: List[Dict]):
        """Validate TSE Core Identity fields"""
        category = "TSE Core Identity"
        issues = []

        tse_linked = [p for p in politicians if p.get('tse_linked')]

        if not tse_linked:
            self.validation_results['validation_categories'][category] = {
                'completion_rate': 0,
                'issues': ["⚠️ No TSE-linked politicians found"],
                'critical': False
            }
            return

        # Check TSE-specific fields for linked politicians
        missing_electoral_number = [p for p in tse_linked if not p.get('electoral_number')]
        missing_nome_urna = [p for p in tse_linked if not p.get('nome_urna_candidato')]
        missing_titulo_eleitoral = [p for p in tse_linked if not p.get('nr_titulo_eleitoral')]

        total_fields = len(tse_linked) * 4  # 4 TSE identity fields
        valid_fields = total_fields - len(missing_electoral_number) - len(missing_nome_urna) - len(missing_titulo_eleitoral)

        if missing_electoral_number:
            issues.append(f"⚠️ {len(missing_electoral_number)} TSE-linked politicians missing electoral number")
        if missing_nome_urna:
            issues.append(f"⚠️ {len(missing_nome_urna)} TSE-linked politicians missing nome_urna")
        if missing_titulo_eleitoral:
            issues.append(f"⚠️ {len(missing_titulo_eleitoral)} TSE-linked politicians missing título eleitoral")

        completion_rate = (valid_fields / total_fields) * 100 if total_fields > 0 else 0
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'tse_linked_count': len(tse_linked),
            'issues': issues,
            'critical': False
        }

    def _validate_current_political_status(self, politicians: List[Dict]):
        """Validate Current Political Status fields"""
        category = "Current Political Status"
        issues = []

        missing_party = [p for p in politicians if not p.get('current_party')]
        missing_state = [p for p in politicians if not p.get('current_state')]
        missing_legislature = [p for p in politicians if not p.get('current_legislature')]
        missing_situacao = [p for p in politicians if not p.get('situacao')]

        total_fields = len(politicians) * 5  # 5 political status fields
        valid_fields = total_fields - len(missing_party) - len(missing_state) - len(missing_legislature) - len(missing_situacao)

        if missing_party:
            issues.append(f"❌ {len(missing_party)} politicians missing current_party")
        if missing_state:
            issues.append(f"❌ {len(missing_state)} politicians missing current_state")
        if missing_legislature:
            issues.append(f"⚠️ {len(missing_legislature)} politicians missing current_legislature")
        if missing_situacao:
            issues.append(f"⚠️ {len(missing_situacao)} politicians missing situacao")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': True
        }

    def _validate_tse_political_details(self, politicians: List[Dict]):
        """Validate TSE Political Details"""
        category = "TSE Political Details"
        issues = []

        tse_linked = [p for p in politicians if p.get('tse_linked')]

        if not tse_linked:
            self.validation_results['validation_categories'][category] = {
                'completion_rate': 0,
                'issues': ["⚠️ No TSE-linked politicians for political details validation"],
                'critical': False
            }
            return

        missing_nr_partido = [p for p in tse_linked if not p.get('nr_partido')]
        missing_nm_partido = [p for p in tse_linked if not p.get('nm_partido')]
        missing_current_position = [p for p in tse_linked if not p.get('current_position')]

        total_fields = len(tse_linked) * 5  # 5 TSE political fields
        valid_fields = total_fields - len(missing_nr_partido) - len(missing_nm_partido) - len(missing_current_position)

        if missing_nr_partido:
            issues.append(f"⚠️ {len(missing_nr_partido)} TSE-linked politicians missing party number")
        if missing_nm_partido:
            issues.append(f"⚠️ {len(missing_nm_partido)} TSE-linked politicians missing party name")
        if missing_current_position:
            issues.append(f"⚠️ {len(missing_current_position)} TSE-linked politicians missing position")

        completion_rate = (valid_fields / total_fields) * 100 if total_fields > 0 else 0
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_tse_electoral_status(self, politicians: List[Dict]):
        """Validate TSE Electoral Status"""
        category = "TSE Electoral Status"
        issues = []

        tse_linked = [p for p in politicians if p.get('tse_linked')]

        if not tse_linked:
            self.validation_results['validation_categories'][category] = {
                'completion_rate': 0,
                'issues': ["⚠️ No TSE-linked politicians for electoral status validation"],
                'critical': False
            }
            return

        missing_situacao_candidatura = [p for p in tse_linked if not p.get('cd_situacao_candidatura')]
        missing_sit_tot_turno = [p for p in tse_linked if not p.get('cd_sit_tot_turno')]

        total_fields = len(tse_linked) * 4  # 4 electoral status fields
        valid_fields = total_fields - len(missing_situacao_candidatura) - len(missing_sit_tot_turno)

        if missing_situacao_candidatura:
            issues.append(f"⚠️ {len(missing_situacao_candidatura)} TSE-linked politicians missing candidatura status")
        if missing_sit_tot_turno:
            issues.append(f"⚠️ {len(missing_sit_tot_turno)} TSE-linked politicians missing turno status")

        completion_rate = (valid_fields / total_fields) * 100 if total_fields > 0 else 0
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_demographics(self, politicians: List[Dict]):
        """Validate Demographics fields"""
        category = "Demographics"
        issues = []

        missing_birth_date = [p for p in politicians if not p.get('birth_date')]
        missing_gender = [p for p in politicians if not p.get('gender')]
        missing_education = [p for p in politicians if not p.get('education_level')]

        total_fields = len(politicians) * 15  # 15 demographic fields
        valid_fields = total_fields - len(missing_birth_date) - len(missing_gender) - len(missing_education)

        if missing_birth_date:
            issues.append(f"⚠️ {len(missing_birth_date)} politicians missing birth_date")
        if missing_gender:
            issues.append(f"⚠️ {len(missing_gender)} politicians missing gender")
        if missing_education:
            issues.append(f"⚠️ {len(missing_education)} politicians missing education_level")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_geographic_details(self, politicians: List[Dict]):
        """Validate Geographic Details"""
        category = "Geographic Details"
        issues = []

        missing_birth_state = [p for p in politicians if not p.get('birth_state')]
        missing_birth_municipality = [p for p in politicians if not p.get('birth_municipality')]

        total_fields = len(politicians) * 4  # 4 geographic fields
        valid_fields = total_fields - len(missing_birth_state) - len(missing_birth_municipality)

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

    def _validate_contact_information(self, politicians: List[Dict]):
        """Validate Contact Information"""
        category = "Contact Information"
        issues = []

        missing_email = [p for p in politicians if not p.get('email')]
        missing_phone = [p for p in politicians if not p.get('phone')]
        missing_website = [p for p in politicians if not p.get('website')]

        total_fields = len(politicians) * 5  # 5 contact fields
        valid_fields = total_fields - len(missing_email) - len(missing_phone) - len(missing_website)

        if missing_email:
            issues.append(f"⚠️ {len(missing_email)} politicians missing email")
        if missing_phone:
            issues.append(f"⚠️ {len(missing_phone)} politicians missing phone")
        if missing_website:
            issues.append(f"⚠️ {len(missing_website)} politicians missing website")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_office_details(self, politicians: List[Dict]):
        """Validate Office Details"""
        category = "Office Details"
        issues = []

        missing_office_building = [p for p in politicians if not p.get('office_building')]
        missing_office_room = [p for p in politicians if not p.get('office_room')]
        missing_office_phone = [p for p in politicians if not p.get('office_phone')]

        total_fields = len(politicians) * 5  # 5 office fields
        valid_fields = total_fields - len(missing_office_building) - len(missing_office_room) - len(missing_office_phone)

        if missing_office_building:
            issues.append(f"⚠️ {len(missing_office_building)} politicians missing office_building")
        if missing_office_room:
            issues.append(f"⚠️ {len(missing_office_room)} politicians missing office_room")
        if missing_office_phone:
            issues.append(f"⚠️ {len(missing_office_phone)} politicians missing office_phone")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_validation_flags(self, politicians: List[Dict]):
        """Validate Validation Flags"""
        category = "Validation Flags"
        issues = []

        missing_cpf_validated = [p for p in politicians if p.get('cpf_validated') is None]
        missing_tse_linked = [p for p in politicians if p.get('tse_linked') is None]
        missing_last_updated = [p for p in politicians if not p.get('last_updated_date')]

        total_fields = len(politicians) * 3  # 3 validation fields
        valid_fields = total_fields - len(missing_cpf_validated) - len(missing_tse_linked) - len(missing_last_updated)

        if missing_cpf_validated:
            issues.append(f"❌ {len(missing_cpf_validated)} politicians missing cpf_validated flag")
        if missing_tse_linked:
            issues.append(f"❌ {len(missing_tse_linked)} politicians missing tse_linked flag")
        if missing_last_updated:
            issues.append(f"❌ {len(missing_last_updated)} politicians missing last_updated_date")

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