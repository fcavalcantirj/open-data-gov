#!/usr/bin/env python3
"""
PAGINATION VERIFICATION: Confirm unique records across pages
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def verify_pagination():
    """Verify we're getting unique records across pages"""

    api_key = os.getenv('PORTAL_TRANSPARENCIA_API_KEY')
    session = requests.Session()
    session.headers.update({
        'chave-api-dados': api_key,
        'User-Agent': 'CLI4-Pagination-Verification/1.0'
    })

    base_url = "https://api.portaldatransparencia.gov.br/api-de-dados/"

    print("🔍 PAGINATION VERIFICATION")
    print("=" * 50)

    all_ids = set()
    all_cnpjs = set()
    all_entities = set()

    # Collect data from first 5 pages
    for page in range(1, 6):
        print(f"📄 Page {page}:")

        response = session.get(f"{base_url}ceis", params={'pagina': page})
        data = response.json()

        page_ids = set()
        page_cnpjs = set()
        page_entities = set()

        for sanction in data:
            sanction_id = sanction.get('id')
            pessoa = sanction.get('pessoa', {})
            cnpj = pessoa.get('cnpjFormatado', '')
            entity_name = pessoa.get('nome', '')

            if sanction_id:
                page_ids.add(sanction_id)
            if cnpj:
                page_cnpjs.add(cnpj)
            if entity_name:
                page_entities.add(entity_name)

        print(f"   IDs: {len(page_ids)} unique")
        print(f"   CNPJs: {len(page_cnpjs)} unique")
        print(f"   Entities: {len(page_entities)} unique")

        # Check for overlaps with previous pages
        id_overlap = page_ids.intersection(all_ids)
        cnpj_overlap = page_cnpjs.intersection(all_cnpjs)

        if id_overlap:
            print(f"   ⚠️ ID overlap: {len(id_overlap)} IDs seen before")
        if cnpj_overlap:
            print(f"   ⚠️ CNPJ overlap: {len(cnpj_overlap)} CNPJs seen before")

        # Add to cumulative sets
        all_ids.update(page_ids)
        all_cnpjs.update(page_cnpjs)
        all_entities.update(page_entities)

    print(f"\n📊 CUMULATIVE RESULTS (5 pages):")
    print(f"   Total unique IDs: {len(all_ids)}")
    print(f"   Total unique CNPJs: {len(all_cnpjs)}")
    print(f"   Total unique entities: {len(all_entities)}")
    print(f"   Total records fetched: {5 * 15}")

    if len(all_ids) == 75:  # 5 pages × 15 records
        print(f"   ✅ Perfect: All records are unique")
    else:
        print(f"   ⚠️ Some records are duplicated")

    # Show some sample entities
    print(f"\n🏢 SAMPLE SANCTIONED ENTITIES:")
    for i, entity in enumerate(sorted(all_entities)[:10]):
        print(f"   {i+1}. {entity}")

    return len(all_ids), len(all_cnpjs)

if __name__ == "__main__":
    verify_pagination()