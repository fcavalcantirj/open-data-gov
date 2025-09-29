"""
CLI4 Parties Populator
Political parties population following CLI4 patterns
"""

import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from cli4.modules import database
from cli4.modules.logger import CLI4Logger
from cli4.modules.rate_limiter import CLI4RateLimiter


class CLI4PartiesPopulator:
    """Populate political_parties and party_memberships tables with Câmara data"""

    def __init__(self, logger: CLI4Logger, rate_limiter: CLI4RateLimiter):
        self.logger = logger
        self.rate_limiter = rate_limiter
        self.camara_base = "https://dadosabertos.camara.leg.br/api/v2"

    def populate(self, limit: Optional[int] = None, legislatura_id: Optional[int] = None,
                force_refresh: bool = False) -> List[int]:
        """Main population method"""

        print(f"🏛️ Discovering political parties...")

        # Default to current legislature if not specified
        if not legislatura_id:
            legislatura_id = 57  # Current legislature as of 2025

        party_ids = self._get_party_ids(limit=limit)
        print(f"📋 Processing {len(party_ids)} parties for legislature {legislatura_id}")

        created_ids = []

        for i, party_id in enumerate(party_ids, 1):
            try:
                print(f"\n🎯 [{i}/{len(party_ids)}] Processing party {party_id}")

                # Check if party already exists for this legislature (idempotency)
                if not force_refresh and self._party_exists(party_id, legislatura_id):
                    print(f"   ⏭️ Party {party_id} already exists for legislature {legislatura_id}")
                    continue

                # Get party details
                party_detail = self._get_party_detail(party_id)
                if not party_detail:
                    continue

                # Get party members
                party_members = self._get_party_members(party_id)

                # Create or update party record
                party_db_id = self._create_or_update_party(party_detail, legislatura_id, party_members)
                if party_db_id:
                    created_ids.append(party_db_id)

                # Create party memberships
                if party_members:
                    self._create_party_memberships(party_id, party_members, legislatura_id)

                self.logger.log_processing(
                    'parties', str(party_id), 'success',
                    {
                        'party_name': party_detail.get('nome', 'Unknown'),
                        'members_count': len(party_members) if party_members else 0,
                        'legislatura_id': legislatura_id
                    }
                )

                print(f"   ✅ Party created/updated: {party_detail.get('nome')} ({len(party_members) if party_members else 0} members)")

            except Exception as e:
                print(f"   ❌ Error processing party {party_id}: {e}")
                self.logger.log_processing('parties', str(party_id), 'error', {'error': str(e)})
                continue

            self.rate_limiter.wait_if_needed('default')

        print(f"\n✅ PARTIES POPULATION COMPLETED")
        print(f"   Parties processed: {len(party_ids)}")
        print(f"   Parties created/updated: {len(created_ids)}")

        return created_ids

    def _get_party_ids(self, limit: Optional[int] = None) -> List[int]:
        """Get list of all party IDs from Câmara API"""
        try:
            url = f"{self.camara_base}/partidos"
            params = {}
            if limit:
                params['itens'] = min(limit, 100)  # API max is 100

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            parties = data.get('dados', [])

            party_ids = [party['id'] for party in parties if party.get('id')]

            print(f"   📊 Found {len(party_ids)} parties")
            return party_ids[:limit] if limit else party_ids

        except Exception as e:
            print(f"   ❌ Error fetching party list: {e}")
            return []

    def _get_party_detail(self, party_id: int) -> Optional[Dict]:
        """Get detailed party information"""
        try:
            url = f"{self.camara_base}/partidos/{party_id}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            party_detail = data.get('dados')

            if not party_detail:
                print(f"   ⚠️ No detail data for party {party_id}")
                return None

            print(f"   📄 Party: {party_detail.get('nome', 'Unknown')} ({party_detail.get('sigla', 'N/A')})")
            return party_detail

        except Exception as e:
            print(f"   ❌ Error fetching party {party_id} detail: {e}")
            return None

    def _get_party_members(self, party_id: int) -> Optional[List[Dict]]:
        """Get party members list"""
        try:
            url = f"{self.camara_base}/partidos/{party_id}/membros"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            members = data.get('dados', [])

            print(f"   👥 Members: {len(members)}")
            return members

        except Exception as e:
            print(f"   ❌ Error fetching party {party_id} members: {e}")
            return None

    def _party_exists(self, party_id: int, legislatura_id: int) -> bool:
        """Check if party already exists for this legislature (idempotency)"""
        query = """
            SELECT id FROM political_parties
            WHERE id = %s AND legislatura_id = %s
        """
        result = database.execute_query(query, (party_id, legislatura_id))
        return len(result) > 0 if result else False

    def _create_or_update_party(self, party_detail: Dict, legislatura_id: int,
                               members: Optional[List[Dict]]) -> Optional[int]:
        """Create or update party record"""
        try:
            # Extract status information (nested structure in API)
            status = party_detail.get('status', {})

            party_data = {
                'id': party_detail['id'],
                'nome': party_detail.get('nome'),
                'sigla': party_detail.get('sigla'),
                'numero_eleitoral': party_detail.get('numeroEleitoral'),
                'status': status.get('situacao', 'Ativo'),
                'legislatura_id': legislatura_id,
                'logo_url': party_detail.get('urlLogo'),
                'uri_membros': status.get('uriMembros'),
                'total_membros': len(members) if members else 0,
                'total_efetivos': int(status.get('totalPosse', 0)) if status.get('totalPosse') else 0,
                'updated_at': datetime.now()
            }

            # Extract leader information if available (also in status)
            leader = status.get('lider', {})
            if leader:
                party_data.update({
                    'lider_atual': leader.get('nome'),
                    'lider_id': leader.get('uri', '').split('/')[-1] if leader.get('uri') else None,
                    'lider_estado': leader.get('uf'),
                    'lider_legislatura': leader.get('idLegislatura')
                })

            # Try to update first (idempotency)
            update_query = """
                UPDATE political_parties
                SET nome = %s, sigla = %s, numero_eleitoral = %s, status = %s,
                    lider_atual = %s, lider_id = %s, lider_estado = %s, lider_legislatura = %s,
                    total_membros = %s, total_efetivos = %s, logo_url = %s, uri_membros = %s,
                    updated_at = %s
                WHERE id = %s AND legislatura_id = %s
            """

            update_params = (
                party_data['nome'], party_data['sigla'], party_data['numero_eleitoral'],
                party_data['status'], party_data.get('lider_atual'), party_data.get('lider_id'),
                party_data.get('lider_estado'), party_data.get('lider_legislatura'),
                party_data['total_membros'], party_data['total_efetivos'],
                party_data['logo_url'], party_data['uri_membros'], party_data['updated_at'],
                party_data['id'], party_data['legislatura_id']
            )

            rows_updated = database.execute_update(update_query, update_params)

            if rows_updated > 0:
                print(f"   🔄 Updated existing party record")
                return party_data['id']

            # If no rows updated, insert new record
            insert_query = """
                INSERT INTO political_parties (
                    id, nome, sigla, numero_eleitoral, status, lider_atual, lider_id,
                    lider_estado, lider_legislatura, total_membros, total_efetivos,
                    legislatura_id, logo_url, uri_membros, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            insert_params = (
                party_data['id'], party_data['nome'], party_data['sigla'],
                party_data['numero_eleitoral'], party_data['status'],
                party_data.get('lider_atual'), party_data.get('lider_id'),
                party_data.get('lider_estado'), party_data.get('lider_legislatura'),
                party_data['total_membros'], party_data['total_efetivos'],
                party_data['legislatura_id'], party_data['logo_url'],
                party_data['uri_membros'], datetime.now(), party_data['updated_at']
            )

            database.execute_update(insert_query, insert_params)
            print(f"   ➕ Created new party record")

            return party_data['id']

        except Exception as e:
            print(f"   ❌ Error creating/updating party: {e}")
            return None

    def _create_party_memberships(self, party_id: int, members: List[Dict],
                                 legislatura_id: int) -> int:
        """Create party membership records"""
        created_count = 0

        for member in members:
            try:
                member_data = {
                    'party_id': party_id,
                    'deputy_id': member.get('id'),
                    'deputy_name': member.get('nome'),
                    'legislatura_id': member.get('idLegislatura', legislatura_id),
                    'status': 'Ativo',  # Members from API are assumed active
                    'created_at': datetime.now()
                }

                # Check if membership already exists (idempotency)
                check_query = """
                    SELECT id FROM party_memberships
                    WHERE party_id = %s AND deputy_id = %s AND legislatura_id = %s
                """
                existing = database.execute_query(
                    check_query,
                    (member_data['party_id'], member_data['deputy_id'], member_data['legislatura_id'])
                )

                if existing:
                    continue  # Skip if already exists

                # Insert new membership
                insert_query = """
                    INSERT INTO party_memberships (
                        party_id, deputy_id, deputy_name, legislatura_id, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """

                insert_params = (
                    member_data['party_id'], member_data['deputy_id'],
                    member_data['deputy_name'], member_data['legislatura_id'],
                    member_data['status'], member_data['created_at']
                )

                database.execute_update(insert_query, insert_params)
                created_count += 1

            except Exception as e:
                print(f"   ⚠️ Error creating membership for deputy {member.get('id', 'unknown')}: {e}")
                continue

        if created_count > 0:
            print(f"   👥 Created {created_count} new party memberships")

        return created_count

    def get_population_stats(self) -> Dict[str, Any]:
        """Get current population statistics"""
        try:
            stats_query = """
                SELECT
                    COUNT(*) as total_parties,
                    COUNT(DISTINCT legislatura_id) as legislatures_covered,
                    SUM(total_membros) as total_members_across_parties,
                    AVG(total_membros) as avg_members_per_party
                FROM political_parties
            """

            membership_query = """
                SELECT COUNT(*) as total_memberships
                FROM party_memberships
            """

            stats = database.execute_query(stats_query)
            memberships = database.execute_query(membership_query)

            result = {
                'total_parties': stats[0]['total_parties'] if stats else 0,
                'legislatures_covered': stats[0]['legislatures_covered'] if stats else 0,
                'total_members_across_parties': stats[0]['total_members_across_parties'] if stats else 0,
                'avg_members_per_party': float(stats[0]['avg_members_per_party']) if stats and stats[0]['avg_members_per_party'] else 0.0,
                'total_memberships': memberships[0]['total_memberships'] if memberships else 0
            }

            return result

        except Exception as e:
            print(f"Error getting population stats: {e}")
            return {}


def main():
    """Standalone test of parties populator"""
    print("🧪 TESTING PARTIES POPULATOR")
    print("=" * 50)

    from cli4.modules.logger import CLI4Logger
    from cli4.modules.rate_limiter import CLI4RateLimiter

    logger = CLI4Logger()
    rate_limiter = CLI4RateLimiter()

    populator = CLI4PartiesPopulator(logger, rate_limiter)

    # Test with limited parties
    result = populator.populate(limit=5)
    print(f"\n🎯 Test completed: {len(result)} parties processed")

    # Show stats
    stats = populator.get_population_stats()
    print(f"\n📊 Population Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    main()