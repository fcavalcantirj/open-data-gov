"""
CLI4 Parties Validator
Comprehensive validation for political parties and memberships data
"""

from typing import Dict, List, Any, Optional
from cli4.modules import database


class CLI4PartiesValidator:
    """Comprehensive parties and memberships data validation"""

    def __init__(self):
        self.validation_results = {
            'total_parties': 0,
            'total_memberships': 0,
            'validation_categories': {},
            'critical_issues': [],
            'warnings': [],
            'summary': {},
            'compliance_score': 0.0
        }

    def validate_all_parties(self, limit: Optional[int] = None, detailed: bool = False) -> Dict[str, Any]:
        """Run comprehensive validation on all party records"""
        print("🔍 COMPREHENSIVE PARTIES VALIDATION")
        print("=" * 60)
        print("Validating political_parties and party_memberships tables")
        print("=" * 60)

        # Get parties with optional limit
        parties_query = "SELECT * FROM political_parties"
        if limit:
            parties_query += f" LIMIT {limit}"

        parties = database.execute_query(parties_query)
        self.validation_results['total_parties'] = len(parties)

        # Get memberships
        memberships_query = "SELECT * FROM party_memberships"
        if limit:
            memberships_query += f" LIMIT {limit * 50}"  # Assume avg 50 members per party

        memberships = database.execute_query(memberships_query)
        self.validation_results['total_memberships'] = len(memberships)

        if not parties:
            print("⚠️ No parties found in database")
            return self.validation_results

        limit_text = f" (limited to {limit})" if limit else ""
        print(f"📊 Validating {len(parties)} party records{limit_text}...")
        print(f"📊 Validating {len(memberships)} membership records...")

        # Run validation categories
        self._validate_party_core_fields(parties)
        self._validate_party_leadership(parties)
        self._validate_party_statistics(parties)
        self._validate_party_metadata(parties)
        self._validate_membership_relationships(memberships)
        self._validate_data_consistency(parties, memberships)

        # Calculate compliance score
        self._calculate_compliance_score()

        # Print results
        self._print_validation_summary()

        return self.validation_results

    def _validate_party_core_fields(self, parties: List[Dict]):
        """Validate core party identification fields"""
        category = "Party Core Fields"
        issues = []
        total_fields = len(parties) * 4  # 4 core fields

        # Required fields validation
        missing_id = [p for p in parties if not p.get('id')]
        missing_nome = [p for p in parties if not p.get('nome')]
        missing_sigla = [p for p in parties if not p.get('sigla')]
        missing_status = [p for p in parties if not p.get('status')]

        # Sigla format validation (should be uppercase, 2-10 chars)
        invalid_sigla = [p for p in parties if p.get('sigla') and (
            len(p['sigla']) < 2 or len(p['sigla']) > 10 or not p['sigla'].isupper()
        )]

        valid_fields = total_fields - len(missing_id) - len(missing_nome) - len(missing_sigla) - len(missing_status)

        if missing_id:
            issues.append(f"❌ {len(missing_id)} parties missing id")
        if missing_nome:
            issues.append(f"❌ {len(missing_nome)} parties missing nome")
        if missing_sigla:
            issues.append(f"❌ {len(missing_sigla)} parties missing sigla")
        if missing_status:
            issues.append(f"⚠️ {len(missing_status)} parties missing status")
        if invalid_sigla:
            issues.append(f"⚠️ {len(invalid_sigla)} parties with invalid sigla format")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': True
        }

    def _validate_party_leadership(self, parties: List[Dict]):
        """Validate party leadership information"""
        category = "Party Leadership"
        issues = []
        total_fields = len(parties) * 4  # 4 leadership fields

        missing_lider = [p for p in parties if not p.get('lider_atual')]
        missing_lider_id = [p for p in parties if not p.get('lider_id')]
        missing_lider_estado = [p for p in parties if not p.get('lider_estado')]
        missing_lider_legislatura = [p for p in parties if not p.get('lider_legislatura')]

        # Count parties with complete leadership info
        complete_leadership = [p for p in parties if all([
            p.get('lider_atual'), p.get('lider_id'), p.get('lider_estado'), p.get('lider_legislatura')
        ])]

        leadership_completeness = (len(complete_leadership) / len(parties)) * 100

        valid_fields = total_fields - len(missing_lider) - len(missing_lider_id) - len(missing_lider_estado) - len(missing_lider_legislatura)

        if missing_lider:
            issues.append(f"⚠️ {len(missing_lider)} parties missing lider_atual")
        if missing_lider_id:
            issues.append(f"⚠️ {len(missing_lider_id)} parties missing lider_id")
        if missing_lider_estado:
            issues.append(f"⚠️ {len(missing_lider_estado)} parties missing lider_estado")
        if missing_lider_legislatura:
            issues.append(f"⚠️ {len(missing_lider_legislatura)} parties missing lider_legislatura")

        issues.append(f"ℹ️ {leadership_completeness:.1f}% parties have complete leadership info")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'leadership_completeness': leadership_completeness,
            'issues': issues,
            'critical': False
        }

    def _validate_party_statistics(self, parties: List[Dict]):
        """Validate party membership statistics"""
        category = "Party Statistics"
        issues = []

        # Validate member counts
        negative_membros = [p for p in parties if p.get('total_membros', 0) < 0]
        negative_efetivos = [p for p in parties if p.get('total_efetivos', 0) < 0]
        zero_members = [p for p in parties if p.get('total_membros', 0) == 0]

        # Check for unrealistic member counts (> 600 deputies total)
        excessive_members = [p for p in parties if p.get('total_membros', 0) > 600]

        # Statistics summary
        total_members = sum(p.get('total_membros', 0) for p in parties)
        avg_members = total_members / len(parties) if parties else 0

        if negative_membros:
            issues.append(f"❌ {len(negative_membros)} parties with negative total_membros")
        if negative_efetivos:
            issues.append(f"❌ {len(negative_efetivos)} parties with negative total_efetivos")
        if zero_members:
            issues.append(f"⚠️ {len(zero_members)} parties with zero members")
        if excessive_members:
            issues.append(f"⚠️ {len(excessive_members)} parties with >600 members (suspicious)")

        issues.append(f"ℹ️ Total members across all parties: {total_members}")
        issues.append(f"ℹ️ Average members per party: {avg_members:.1f}")

        # Completion rate based on reasonable statistics
        valid_stats = len(parties) - len(negative_membros) - len(negative_efetivos) - len(excessive_members)
        completion_rate = (valid_stats / len(parties)) * 100

        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'total_members': total_members,
            'avg_members': avg_members,
            'issues': issues,
            'critical': False
        }

    def _validate_party_metadata(self, parties: List[Dict]):
        """Validate party metadata and URLs"""
        category = "Party Metadata"
        issues = []
        total_fields = len(parties) * 3  # 3 metadata fields

        missing_created_at = [p for p in parties if not p.get('created_at')]
        missing_updated_at = [p for p in parties if not p.get('updated_at')]
        missing_legislatura = [p for p in parties if not p.get('legislatura_id')]

        # URL validation
        parties_with_logo = [p for p in parties if p.get('logo_url')]
        parties_with_members_uri = [p for p in parties if p.get('uri_membros')]

        valid_fields = total_fields - len(missing_created_at) - len(missing_updated_at) - len(missing_legislatura)

        if missing_created_at:
            issues.append(f"⚠️ {len(missing_created_at)} parties missing created_at")
        if missing_updated_at:
            issues.append(f"⚠️ {len(missing_updated_at)} parties missing updated_at")
        if missing_legislatura:
            issues.append(f"❌ {len(missing_legislatura)} parties missing legislatura_id")

        logo_percentage = (len(parties_with_logo) / len(parties)) * 100
        uri_percentage = (len(parties_with_members_uri) / len(parties)) * 100

        issues.append(f"ℹ️ {logo_percentage:.1f}% parties have logo URL")
        issues.append(f"ℹ️ {uri_percentage:.1f}% parties have members URI")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'logo_percentage': logo_percentage,
            'uri_percentage': uri_percentage,
            'issues': issues,
            'critical': True
        }

    def _validate_membership_relationships(self, memberships: List[Dict]):
        """Validate party membership relationships"""
        category = "Party Memberships"
        issues = []

        if not memberships:
            self.validation_results['validation_categories'][category] = {
                'completion_rate': 0,
                'issues': ["⚠️ No party memberships found"],
                'critical': True
            }
            return

        total_fields = len(memberships) * 4  # 4 core membership fields

        # Required fields validation
        missing_party_id = [m for m in memberships if not m.get('party_id')]
        missing_deputy_id = [m for m in memberships if not m.get('deputy_id')]
        missing_deputy_name = [m for m in memberships if not m.get('deputy_name')]
        missing_legislatura = [m for m in memberships if not m.get('legislatura_id')]

        # Relationship validation - check if referenced parties exist
        unique_party_ids = set(m.get('party_id') for m in memberships if m.get('party_id'))
        party_check_query = f"SELECT id FROM political_parties WHERE id IN ({','.join(map(str, unique_party_ids))})"
        existing_parties = database.execute_query(party_check_query) if unique_party_ids else []
        existing_party_ids = set(p['id'] for p in existing_parties) if existing_parties else set()

        orphaned_memberships = [m for m in memberships if m.get('party_id') not in existing_party_ids]

        valid_fields = total_fields - len(missing_party_id) - len(missing_deputy_id) - len(missing_deputy_name) - len(missing_legislatura)

        if missing_party_id:
            issues.append(f"❌ {len(missing_party_id)} memberships missing party_id")
        if missing_deputy_id:
            issues.append(f"❌ {len(missing_deputy_id)} memberships missing deputy_id")
        if missing_deputy_name:
            issues.append(f"⚠️ {len(missing_deputy_name)} memberships missing deputy_name")
        if missing_legislatura:
            issues.append(f"⚠️ {len(missing_legislatura)} memberships missing legislatura_id")
        if orphaned_memberships:
            issues.append(f"❌ {len(orphaned_memberships)} memberships reference non-existent parties")

        # Statistics
        unique_deputies = len(set(m.get('deputy_id') for m in memberships if m.get('deputy_id')))
        issues.append(f"ℹ️ {unique_deputies} unique deputies in memberships")
        issues.append(f"ℹ️ {len(unique_party_ids)} unique parties have members")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'unique_deputies': unique_deputies,
            'unique_parties': len(unique_party_ids),
            'orphaned_memberships': len(orphaned_memberships),
            'issues': issues,
            'critical': True
        }

    def _validate_data_consistency(self, parties: List[Dict], memberships: List[Dict]):
        """Validate consistency between parties and memberships"""
        category = "Data Consistency"
        issues = []

        # Check if party member counts match actual memberships
        membership_counts = {}
        for membership in memberships:
            party_id = membership.get('party_id')
            if party_id:
                membership_counts[party_id] = membership_counts.get(party_id, 0) + 1

        count_mismatches = []
        for party in parties:
            party_id = party.get('id')
            declared_count = party.get('total_membros', 0)
            actual_count = membership_counts.get(party_id, 0)

            if declared_count != actual_count:
                count_mismatches.append({
                    'party_id': party_id,
                    'party_name': party.get('nome'),
                    'declared': declared_count,
                    'actual': actual_count
                })

        # Check for duplicate memberships (same deputy in same party/legislature)
        membership_keys = []
        for membership in memberships:
            key = (membership.get('party_id'), membership.get('deputy_id'), membership.get('legislatura_id'))
            membership_keys.append(key)

        duplicate_memberships = len(membership_keys) - len(set(membership_keys))

        if count_mismatches:
            issues.append(f"⚠️ {len(count_mismatches)} parties have member count mismatches")
            if len(count_mismatches) <= 5:  # Show details for small numbers
                for mismatch in count_mismatches:
                    issues.append(f"    {mismatch['party_name']}: declared {mismatch['declared']}, actual {mismatch['actual']}")

        if duplicate_memberships > 0:
            issues.append(f"❌ {duplicate_memberships} duplicate membership records")

        # Calculate consistency score
        total_parties = len(parties)
        consistent_parties = total_parties - len(count_mismatches)
        consistency_rate = (consistent_parties / total_parties) * 100 if total_parties > 0 else 100

        self.validation_results['validation_categories'][category] = {
            'completion_rate': consistency_rate,
            'count_mismatches': len(count_mismatches),
            'duplicate_memberships': duplicate_memberships,
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
        print(f"\n📊 PARTIES VALIDATION SUMMARY")
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
            if 'leadership_completeness' in data:
                print(f"    👑 Leadership Info: {data['leadership_completeness']:.1f}%")
            if 'total_members' in data:
                print(f"    👥 Total Members: {data['total_members']}")

        print("=" * 60)
        print(f"🎯 OVERALL COMPLIANCE SCORE: {self.validation_results['compliance_score']:.1f}%")

        if self.validation_results['compliance_score'] >= 90:
            print("🏆 EXCELLENT - High quality parties data")
        elif self.validation_results['compliance_score'] >= 70:
            print("👍 GOOD - Minor improvements needed")
        else:
            print("⚠️ NEEDS IMPROVEMENT - Significant data quality issues")

        print("=" * 60)

        return self.validation_results


def main():
    """Standalone test of parties validator"""
    print("🧪 TESTING PARTIES VALIDATOR")
    print("=" * 50)

    validator = CLI4PartiesValidator()
    results = validator.validate_all_parties(limit=10)

    print(f"\n🎯 Validation completed")
    print(f"Parties validated: {results['total_parties']}")
    print(f"Memberships validated: {results['total_memberships']}")
    print(f"Compliance score: {results['compliance_score']:.1f}%")


if __name__ == "__main__":
    main()