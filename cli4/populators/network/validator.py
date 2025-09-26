"""
CLI4 Network Validator
Comprehensive validation for unified_political_networks table
"""

from typing import Dict, List, Any, Optional
from cli4.modules import database


class NetworkValidator:
    """Comprehensive network data validation following CLI4 patterns"""

    def __init__(self):
        self.validation_results = {
            'total_networks': 0,
            'validation_categories': {},
            'critical_issues': [],
            'warnings': [],
            'compliance_score': 0.0
        }

    def validate_all_networks(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive validation on all network records"""
        print("🤝 COMPREHENSIVE NETWORK VALIDATION")
        print("=" * 60)
        print("Political network memberships data quality assessment")
        print()

        # Get network records
        query = "SELECT * FROM unified_political_networks"
        if limit:
            query += f" LIMIT {limit}"

        networks = database.execute_query(query)
        self.validation_results['total_networks'] = len(networks)

        if not networks:
            print("⚠️ No network records found in database")
            return self.validation_results

        limit_text = f" (limited to {limit})" if limit else ""
        print(f"📊 Validating {len(networks)} network records{limit_text}...")
        print()

        # Run validation categories
        self._validate_core_identifiers(networks)
        self._validate_network_details(networks)
        self._validate_membership_details(networks)
        self._validate_source_tracking(networks)
        self._validate_data_quality(networks)
        self._validate_network_distribution(networks)
        self._validate_politician_references(networks)

        # Calculate compliance score
        self._calculate_compliance_score()

        # Print results
        self._print_validation_summary()

        return self.validation_results

    def _validate_core_identifiers(self, networks: List[Dict]):
        """Validate core identifier fields"""
        category = "Core Identifiers"
        issues = []
        total_fields = len(networks) * 4

        missing_politician_id = [n for n in networks if not n.get('politician_id')]
        missing_network_type = [n for n in networks if not n.get('network_type')]
        missing_network_id = [n for n in networks if not n.get('network_id')]
        missing_network_name = [n for n in networks if not n.get('network_name')]

        # Validate network types
        valid_types = {'COMMITTEE', 'PARLIAMENTARY_FRONT', 'COALITION', 'FEDERATION', 'PARTY'}
        invalid_types = [n for n in networks if n.get('network_type') not in valid_types]

        valid_fields = total_fields - len(missing_politician_id) - len(missing_network_type) - len(missing_network_id) - len(missing_network_name)

        if missing_politician_id:
            issues.append(f"❌ {len(missing_politician_id)} records missing politician_id")
        if missing_network_type:
            issues.append(f"❌ {len(missing_network_type)} records missing network_type")
        if missing_network_id:
            issues.append(f"❌ {len(missing_network_id)} records missing network_id")
        if missing_network_name:
            issues.append(f"❌ {len(missing_network_name)} records missing network_name")
        if invalid_types:
            issues.append(f"❌ {len(invalid_types)} records with invalid network_type")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': True
        }

    def _validate_network_details(self, networks: List[Dict]):
        """Validate network detail fields"""
        category = "Network Details"
        issues = []

        # Check network type distribution
        type_counts = {}
        for network in networks:
            network_type = network.get('network_type')
            type_counts[network_type] = type_counts.get(network_type, 0) + 1

        # Report distribution
        total = len(networks)
        for net_type, count in type_counts.items():
            percentage = (count / total) * 100
            issues.append(f"ℹ️ {net_type}: {count} records ({percentage:.1f}%)")

        # Check for reasonable network name lengths
        short_names = [n for n in networks if n.get('network_name') and len(n['network_name']) < 10]
        long_names = [n for n in networks if n.get('network_name') and len(n['network_name']) > 200]

        if short_names:
            issues.append(f"⚠️ {len(short_names)} records with very short network names")
        if long_names:
            issues.append(f"⚠️ {len(long_names)} records with very long network names")

        completion_rate = 100.0  # Network details are informational
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False,
            'type_distribution': type_counts
        }

    def _validate_membership_details(self, networks: List[Dict]):
        """Validate membership detail fields"""
        category = "Membership Details"
        issues = []
        total_fields = len(networks) * 4

        missing_role = [n for n in networks if not n.get('role')]
        missing_year = [n for n in networks if not n.get('year')]

        # Date validation
        invalid_dates = []
        for network in networks:
            start_date = network.get('start_date')
            end_date = network.get('end_date')

            if start_date and end_date:
                try:
                    if start_date > end_date:
                        invalid_dates.append(network)
                except:
                    invalid_dates.append(network)

        # Year validation
        current_year = 2024
        invalid_years = [n for n in networks if n.get('year') and (n['year'] < 1990 or n['year'] > current_year + 1)]

        valid_fields = total_fields - len(missing_year) - len(invalid_dates) - len(invalid_years)

        # Role is optional for some network types (fronts don't have roles)
        committees_without_role = [n for n in networks if n.get('network_type') == 'COMMITTEE' and not n.get('role')]
        if committees_without_role:
            issues.append(f"⚠️ {len(committees_without_role)} committees missing role (expected for committees)")

        if missing_year:
            issues.append(f"❌ {len(missing_year)} records missing year")
        if invalid_dates:
            issues.append(f"❌ {len(invalid_dates)} records with invalid date ranges")
        if invalid_years:
            issues.append(f"❌ {len(invalid_years)} records with invalid years")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False
        }

    def _validate_source_tracking(self, networks: List[Dict]):
        """Validate source tracking fields"""
        category = "Source Tracking"
        issues = []
        total_fields = len(networks) * 2

        missing_source_system = [n for n in networks if not n.get('source_system')]
        missing_created_at = [n for n in networks if not n.get('created_at')]

        # Validate source systems
        valid_sources = {'DEPUTADOS', 'TSE'}
        invalid_sources = [n for n in networks if n.get('source_system') not in valid_sources]

        # Check source distribution
        source_counts = {}
        for network in networks:
            source = network.get('source_system')
            source_counts[source] = source_counts.get(source, 0) + 1

        valid_fields = total_fields - len(missing_source_system) - len(missing_created_at)

        if missing_source_system:
            issues.append(f"❌ {len(missing_source_system)} records missing source_system")
        if missing_created_at:
            issues.append(f"⚠️ {len(missing_created_at)} records missing created_at")
        if invalid_sources:
            issues.append(f"❌ {len(invalid_sources)} records with invalid source_system")

        # Report source distribution
        for source, count in source_counts.items():
            if source:
                percentage = (count / len(networks)) * 100
                issues.append(f"ℹ️ {source}: {count} records ({percentage:.1f}%)")

        completion_rate = (valid_fields / total_fields) * 100
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': True,
            'source_distribution': source_counts
        }

    def _validate_data_quality(self, networks: List[Dict]):
        """Validate overall data quality"""
        category = "Data Quality"
        issues = []

        # Check for duplicates using the unique constraint
        duplicate_check = database.execute_query("""
            SELECT politician_id, network_type, network_id, year, COUNT(*) as count
            FROM unified_political_networks
            GROUP BY politician_id, network_type, network_id, year
            HAVING COUNT(*) > 1
        """)

        # Check for empty network names
        empty_names = [n for n in networks if not n.get('network_name') or n['network_name'].strip() == '']

        # Check for missing network IDs
        empty_ids = [n for n in networks if not n.get('network_id') or n['network_id'].strip() == '']

        completion_rate = 100.0
        if duplicate_check:
            issues.append(f"❌ {len(duplicate_check)} duplicate network memberships found")
            completion_rate -= 10

        if empty_names:
            issues.append(f"❌ {len(empty_names)} records with empty network names")
            completion_rate -= 5

        if empty_ids:
            issues.append(f"❌ {len(empty_ids)} records with empty network IDs")
            completion_rate -= 5

        if not duplicate_check and not empty_names and not empty_ids:
            issues.append("✅ No duplicate or empty records found")

        self.validation_results['validation_categories'][category] = {
            'completion_rate': max(completion_rate, 0),
            'issues': issues,
            'critical': True
        }

    def _validate_network_distribution(self, networks: List[Dict]):
        """Validate network distribution makes sense"""
        category = "Network Distribution"
        issues = []

        # Check politicians with no networks
        politicians_without_networks = database.execute_query("""
            SELECT COUNT(*) as count FROM unified_politicians
            WHERE id NOT IN (SELECT DISTINCT politician_id FROM unified_political_networks)
        """)

        politicians_without_count = politicians_without_networks[0]['count'] if politicians_without_networks else 0

        # Check politicians with networks
        politicians_with_networks = database.execute_query("""
            SELECT COUNT(DISTINCT politician_id) as count FROM unified_political_networks
        """)

        politicians_with_count = politicians_with_networks[0]['count'] if politicians_with_networks else 0

        # Check average networks per politician
        avg_networks = database.execute_query("""
            SELECT AVG(network_count) as avg_count FROM (
                SELECT politician_id, COUNT(*) as network_count
                FROM unified_political_networks
                GROUP BY politician_id
            ) subq
        """)

        avg_count = float(avg_networks[0]['avg_count']) if avg_networks and avg_networks[0]['avg_count'] else 0

        # Check distribution by network type
        type_stats = database.execute_query("""
            SELECT network_type, COUNT(*) as count,
                   COUNT(DISTINCT politician_id) as unique_politicians
            FROM unified_political_networks
            GROUP BY network_type
            ORDER BY count DESC
        """)

        if politicians_without_count > 0:
            issues.append(f"ℹ️ {politicians_without_count} politicians have no network memberships")

        issues.append(f"ℹ️ {politicians_with_count} politicians have network memberships")
        issues.append(f"ℹ️ Average networks per politician: {avg_count:.1f}")

        issues.append("📊 Network type statistics:")
        for stat in type_stats:
            issues.append(f"  {stat['network_type']}: {stat['count']} records, {stat['unique_politicians']} politicians")

        completion_rate = 100.0  # Distribution is informational
        self.validation_results['validation_categories'][category] = {
            'completion_rate': completion_rate,
            'issues': issues,
            'critical': False,
            'avg_networks_per_politician': avg_count,
            'politicians_with_networks': politicians_with_count,
            'politicians_without_networks': politicians_without_count
        }

    def _validate_politician_references(self, networks: List[Dict]):
        """Validate politician ID references"""
        category = "Politician References"
        issues = []

        # Check for orphaned politician references
        orphaned_politicians = database.execute_query("""
            SELECT DISTINCT politician_id
            FROM unified_political_networks
            WHERE politician_id NOT IN (SELECT id FROM unified_politicians)
        """)

        # Check for politicians with deputy_id but no committee/front memberships
        active_deputies_without_networks = database.execute_query("""
            SELECT COUNT(*) as count FROM unified_politicians
            WHERE deputy_id IS NOT NULL
            AND id NOT IN (
                SELECT DISTINCT politician_id
                FROM unified_political_networks
                WHERE source_system = 'DEPUTADOS'
            )
        """)

        active_without_count = active_deputies_without_networks[0]['count'] if active_deputies_without_networks else 0

        completion_rate = 100.0
        if orphaned_politicians:
            issues.append(f"❌ {len(orphaned_politicians)} records reference non-existent politicians")
            completion_rate -= 20
        else:
            issues.append("✅ All politician references are valid")

        if active_without_count > 0:
            issues.append(f"⚠️ {active_without_count} active deputies have no committee/front memberships")
        else:
            issues.append("✅ All active deputies have network memberships")

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
        print(f"📊 NETWORK VALIDATION SUMMARY")
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

            print()  # Add spacing between categories

        print("=" * 60)
        print(f"🎯 OVERALL COMPLIANCE SCORE: {self.validation_results['compliance_score']:.1f}%")

        if self.validation_results['compliance_score'] >= 90:
            print("🏆 EXCELLENT - Network data quality is excellent")
        elif self.validation_results['compliance_score'] >= 70:
            print("👍 GOOD - Minor improvements needed")
        else:
            print("⚠️ NEEDS IMPROVEMENT - Significant data quality issues")

        print("=" * 60)

        return self.validation_results

    def generate_network_report(self) -> Dict[str, Any]:
        """Generate detailed network analysis report"""

        # Get network statistics
        network_stats = database.execute_query("""
            SELECT
                network_type,
                COUNT(*) as total_records,
                COUNT(DISTINCT politician_id) as unique_politicians,
                COUNT(DISTINCT network_id) as unique_networks,
                AVG(CASE WHEN start_date IS NOT NULL THEN 1 ELSE 0 END) * 100 as date_completion_rate
            FROM unified_political_networks
            GROUP BY network_type
            ORDER BY total_records DESC
        """)

        # Get source system breakdown
        source_stats = database.execute_query("""
            SELECT
                source_system,
                network_type,
                COUNT(*) as count,
                COUNT(DISTINCT politician_id) as unique_politicians
            FROM unified_political_networks
            GROUP BY source_system, network_type
            ORDER BY source_system, count DESC
        """)

        # Get top networks by membership
        top_networks = database.execute_query("""
            SELECT
                network_name,
                network_type,
                COUNT(*) as member_count,
                source_system
            FROM unified_political_networks
            GROUP BY network_name, network_type, source_system
            ORDER BY member_count DESC
            LIMIT 10
        """)

        report = {
            'network_statistics': network_stats,
            'source_breakdown': source_stats,
            'top_networks': top_networks,
            'validation_results': self.validation_results
        }

        return report