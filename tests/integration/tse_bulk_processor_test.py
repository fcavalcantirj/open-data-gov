"""
TSE BULK PROCESSOR - FULL PROCESSING ALGORITHM
Standalone test for processing ALL 108 CSV files with 5M+ records

This algorithm will be tested separately before integration into TSE client.
GOAL: 100% data coverage with production-grade performance.
"""

import csv
import os
import time
from typing import Dict, List, Any, Optional, Generator
from pathlib import Path
import sys
from collections import defaultdict

class TSEBulkProcessor:
    """
    Production-grade TSE bulk processor
    Handles ALL 108 files with 5M+ records using streaming and batch processing
    """

    def __init__(self, data_directory: str):
        self.data_directory = Path(data_directory)
        self.stats = {
            'files_processed': 0,
            'total_records': 0,
            'records_by_type': defaultdict(int),
            'records_by_state': defaultdict(int),
            'files_by_type': defaultdict(int),
            'processing_time': 0,
            'memory_usage': 0
        }
        self.start_time = None

    def discover_all_files(self) -> Dict[str, List[Path]]:
        """
        Discover ALL TSE finance CSV files
        Returns: Dict with file paths organized by data type
        """
        print("🔍 DISCOVERING ALL TSE FINANCE FILES...")

        all_files = {
            'receitas': [],
            'despesas_contratadas': [],
            'despesas_pagas': [],
            'doador_originario': []
        }

        # Find all CSV files
        csv_files = list(self.data_directory.glob("*.csv"))
        print(f"📁 Found {len(csv_files)} total CSV files")

        # Categorize by data type
        for file_path in csv_files:
            filename = file_path.name.lower()

            if 'doador_originario' in filename:
                all_files['doador_originario'].append(file_path)
            elif 'despesas_contratadas' in filename:
                all_files['despesas_contratadas'].append(file_path)
            elif 'despesas_pagas' in filename:
                all_files['despesas_pagas'].append(file_path)
            elif 'receitas_candidatos' in filename:
                all_files['receitas'].append(file_path)

        # Report discovery results
        for data_type, files in all_files.items():
            print(f"  📊 {data_type}: {len(files)} files")
            self.stats['files_by_type'][data_type] = len(files)

        total_files = sum(len(files) for files in all_files.values())
        print(f"🎯 TOTAL FILES TO PROCESS: {total_files}")

        return all_files

    def stream_csv_records(self, file_path: Path, data_type: str) -> Generator[Dict[str, Any], None, None]:
        """
        Memory-efficient streaming of CSV records
        Yields one record at a time to avoid loading massive files into memory
        """
        try:
            with open(file_path, 'r', encoding='latin-1') as csvfile:
                # TSE uses semicolon delimiter
                reader = csv.DictReader(csvfile, delimiter=';')

                for row_num, row in enumerate(reader, 1):
                    # Add metadata
                    processed_record = {
                        **row,
                        'tse_data_type': data_type,
                        'source_file': file_path.name,
                        'row_number': row_num
                    }

                    yield processed_record

                    # Progress indicator for large files
                    if row_num % 10000 == 0:
                        print(f"    📄 {file_path.name}: {row_num:,} records processed...")

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")

    def process_single_file(self, file_path: Path, data_type: str) -> Dict[str, Any]:
        """
        Process a single CSV file with full statistics
        """
        print(f"📄 Processing: {file_path.name} ({data_type})")

        file_stats = {
            'file_path': str(file_path),
            'data_type': data_type,
            'records_processed': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'states_found': set(),
            'file_size_mb': file_path.stat().st_size / 1024 / 1024,
            'processing_time': 0
        }

        start_time = time.time()

        # Stream all records from file
        for record in self.stream_csv_records(file_path, data_type):
            file_stats['records_processed'] += 1
            self.stats['total_records'] += 1

            # Validate record based on data type
            if self._validate_record(record, data_type):
                file_stats['valid_records'] += 1

                # Extract state for geographic analysis
                state = self._extract_state(record, data_type)
                if state:
                    file_stats['states_found'].add(state)
                    self.stats['records_by_state'][state] += 1
            else:
                file_stats['invalid_records'] += 1

        file_stats['processing_time'] = time.time() - start_time
        file_stats['states_found'] = list(file_stats['states_found'])  # Convert set to list

        # Update global stats
        self.stats['records_by_type'][data_type] += file_stats['valid_records']
        self.stats['files_processed'] += 1

        print(f"  ✅ {file_stats['records_processed']:,} records ({file_stats['valid_records']:,} valid) in {file_stats['processing_time']:.1f}s")

        return file_stats

    def _validate_record(self, record: Dict[str, Any], data_type: str) -> bool:
        """
        Validate record based on TSE data type requirements
        """
        try:
            if data_type in ['receitas', 'doador_originario']:
                # Must have candidate CPF and amount
                return (
                    record.get('NR_CPF_CANDIDATO') and
                    record.get('VR_RECEITA') and
                    float(record.get('VR_RECEITA', 0)) > 0
                )
            elif data_type == 'despesas_contratadas':
                # Must have candidate CPF and contracted amount
                return (
                    record.get('NR_CPF_CANDIDATO') and
                    record.get('VR_DESPESA_CONTRATADA') and
                    float(record.get('VR_DESPESA_CONTRATADA', 0)) > 0
                )
            elif data_type == 'despesas_pagas':
                # Must have candidate CPF and payment amount
                return (
                    record.get('NR_CPF_CANDIDATO') and
                    record.get('VR_PAGAMENTO') and
                    float(record.get('VR_PAGAMENTO', 0)) > 0
                )

            return False

        except (ValueError, TypeError):
            return False

    def _extract_state(self, record: Dict[str, Any], data_type: str) -> Optional[str]:
        """
        Extract state code from record
        """
        return record.get('SG_UF') or record.get('SG_UF_CANDIDATO')

    def process_all_files(self) -> Dict[str, Any]:
        """
        FULL PROCESSING: Process ALL 108 files with ALL records
        """
        print("🚀 STARTING FULL TSE PROCESSING")
        print("=" * 60)
        print("TARGET: ALL 108 files, 5M+ records, 100% data coverage")
        print("=" * 60)

        self.start_time = time.time()

        # Discover all files
        all_files = self.discover_all_files()

        # Process each data type completely
        detailed_results = {}

        for data_type, files in all_files.items():
            if not files:
                print(f"⚠️ No files found for {data_type}")
                continue

            print(f"\n📊 PROCESSING {data_type.upper()}: {len(files)} files")
            print("-" * 50)

            type_results = []

            for file_path in files:
                file_result = self.process_single_file(file_path, data_type)
                type_results.append(file_result)

            detailed_results[data_type] = type_results

        # Final statistics
        self.stats['processing_time'] = time.time() - self.start_time

        return {
            'summary_stats': dict(self.stats),
            'detailed_results': detailed_results
        }

    def print_final_report(self, results: Dict[str, Any]):
        """
        Print comprehensive processing report
        """
        stats = results['summary_stats']

        print("\n" + "=" * 60)
        print("🎯 FULL TSE PROCESSING COMPLETE")
        print("=" * 60)

        print(f"📁 Files processed: {stats['files_processed']:,}")
        print(f"📊 Total records: {stats['total_records']:,}")
        print(f"⏱️ Processing time: {stats['processing_time']:.1f} seconds")
        print(f"🚄 Records/second: {stats['total_records'] / stats['processing_time']:,.0f}")

        print(f"\n📈 RECORDS BY TYPE:")
        for data_type, count in stats['records_by_type'].items():
            percentage = (count / stats['total_records']) * 100
            print(f"  {data_type}: {count:,} ({percentage:.1f}%)")

        print(f"\n🗺️ RECORDS BY STATE (top 10):")
        top_states = sorted(stats['records_by_state'].items(), key=lambda x: x[1], reverse=True)[:10]
        for state, count in top_states:
            percentage = (count / stats['total_records']) * 100
            print(f"  {state}: {count:,} ({percentage:.1f}%)")

        print(f"\n📋 FILES BY TYPE:")
        for data_type, count in stats['files_by_type'].items():
            print(f"  {data_type}: {count} files")

        print("\n✅ FULL PROCESSING VALIDATION:")
        expected_files = 108  # 4 types × 27 states
        if stats['files_processed'] >= expected_files * 0.9:  # Allow for missing files
            print(f"  ✅ File coverage: EXCELLENT ({stats['files_processed']}/{expected_files})")
        else:
            print(f"  ⚠️ File coverage: PARTIAL ({stats['files_processed']}/{expected_files})")

        if stats['total_records'] >= 1000000:  # At least 1M records
            print(f"  ✅ Data volume: PRODUCTION-SCALE ({stats['total_records']:,} records)")
        else:
            print(f"  ⚠️ Data volume: LIMITED ({stats['total_records']:,} records)")


def main():
    """
    Test the FULL PROCESSING algorithm
    """
    print("🧪 TSE BULK PROCESSOR TEST")
    print("Testing FULL PROCESSING algorithm before TSE client integration")
    print()

    # Initialize processor
    data_dir = "/Users/fcavalcanti/Downloads/prestacao_de_contas_eleitorais_candidatos_2022"

    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        print("Please ensure TSE data is downloaded to the correct location.")
        return

    processor = TSEBulkProcessor(data_dir)

    # Run full processing
    try:
        results = processor.process_all_files()
        processor.print_final_report(results)

        print(f"\n💾 Results can be saved to JSON if needed")
        print(f"🔧 Algorithm ready for TSE client integration")

    except KeyboardInterrupt:
        print(f"\n⏹️ Processing interrupted by user")
        print(f"📊 Partial results: {processor.stats['total_records']:,} records processed")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()