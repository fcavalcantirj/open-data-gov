"""
Wealth Populator Integration Test
Tests the complete CLI4 Wealth Populator workflow with real data
"""

import unittest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter
from cli4.populators.wealth import CLI4WealthPopulator, CLI4WealthValidator
from src.clients.tse_client import TSEClient


class TestWealthPopulatorIntegration(unittest.TestCase):
    """Integration tests for CLI4 Wealth Populator components"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.logger = CLI4Logger()
        cls.rate_limiter = CLI4RateLimiter()
        cls.tse_client = TSEClient()

    def test_01_database_connection(self):
        """Test database connection and schema"""
        print("\n🗄️ Testing database connection...")

        # Test basic connection
        result = database.execute_query('SELECT 1 as test')
        self.assertTrue(result)
        self.assertEqual(result[0]['test'], 1)
        print("✅ Database connection successful")

        # Test unified_wealth_tracking table exists
        result = database.execute_query('''
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'unified_wealth_tracking'
            )
        ''')

        table_exists = result[0]['exists'] if result else False
        self.assertTrue(table_exists, "unified_wealth_tracking table must exist")
        print("✅ unified_wealth_tracking table exists")

    def test_02_get_test_politician(self):
        """Get a test politician with TSE data for testing"""
        print("\n👤 Getting test politician...")

        politicians = database.execute_query('''
            SELECT id, cpf, sq_candidato_current, nome_civil
            FROM unified_politicians
            WHERE cpf IS NOT NULL AND sq_candidato_current IS NOT NULL
            LIMIT 1
        ''')

        self.assertTrue(politicians, "Must have at least one politician with CPF and SQ_CANDIDATO")

        self.test_politician = politicians[0]
        print(f"✅ Test politician: {self.test_politician['nome_civil']} (ID: {self.test_politician['id']})")
        print(f"   CPF: {self.test_politician['cpf']}")
        print(f"   SQ_CANDIDATO: {self.test_politician['sq_candidato_current']}")

    def test_03_tse_asset_data_retrieval(self):
        """Test TSE asset data retrieval"""
        print("\n💎 Testing TSE asset data retrieval...")

        # Test asset data retrieval for 2022
        asset_data = self.tse_client.get_asset_data(2022)

        if asset_data:
            print(f"✅ Retrieved {len(asset_data)} asset records for 2022")

            # Check data structure
            sample_asset = asset_data[0]
            required_fields = ['SQ_CANDIDATO', 'VR_BEM_CANDIDATO', 'ANO_ELEICAO']

            for field in required_fields:
                self.assertIn(field, sample_asset, f"Asset data must contain {field}")

            print("✅ Asset data has required fields")
        else:
            print("⚠️ No asset data available for 2022")

    def test_04_currency_parsing(self):
        """Test Brazilian currency parsing"""
        print("\n💰 Testing Brazilian currency parsing...")

        # Create wealth populator for testing
        wealth_populator = CLI4WealthPopulator(self.logger, self.rate_limiter)

        # Test various currency formats
        test_cases = [
            ("1234567.89", 1234567.89),
            ("1234567,89", 1234567.89),
            ("1.234.567,89", 1234567.89),
            ("0", 0.0),
            ("", 0.0),
            (None, 0.0),
            ("invalid", 0.0)
        ]

        for input_val, expected in test_cases:
            result = wealth_populator._parse_brazilian_currency(input_val)
            self.assertEqual(float(result), expected, f"Currency parsing failed for {input_val}")

        print("✅ Currency parsing works correctly")

    def test_05_asset_categorization(self):
        """Test asset categorization logic"""
        print("\n📊 Testing asset categorization...")

        # Create wealth populator for testing
        wealth_populator = CLI4WealthPopulator(self.logger, self.rate_limiter)

        # Test categorization logic
        test_cases = [
            (1, 'real_estate'),    # Real estate codes
            (11, 'vehicles'),      # Vehicle codes
            (21, 'investments'),   # Investment codes
            (31, 'business'),      # Business codes
            (41, 'cash_deposits'), # Cash codes
            (999, 'other'),        # Unknown codes
            (None, 'other')        # None values
        ]

        for input_code, expected_category in test_cases:
            result = wealth_populator._categorize_asset(input_code)
            self.assertEqual(result, expected_category,
                           f"Asset categorization failed for code {input_code}")

        print("✅ Asset categorization works correctly")

    def test_06_wealth_populator_initialization(self):
        """Test wealth populator initialization"""
        print("\n🏗️ Testing wealth populator initialization...")

        # Test populator creation
        wealth_populator = CLI4WealthPopulator(self.logger, self.rate_limiter)

        # Check essential components
        self.assertIsNotNone(wealth_populator.logger)
        self.assertIsNotNone(wealth_populator.rate_limiter)
        self.assertIsNotNone(wealth_populator.tse_client)
        self.assertIsInstance(wealth_populator.ASSET_CATEGORIES, dict)

        print("✅ Wealth populator initialized correctly")

    def test_07_wealth_validator_initialization(self):
        """Test wealth validator initialization"""
        print("\n🔍 Testing wealth validator initialization...")

        # Test validator creation
        wealth_validator = CLI4WealthValidator()

        self.assertIsNotNone(wealth_validator)
        self.assertIsInstance(wealth_validator.validation_results, dict)

        print("✅ Wealth validator initialized correctly")

    def test_08_existing_wealth_records_check(self):
        """Test existing wealth records detection"""
        print("\n📋 Testing existing wealth records check...")

        # Use test politician from earlier test
        if not hasattr(self, 'test_politician'):
            self.test_02_get_test_politician()

        # Create wealth populator
        wealth_populator = CLI4WealthPopulator(self.logger, self.rate_limiter)

        # Check existing records
        existing_count = wealth_populator._count_existing_records(self.test_politician['id'])

        print(f"✅ Found {existing_count} existing wealth records for test politician")

        # Should return a non-negative integer
        self.assertIsInstance(existing_count, int)
        self.assertGreaterEqual(existing_count, 0)

    def test_09_cli_integration_help(self):
        """Test CLI integration by checking help text"""
        print("\n⚙️ Testing CLI integration...")

        # Test importing the CLI module
        from cli4.main import setup_cli

        parser = setup_cli()
        help_text = parser.format_help()

        # Check that wealth commands are included
        self.assertIn('populate-wealth', help_text)
        self.assertIn('--election-years', help_text)

        print("✅ CLI integration successful - wealth commands available")


if __name__ == '__main__':
    print("🧪 CLI4 WEALTH POPULATOR INTEGRATION TESTS")
    print("=" * 60)
    print("Testing comprehensive wealth populator workflow")
    print("=" * 60)

    unittest.main(verbosity=2)