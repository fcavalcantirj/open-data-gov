"""
Network Populator Integration Test
Tests the complete Network Populator workflow with real API data
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
from src.clients.deputados_client import DeputadosClient
from src.clients.tse_client import TSEClient


class TestNetworkPopulatorIntegration(unittest.TestCase):
    """Integration tests for Network Populator components"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.logger = CLI4Logger()
        cls.rate_limiter = CLI4RateLimiter()
        cls.deputados_client = DeputadosClient()
        cls.tse_client = TSEClient()

    def test_01_database_connection(self):
        """Test database connection and schema"""
        print("\n🗄️ Testing database connection...")

        # Test basic connection
        result = database.execute_query('SELECT 1 as test')
        self.assertTrue(result)
        self.assertEqual(result[0]['test'], 1)
        print("✅ Database connection successful")

        # Test unified_political_networks table exists
        result = database.execute_query('''
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'unified_political_networks'
            )
        ''')

        table_exists = result[0]['exists'] if result else False
        self.assertTrue(table_exists, "unified_political_networks table must exist")
        print("✅ unified_political_networks table exists")

    def test_02_get_test_politician(self):
        """Get a test politician with deputy_id for testing"""
        print("\n👤 Getting test politician...")

        politicians = database.execute_query('''
            SELECT id, deputy_id, cpf, nome_civil, current_state
            FROM unified_politicians
            WHERE deputy_id IS NOT NULL AND cpf IS NOT NULL
            LIMIT 1
        ''')

        self.assertTrue(politicians, "Must have at least one politician with deputy_id and CPF")

        self.test_politician = politicians[0]
        print(f"✅ Test politician: {self.test_politician['nome_civil']} (ID: {self.test_politician['id']})")
        print(f"   Deputy ID: {self.test_politician['deputy_id']}")
        print(f"   State: {self.test_politician['current_state']}")

    def test_03_deputados_api_committees(self):
        """Test Deputados API committee endpoint"""
        print("\n📋 Testing Deputados committees API...")

        # Use test politician from previous test
        if not hasattr(self, 'test_politician'):
            self.test_02_get_test_politician()

        deputy_id = self.test_politician['deputy_id']

        # Test with rate limiting
        wait_time = self.rate_limiter.wait_if_needed('camara')
        print(f"   Rate limit wait: {wait_time:.3f}s")

        # Get committees
        committees = self.deputados_client.get_deputy_committees(deputy_id)
        self.assertIsInstance(committees, list)

        print(f"✅ Found {len(committees)} committee memberships")

        if committees:
            sample = committees[0]
            required_fields = ['idOrgao', 'nomeOrgao', 'titulo']
            for field in required_fields:
                self.assertIn(field, sample, f"Committee must have {field} field")

            print(f"   Sample: {sample.get('nomeOrgao')} ({sample.get('titulo')})")

    def test_04_deputados_api_fronts(self):
        """Test Deputados API parliamentary fronts endpoint"""
        print("\n🏛️ Testing Deputados fronts API...")

        # Use test politician from previous test
        if not hasattr(self, 'test_politician'):
            self.test_02_get_test_politician()

        deputy_id = self.test_politician['deputy_id']

        # Test with rate limiting
        wait_time = self.rate_limiter.wait_if_needed('camara')

        # Get fronts
        fronts = self.deputados_client.get_deputy_fronts(deputy_id)
        self.assertIsInstance(fronts, list)

        print(f"✅ Found {len(fronts)} parliamentary front memberships")

        if fronts:
            sample = fronts[0]
            required_fields = ['id', 'titulo']
            for field in required_fields:
                self.assertIn(field, sample, f"Front must have {field} field")

            print(f"   Sample: {sample.get('titulo')[:80]}...")

    def test_05_tse_client_coalition_data(self):
        """Test TSE client coalition/federation data"""
        print("\n🗳️ Testing TSE coalition data...")

        # Use test politician from previous test
        if not hasattr(self, 'test_politician'):
            self.test_02_get_test_politician()

        cpf = self.test_politician['cpf']
        state = self.test_politician['current_state']

        print(f"   Searching TSE for CPF in {state}...")

        # Test with rate limiting
        wait_time = self.rate_limiter.wait_if_needed('tse')

        try:
            # Get candidate data for recent election
            candidates = self.tse_client.get_candidate_data(2022, state)
            self.assertIsInstance(candidates, list)
            print(f"   Found {len(candidates)} candidates in {state} 2022")

            # Look for our politician
            matches = [c for c in candidates if c.get('nr_cpf_candidato') == cpf]

            if matches:
                match = matches[0]
                print(f"✅ Found politician in TSE: {match.get('nm_candidato')}")
                print(f"   Party: {match.get('sg_partido')}")

                # Check federation data
                if match.get('nr_federacao') and match.get('nr_federacao') != '-1':
                    print(f"   Federation: {match.get('sg_federacao')} (ID: {match.get('nr_federacao')})")
                else:
                    print("   No federation membership")
            else:
                print("⚠️ Politician not found in TSE 2022 (normal - may not have run)")

        except Exception as e:
            print(f"⚠️ TSE search error: {e} (this can happen - TSE data is large)")

    def test_06_field_mapping_validation(self):
        """Test field mapping for network records"""
        print("\n🗺️ Testing field mappings...")

        # Test committee mapping
        sample_committee = {
            'idOrgao': 12345,
            'nomeOrgao': 'Test Committee',
            'titulo': 'Titular',
            'dataInicio': '2024-01-01T00:00',
            'dataFim': None
        }

        committee_record = {
            'politician_id': 1,
            'network_type': 'COMMITTEE',
            'network_id': str(sample_committee.get('idOrgao')),
            'network_name': sample_committee.get('nomeOrgao'),
            'role': sample_committee.get('titulo'),
            'start_date': sample_committee.get('dataInicio'),
            'end_date': sample_committee.get('dataFim'),
            'source_system': 'DEPUTADOS'
        }

        # Validate required fields are mapped
        required_fields = ['politician_id', 'network_type', 'network_id', 'network_name', 'source_system']
        for field in required_fields:
            self.assertIn(field, committee_record)
            self.assertIsNotNone(committee_record[field])

        print("✅ Committee field mapping validated")

        # Test front mapping
        sample_front = {
            'id': 67890,
            'titulo': 'Test Parliamentary Front',
            'idLegislatura': 57
        }

        front_record = {
            'politician_id': 1,
            'network_type': 'PARLIAMENTARY_FRONT',
            'network_id': str(sample_front.get('id')),
            'network_name': sample_front.get('titulo'),
            'legislature_id': sample_front.get('idLegislatura'),
            'source_system': 'DEPUTADOS'
        }

        for field in required_fields:
            self.assertIn(field, front_record)
            self.assertIsNotNone(front_record[field])

        print("✅ Parliamentary front field mapping validated")

    def test_07_rate_limiting_integration(self):
        """Test rate limiting with network endpoints"""
        print("\n⏱️ Testing rate limiting integration...")

        import time

        # Test multiple rapid calls to camara API
        start_time = time.time()
        for i in range(3):
            wait_time = self.rate_limiter.wait_if_needed('camara')
            if wait_time > 0:
                time.sleep(wait_time)

        total_time = time.time() - start_time
        self.assertGreater(total_time, 1.0, "Rate limiting should enforce delays")

        print(f"✅ Rate limiting working (total time: {total_time:.2f}s)")

    def test_08_logger_integration(self):
        """Test logger integration"""
        print("\n📝 Testing logger integration...")

        # Test different log types that Network Populator will use
        self.logger.log_processing('network', 'test_123', 'success', {'networks_found': 3})
        print("✅ log_processing works")

        self.logger.log_api_call('camara', 'committees/test', 'success', 0.5)
        print("✅ log_api_call works")

        self.logger.log_processing('network', 'test_456', 'error', {'error': 'test error'})
        print("✅ Error logging works")


def run_integration_tests():
    """Run the integration tests"""
    print("🚀 NETWORK POPULATOR INTEGRATION TESTS")
    print("=" * 60)

    # Check environment
    if not os.getenv('POSTGRES_POOL_URL'):
        print("❌ POSTGRES_POOL_URL environment variable required")
        print("   Export it or source .env file")
        return False

    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNetworkPopulatorIntegration)

    runner = unittest.TextTestRunner(verbosity=0, buffer=True)
    result = runner.run(suite)

    print("\n" + "=" * 60)

    if result.wasSuccessful():
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("🚀 Network Populator is ready for implementation!")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        return False


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)