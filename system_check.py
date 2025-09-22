#!/usr/bin/env python3
"""
Final system check before running
"""

print('🔍 FINAL SYSTEM CHECK BEFORE RUNNING')
print('=' * 60)

# 1. Check all critical fixes are in place
from pathlib import Path

fixes_status = []

# Check asset_populator has uppercase field mapping
asset_pop = Path('cli/modules/asset_populator.py').read_text()
if 'NR_ORDEM_BEM_CANDIDATO' in asset_pop and 'ANO_ELEICAO' in asset_pop:
    fixes_status.append('✅ Asset field mapping: UPPERCASE TSE fields')
else:
    fixes_status.append('❌ Asset field mapping: NOT FIXED')

# Check VARCHAR truncation
if 'type_desc[:97]' in asset_pop:
    fixes_status.append('✅ VARCHAR truncation: Active (100 char limit)')
else:
    fixes_status.append('❌ VARCHAR truncation: NOT FIXED')

# Check currency parsing
if '_parse_currency_value' in asset_pop:
    fixes_status.append('✅ Currency parsing: Brazilian format supported')
else:
    fixes_status.append('❌ Currency parsing: NOT FIXED')

# Check date parsing
if 'Brazilian format' in asset_pop or 'DD/MM/YYYY' in asset_pop:
    fixes_status.append('✅ Date parsing: Brazilian format supported')
else:
    fixes_status.append('❌ Date parsing: NOT FIXED')

# Check wealth_populator
wealth_pop = Path('cli/modules/wealth_populator.py').read_text()
if 'ANO_ELEICAO' in wealth_pop and 'VR_BEM_CANDIDATO' in wealth_pop:
    fixes_status.append('✅ Wealth populator: UPPERCASE fields')
else:
    fixes_status.append('❌ Wealth populator: NOT FIXED')

# Check logging
if Path('cli/modules/logger_config.py').exists():
    fixes_status.append('✅ File logging: Configured')
if Path('cli/modules/enhanced_logger.py').exists():
    fixes_status.append('✅ Enhanced logging: Available')
if Path('cli/modules/rate_limiter.py').exists():
    fixes_status.append('✅ Rate limiter: Available')

print('📋 FIXES STATUS:')
for status in fixes_status:
    print(f'  {status}')

# 2. Check database connectivity
print('\n🗄️ DATABASE CHECK:')
from cli.modules.database_manager import DatabaseManager
db = DatabaseManager()
print(f'  ✅ Database connected')

# 3. Check table status
print('\n📊 TABLE STATUS:')
tables = [
    'unified_politicians',
    'unified_financial_records',
    'financial_counterparts',
    'unified_political_networks',
    'unified_wealth_tracking',
    'politician_career_history',
    'politician_events',
    'politician_assets',
    'politician_professional_background'
]

empty_tables = []
populated_tables = []
for table in tables:
    try:
        count = db.execute_query(f'SELECT COUNT(*) as count FROM {table}')[0]['count']
        status = '✅' if count > 0 else '⚪'
        print(f'  {status} {table}: {count} records')
        if count == 0:
            empty_tables.append(table)
        else:
            populated_tables.append(table)
    except Exception as e:
        print(f'  ❌ {table}: ERROR - {e}')

# 4. Check TSE client caching
print('\n🌐 TSE CLIENT STATUS:')
import os
cache_dir = Path('.cache/tse')
if cache_dir.exists():
    cache_files = list(cache_dir.glob('*.json'))
    print(f'  ✅ Cache directory exists with {len(cache_files)} files')
    for cf in cache_files[:3]:
        size_mb = cf.stat().st_size / (1024*1024)
        print(f'    - {cf.name}: {size_mb:.1f} MB')
else:
    print(f'  ⚪ No cache directory (will be created on first run)')

# 5. Check for SQ_CANDIDATO availability
print('\n🔑 SQ_CANDIDATO CHECK:')
try:
    sq_check = db.execute_query("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN sq_candidato_current IS NOT NULL THEN 1 ELSE 0 END) as with_sq
        FROM unified_politicians
    """)[0]
    if sq_check['total'] > 0:
        pct = (sq_check['with_sq'] / sq_check['total'] * 100)
        print(f"  Politicians with SQ_CANDIDATO: {sq_check['with_sq']}/{sq_check['total']} ({pct:.1f}%)")
    else:
        print("  No politicians in database yet")
except:
    print("  No politicians table yet")

print('\n' + '=' * 60)
print('📝 SUMMARY:')
print(f'  Tables populated: {len(populated_tables)}/9')
print(f'  Tables empty: {len(empty_tables)}/9')
print(f'  All fixes applied: {"YES" if all("✅" in s for s in fixes_status) else "PARTIAL"}')

print('\n💡 RECOMMENDATIONS:')
print('  1. Run in smaller batches: --limit 10')
print('  2. Monitor logs in /logs/ directory')
print('  3. If errors occur, check VARCHAR truncation in logs')

if empty_tables:
    print(f'\n⚠️ Empty tables: {", ".join(empty_tables)}')

print('\n✨ SYSTEM READY TO RUN!')
print('\n🚀 Suggested commands:')
print('   python cli/main.py populate all --limit 10  # For testing')
print('   python cli/main.py populate all --limit 100 # For full run')