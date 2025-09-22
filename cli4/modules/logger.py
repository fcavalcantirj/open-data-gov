"""
CLI4 Logger
Simple logging - console + file, no overcomplicated nonsense
"""

import json
import time
from datetime import datetime
from pathlib import Path


class CLI4Logger:
    """Simple logger - console + optional file"""

    def __init__(self, console: bool = True, file: bool = False):
        self.console = console
        self.file = file
        self.start_time = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Simple counters
        self.api_calls = 0
        self.api_errors = 0
        self.processed = 0
        self.errors = 0

        if self.file:
            self.log_dir = Path("logs")
            self.log_dir.mkdir(exist_ok=True)
            self.log_file = self.log_dir / f"cli4_{self.session_id}.log"

    def log_api_call(self, api: str, endpoint: str, status: str, response_time: float):
        """Log API calls"""
        self.api_calls += 1
        if status != "success":
            self.api_errors += 1

        if self.console:
            emoji = "✅" if status == "success" else "❌"
            print(f"{emoji} {api} {endpoint}: {status} ({response_time:.2f}s)")

        if self.file:
            self._write_to_file({
                'timestamp': datetime.now().isoformat(),
                'type': 'api_call',
                'api': api,
                'endpoint': endpoint,
                'status': status,
                'response_time': response_time
            })

    def log_processing(self, entity_type: str, entity_id: str, status: str, details: dict = None):
        """Log processing events"""
        self.processed += 1
        if status == "error":
            self.errors += 1

        if self.console:
            emoji = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
            message = f"{emoji} {entity_type} {entity_id}: {status}"
            if details and 'name' in details:
                message += f" ({details['name']})"
            print(message)

        if self.file:
            self._write_to_file({
                'timestamp': datetime.now().isoformat(),
                'type': 'processing',
                'entity_type': entity_type,
                'entity_id': str(entity_id),
                'status': status,
                'details': details or {}
            })

    def _write_to_file(self, log_entry: dict):
        """Write to log file - simple, no async complexity"""
        if not self.file:
            return

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(log_entry, f, ensure_ascii=False)
                f.write('\n')
        except Exception:
            # Never crash on logging errors
            pass

    def print_summary(self):
        """Print simple session summary"""
        elapsed = time.time() - self.start_time

        print("\n📊 CLI4 SESSION SUMMARY")
        print("=" * 50)
        print(f"Session ID: {self.session_id}")
        print(f"Duration: {elapsed:.1f}s")
        print(f"API calls: {self.api_calls} ({self.api_errors} errors)")
        print(f"Processed: {self.processed} ({self.errors} errors)")

        if self.file:
            print(f"Log file: {self.log_file}")

        print("=" * 50)

    def cleanup(self):
        """Simple cleanup - no complex threading"""
        pass


# Simple functions for basic logging
def log_info(message: str):
    print(f"ℹ️ {message}")

def log_error(message: str):
    print(f"❌ {message}")

def log_warning(message: str):
    print(f"⚠️ {message}")