"""
CLI4 Assets Validator
Comprehensive validation for politician_assets table
"""

from typing import Dict, List, Any, Optional
from cli4.modules import database


class AssetsValidator:
    """Comprehensive assets data validation following CLI4 patterns"""

    def __init__(self):
        self.validation_results = {
            'total_asset_records': 0,
            'validation_categories': {},
            'critical_issues': [],
            'warnings': [],
            'compliance_score': 0.0
        }

    def validate_all_assets(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive validation on all asset records"""
        print("🏛️ COMPREHENSIVE ASSETS VALIDATION")
        print("=" * 60)
        print("Individual TSE asset declarations data quality assessment")
        print()

        # Get asset records
        query = "SELECT * FROM politician_assets"
        if limit:
            query += f" LIMIT {limit}"

        asset_records = database.execute_query(query)
        self.validation_results['total_asset_records'] = len(asset_records)

        if not asset_records:
            print("⚠️ No asset records found in database")
            return self.validation_results

        limit_text = f" (limited to {limit})" if limit else ""
        print(f"📊 Validating {len(asset_records)} asset records{limit_text}...")
        print()

        # Run validation categories
        self._validate_core_identifiers(asset_records)
        self._validate_asset_details(asset_records)
        self._validate_financial_data(asset_records)
        self._validate_temporal_data(asset_records)
        self._validate_source_tracking(asset_records)
        self._validate_data_quality(asset_records)
        self._validate_asset_distribution(asset_records)
        self._validate_politician_references(asset_records)

        # Calculate compliance score
        self._calculate_compliance_score()

        # Print results
        self._print_validation_summary()

        return self.validation_results

    def _validate_core_identifiers(self, asset_records: List[Dict]):
        """Validate core identifier fields"""
        print("🔍 Core Identifiers Validation")

        results = {
            'valid_politician_ids': 0,
            'missing_politician_ids': 0,
            'valid_asset_sequences': 0,
            'missing_asset_sequences': 0,
            'duplicate_sequences': 0
        }

        # Track for duplicate detection
        sequence_combinations = set()

        for record in asset_records:
            # Check politician_id
            if record.get('politician_id'):
                results['valid_politician_ids'] += 1
            else:
                results['missing_politician_ids'] += 1
                self.validation_results['critical_issues'].append(
                    f"Record {record.get('id')} missing politician_id"
                )

            # Check asset_sequence
            asset_sequence = record.get('asset_sequence')
            if asset_sequence is not None:
                results['valid_asset_sequences'] += 1

                # Check for duplicates (politician_id, declaration_year, asset_sequence)
                combination = (record.get('politician_id'), record.get('declaration_year'), asset_sequence)
                if combination in sequence_combinations:
                    results['duplicate_sequences'] += 1
                    self.validation_results['critical_issues'].append(
                        f"Duplicate asset sequence: politician {record.get('politician_id')}, "
                        f"year {record.get('declaration_year')}, sequence {asset_sequence}"
                    )
                else:
                    sequence_combinations.add(combination)
            else:
                results['missing_asset_sequences'] += 1
                self.validation_results['warnings'].append(
                    f"Record {record.get('id')} missing asset_sequence"
                )

        self.validation_results['validation_categories']['core_identifiers'] = results
        print(f"  ✅ Valid politician IDs: {results['valid_politician_ids']}")
        print(f"  ❌ Missing politician IDs: {results['missing_politician_ids']}")
        print(f"  ✅ Valid asset sequences: {results['valid_asset_sequences']}")
        print(f"  ⚠️ Missing asset sequences: {results['missing_asset_sequences']}")
        print(f"  🔄 Duplicate sequences: {results['duplicate_sequences']}")
        print()

    def _validate_asset_details(self, asset_records: List[Dict]):
        """Validate asset-specific fields"""
        print("🏠 Asset Details Validation")

        results = {
            'valid_asset_types': 0,
            'missing_asset_types': 0,
            'asset_type_distribution': {},
            'complete_descriptions': 0,
            'missing_descriptions': 0,
            'long_descriptions': 0
        }

        for record in asset_records:
            # Check asset type
            asset_type = record.get('asset_type_code')
            asset_type_desc = record.get('asset_type_description')

            if asset_type is not None:
                results['valid_asset_types'] += 1
                # Track distribution
                type_key = f"{asset_type} - {asset_type_desc or 'Unknown'}"
                results['asset_type_distribution'][type_key] = \
                    results['asset_type_distribution'].get(type_key, 0) + 1
            else:
                results['missing_asset_types'] += 1

            # Check asset description
            description = record.get('asset_description', '')
            if description and description.strip():
                results['complete_descriptions'] += 1
                if len(description) > 500:
                    results['long_descriptions'] += 1
            else:
                results['missing_descriptions'] += 1

        self.validation_results['validation_categories']['asset_details'] = results
        print(f"  ✅ Valid asset types: {results['valid_asset_types']}")
        print(f"  ⚠️ Missing asset types: {results['missing_asset_types']}")
        print(f"  📝 Complete descriptions: {results['complete_descriptions']}")
        print(f"  ⚠️ Missing descriptions: {results['missing_descriptions']}")
        print(f"  📏 Long descriptions (>500 chars): {results['long_descriptions']}")
        print(f"  📊 Top asset types:")
        sorted_types = sorted(results['asset_type_distribution'].items(),
                             key=lambda x: x[1], reverse=True)
        for asset_type, count in sorted_types[:5]:
            print(f"     {asset_type}: {count}")
        print()

    def _validate_financial_data(self, asset_records: List[Dict]):
        """Validate financial fields (values, currency)"""
        print("💰 Financial Data Validation")

        results = {
            'valid_values': 0,
            'zero_values': 0,
            'negative_values': 0,
            'unreasonable_values': 0,
            'valid_currency': 0,
            'missing_currency': 0,
            'value_ranges': {
                'under_1k': 0,
                '1k_10k': 0,
                '10k_100k': 0,
                '100k_1m': 0,
                'over_1m': 0
            },
            'total_declared_value': 0.0,
            'average_asset_value': 0.0
        }

        total_value = 0.0
        valid_value_count = 0

        for record in asset_records:
            # Check declared value
            declared_value = record.get('declared_value', 0)

            if declared_value > 0:
                results['valid_values'] += 1
                valid_value_count += 1
                total_value += float(declared_value)

                # Categorize by value range
                if declared_value < 1000:
                    results['value_ranges']['under_1k'] += 1
                elif declared_value < 10000:
                    results['value_ranges']['1k_10k'] += 1
                elif declared_value < 100000:
                    results['value_ranges']['10k_100k'] += 1
                elif declared_value < 1000000:
                    results['value_ranges']['100k_1m'] += 1
                else:
                    results['value_ranges']['over_1m'] += 1

                # Check for unreasonably high values (>R$ 100 million)
                if declared_value > 100000000:
                    results['unreasonable_values'] += 1
                    self.validation_results['warnings'].append(
                        f"Record {record.get('id')} has unreasonably high value: R$ {declared_value:,.2f}"
                    )

            elif declared_value == 0:
                results['zero_values'] += 1
            else:
                results['negative_values'] += 1
                self.validation_results['critical_issues'].append(
                    f"Record {record.get('id')} has negative value: {declared_value}"
                )

            # Check currency
            currency = record.get('currency')
            if currency == 'BRL':
                results['valid_currency'] += 1
            else:
                results['missing_currency'] += 1

        results['total_declared_value'] = total_value
        results['average_asset_value'] = total_value / valid_value_count if valid_value_count > 0 else 0

        self.validation_results['validation_categories']['financial_data'] = results
        print(f"  ✅ Valid values: {results['valid_values']}")
        print(f"  ⚠️ Zero values: {results['zero_values']}")
        print(f"  ❌ Negative values: {results['negative_values']}")
        print(f"  🚨 Unreasonable values: {results['unreasonable_values']}")
        print(f"  💵 Total declared value: R$ {results['total_declared_value']:,.2f}")
        print(f"  📊 Average asset value: R$ {results['average_asset_value']:,.2f}")
        print(f"  🏷️ Valid currency (BRL): {results['valid_currency']}")
        print(f"  📈 Value distribution:")
        for range_name, count in results['value_ranges'].items():
            print(f"     {range_name}: {count}")
        print()

    def _validate_temporal_data(self, asset_records: List[Dict]):
        """Validate temporal fields (years, dates)"""
        print("⏰ Temporal Data Validation")

        results = {
            'valid_declaration_years': 0,
            'missing_declaration_years': 0,
            'future_declarations': 0,
            'old_declarations': 0,
            'year_distribution': {},
            'valid_update_dates': 0,
            'missing_update_dates': 0,
            'valid_generation_dates': 0,
            'missing_generation_dates': 0
        }

        current_year = 2024
        min_reasonable_year = 2010  # TSE electronic declarations

        for record in asset_records:
            # Check declaration year
            declaration_year = record.get('declaration_year')
            if declaration_year:
                results['valid_declaration_years'] += 1
                results['year_distribution'][declaration_year] = \
                    results['year_distribution'].get(declaration_year, 0) + 1

                if declaration_year > current_year:
                    results['future_declarations'] += 1
                    self.validation_results['warnings'].append(
                        f"Record {record.get('id')} has future declaration year: {declaration_year}"
                    )
                elif declaration_year < min_reasonable_year:
                    results['old_declarations'] += 1
            else:
                results['missing_declaration_years'] += 1

            # Check update dates
            if record.get('last_update_date'):
                results['valid_update_dates'] += 1
            else:
                results['missing_update_dates'] += 1

            # Check generation dates
            if record.get('data_generation_date'):
                results['valid_generation_dates'] += 1
            else:
                results['missing_generation_dates'] += 1

        self.validation_results['validation_categories']['temporal_data'] = results
        print(f"  ✅ Valid declaration years: {results['valid_declaration_years']}")
        print(f"  ⚠️ Missing declaration years: {results['missing_declaration_years']}")
        print(f"  🔮 Future declarations: {results['future_declarations']}")
        print(f"  📅 Pre-2010 declarations: {results['old_declarations']}")
        print(f"  📊 Year distribution:")
        sorted_years = sorted(results['year_distribution'].items(), key=lambda x: x[0], reverse=True)
        for year, count in sorted_years:
            print(f"     {year}: {count}")
        print(f"  🕐 Valid update dates: {results['valid_update_dates']}")
        print(f"  🕐 Valid generation dates: {results['valid_generation_dates']}")
        print()

    def _validate_source_tracking(self, asset_records: List[Dict]):
        """Validate source system tracking"""
        print("📡 Source System Validation")

        results = {
            'tse_records': 0,
            'other_sources': 0,
            'missing_source': 0,
            'valid_timestamps': 0,
            'missing_timestamps': 0
        }

        for record in asset_records:
            source_system = record.get('source_system')

            # Check source system
            if source_system == 'TSE':
                results['tse_records'] += 1
            elif source_system:
                results['other_sources'] += 1
            else:
                results['missing_source'] += 1

            # Check timestamps
            if record.get('created_at'):
                results['valid_timestamps'] += 1
            else:
                results['missing_timestamps'] += 1

        self.validation_results['validation_categories']['source_tracking'] = results
        print(f"  ✅ TSE records: {results['tse_records']}")
        print(f"  📊 Other source records: {results['other_sources']}")
        print(f"  ⚠️ Missing source info: {results['missing_source']}")
        print(f"  🕐 Valid timestamps: {results['valid_timestamps']}")
        print(f"  ⚠️ Missing timestamps: {results['missing_timestamps']}")
        print()

    def _validate_data_quality(self, asset_records: List[Dict]):
        """Validate overall data quality"""
        print("🔍 Data Quality Assessment")

        results = {
            'complete_records': 0,
            'partial_records': 0,
            'minimal_records': 0,
            'data_completeness_score': 0.0
        }

        essential_fields = ['politician_id', 'asset_sequence', 'declared_value', 'declaration_year']
        important_fields = ['asset_type_code', 'asset_type_description', 'asset_description']
        optional_fields = ['last_update_date', 'data_generation_date', 'currency']

        total_completeness = 0

        for record in asset_records:
            essential_count = sum(1 for field in essential_fields if record.get(field) is not None)
            important_count = sum(1 for field in important_fields
                                if record.get(field) and str(record.get(field)).strip())
            optional_count = sum(1 for field in optional_fields if record.get(field))

            # Calculate weighted completeness (essential=3, important=2, optional=1)
            max_score = len(essential_fields) * 3 + len(important_fields) * 2 + len(optional_fields) * 1
            actual_score = essential_count * 3 + important_count * 2 + optional_count * 1
            completeness_score = (actual_score / max_score) * 100

            total_completeness += completeness_score

            # Categorize record completeness
            if completeness_score >= 80:
                results['complete_records'] += 1
            elif completeness_score >= 50:
                results['partial_records'] += 1
            else:
                results['minimal_records'] += 1

        results['data_completeness_score'] = total_completeness / len(asset_records) if asset_records else 0

        self.validation_results['validation_categories']['data_quality'] = results
        print(f"  ✅ Complete records (≥80%): {results['complete_records']}")
        print(f"  ⚠️ Partial records (50-79%): {results['partial_records']}")
        print(f"  ❌ Minimal records (<50%): {results['minimal_records']}")
        print(f"  📊 Average completeness: {results['data_completeness_score']:.1f}%")
        print()

    def _validate_asset_distribution(self, asset_records: List[Dict]):
        """Validate asset distribution patterns"""
        print("📊 Asset Distribution Analysis")

        results = {
            'politicians_with_assets': 0,
            'assets_per_politician': {},
            'single_asset_politicians': 0,
            'multi_asset_politicians': 0,
            'max_assets_per_politician': 0,
            'year_coverage': {}
        }

        # Group by politician
        politician_assets = {}
        for record in asset_records:
            politician_id = record.get('politician_id')
            year = record.get('declaration_year')

            if politician_id not in politician_assets:
                politician_assets[politician_id] = {}
            if year not in politician_assets[politician_id]:
                politician_assets[politician_id][year] = []
            politician_assets[politician_id][year].append(record)

        results['politicians_with_assets'] = len(politician_assets)

        for politician_id, years_data in politician_assets.items():
            total_assets = sum(len(assets) for assets in years_data.values())

            if total_assets == 1:
                results['single_asset_politicians'] += 1
            else:
                results['multi_asset_politicians'] += 1

            if total_assets > results['max_assets_per_politician']:
                results['max_assets_per_politician'] = total_assets

            # Track year coverage
            for year in years_data:
                results['year_coverage'][year] = results['year_coverage'].get(year, 0) + 1

        self.validation_results['validation_categories']['asset_distribution'] = results
        print(f"  👥 Politicians with assets: {results['politicians_with_assets']}")
        print(f"  👤 Single asset politicians: {results['single_asset_politicians']}")
        print(f"  🏠 Multi-asset politicians: {results['multi_asset_politicians']}")
        print(f"  📈 Max assets per politician: {results['max_assets_per_politician']}")
        print(f"  📊 Year coverage:")
        sorted_years = sorted(results['year_coverage'].items(), key=lambda x: x[0], reverse=True)
        for year, count in sorted_years:
            print(f"     {year}: {count} politicians")
        print()

    def _validate_politician_references(self, asset_records: List[Dict]):
        """Validate references to unified_politicians table"""
        print("🔗 Politician Reference Validation")

        results = {
            'valid_references': 0,
            'invalid_references': 0,
            'orphaned_records': 0
        }

        # Get all valid politician IDs
        valid_politician_ids = set()
        politicians = database.execute_query("SELECT id FROM unified_politicians")
        for politician in politicians:
            valid_politician_ids.add(politician['id'])

        # Check references
        for record in asset_records:
            politician_id = record.get('politician_id')
            if politician_id in valid_politician_ids:
                results['valid_references'] += 1
            elif politician_id:
                results['invalid_references'] += 1
                self.validation_results['critical_issues'].append(
                    f"Record {record.get('id')} references non-existent politician_id: {politician_id}"
                )
            else:
                results['orphaned_records'] += 1

        self.validation_results['validation_categories']['politician_references'] = results
        print(f"  ✅ Valid politician references: {results['valid_references']}")
        print(f"  ❌ Invalid references: {results['invalid_references']}")
        print(f"  🚨 Orphaned records: {results['orphaned_records']}")
        print()

    def _calculate_compliance_score(self):
        """Calculate overall compliance score"""
        categories = self.validation_results['validation_categories']
        total_records = self.validation_results['total_asset_records']

        if total_records == 0:
            self.validation_results['compliance_score'] = 0.0
            return

        # Weight different validation categories
        score_components = []

        # Core identifiers (25% weight)
        core = categories.get('core_identifiers', {})
        if core:
            core_score = (core.get('valid_politician_ids', 0) +
                         core.get('valid_asset_sequences', 0)) / (total_records * 2) * 100
            score_components.append(('core_identifiers', core_score, 0.25))

        # Financial data (25% weight)
        financial = categories.get('financial_data', {})
        if financial:
            financial_score = (financial.get('valid_values', 0) / total_records) * 100
            score_components.append(('financial_data', financial_score, 0.25))

        # Data quality (20% weight)
        quality = categories.get('data_quality', {})
        if quality:
            quality_score = quality.get('data_completeness_score', 0)
            score_components.append(('data_quality', quality_score, 0.20))

        # Politician references (15% weight)
        refs = categories.get('politician_references', {})
        if refs:
            ref_score = (refs.get('valid_references', 0) / total_records) * 100
            score_components.append(('politician_references', ref_score, 0.15))

        # Temporal data (10% weight)
        temporal = categories.get('temporal_data', {})
        if temporal:
            temporal_score = (temporal.get('valid_declaration_years', 0) / total_records) * 100
            score_components.append(('temporal_data', temporal_score, 0.10))

        # Source tracking (5% weight)
        source = categories.get('source_tracking', {})
        if source:
            source_score = (source.get('tse_records', 0) / total_records) * 100
            score_components.append(('source_tracking', source_score, 0.05))

        # Calculate weighted average
        if score_components:
            weighted_score = sum(score * weight for _, score, weight in score_components)
            self.validation_results['compliance_score'] = weighted_score

    def _print_validation_summary(self):
        """Print comprehensive validation summary"""
        print("=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        total_records = self.validation_results['total_asset_records']
        compliance_score = self.validation_results['compliance_score']
        critical_issues = len(self.validation_results['critical_issues'])
        warnings = len(self.validation_results['warnings'])

        print(f"🏛️ Total asset records validated: {total_records}")
        print(f"🎯 Overall compliance score: {compliance_score:.1f}%")
        print(f"🚨 Critical issues found: {critical_issues}")
        print(f"⚠️ Warnings issued: {warnings}")

        # Compliance rating
        if compliance_score >= 95:
            rating = "🟢 EXCELLENT"
        elif compliance_score >= 85:
            rating = "🔵 GOOD"
        elif compliance_score >= 70:
            rating = "🟡 NEEDS IMPROVEMENT"
        else:
            rating = "🔴 POOR"

        print(f"📈 Data quality rating: {rating}")
        print()

        # Show top issues if any
        if self.validation_results['critical_issues']:
            print("🚨 TOP CRITICAL ISSUES:")
            for issue in self.validation_results['critical_issues'][:5]:
                print(f"   • {issue}")
            if len(self.validation_results['critical_issues']) > 5:
                print(f"   ... and {len(self.validation_results['critical_issues']) - 5} more")
            print()