"""
CLI4 Logger
Simple logging - console + file, no overcomplicated nonsense
"""

import json
import time
import psutil
import os
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

        # System monitoring
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss

        if self.file:
            self.log_dir = Path("logs")
            self.log_dir.mkdir(exist_ok=True)
            self.log_file = self.log_dir / f"cli4_{self.session_id}.log"

    def log_api_call(self, api: str, endpoint: str, status: str, response_time: float):
        """Log API calls with system stats"""
        self.api_calls += 1
        if status != "success":
            self.api_errors += 1

        # Get current system stats
        sys_stats = self._get_system_stats()

        if self.console:
            emoji = "✅" if status == "success" else "❌"
            print(f"{emoji} {api} {endpoint}: {status} ({response_time:.2f}s) | "
                  f"MEM: {sys_stats['memory_percent']:.1f}% ({sys_stats['memory_mb']:.0f}MB) | "
                  f"CPU: {sys_stats['cpu_percent']:.1f}%")

        if self.file:
            self._write_to_file({
                'timestamp': datetime.now().isoformat(),
                'type': 'api_call',
                'api': api,
                'endpoint': endpoint,
                'status': status,
                'response_time': response_time,
                'system_stats': sys_stats
            })

    def log_processing(self, entity_type: str, entity_id: str, status: str, details: dict = None):
        """Log processing events with system stats"""
        self.processed += 1
        if status == "error":
            self.errors += 1

        # Get current system stats
        sys_stats = self._get_system_stats()

        if self.console:
            emoji = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
            message = f"{emoji} {entity_type} {entity_id}: {status}"
            if details and 'name' in details:
                message += f" ({details['name']})"
            message += f" | MEM: {sys_stats['memory_percent']:.1f}% ({sys_stats['memory_mb']:.0f}MB)"
            print(message)

        if self.file:
            self._write_to_file({
                'timestamp': datetime.now().isoformat(),
                'type': 'processing',
                'entity_type': entity_type,
                'entity_id': str(entity_id),
                'status': status,
                'details': details or {},
                'system_stats': sys_stats
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

    def _get_system_stats(self) -> dict:
        """Get comprehensive system statistics"""
        try:
            # Process memory info
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_growth_mb = (memory_info.rss - self.initial_memory) / 1024 / 1024

            # System memory info
            system_memory = psutil.virtual_memory()

            # Disk usage for current directory
            disk_usage = psutil.disk_usage('.')

            # CPU usage
            cpu_percent = self.process.cpu_percent()
            system_cpu = psutil.cpu_percent(interval=None)

            return {
                'memory_mb': memory_mb,
                'memory_percent': (memory_info.rss / system_memory.total) * 100,
                'memory_growth_mb': memory_growth_mb,
                'system_memory_percent': system_memory.percent,
                'system_memory_available_gb': system_memory.available / 1024 / 1024 / 1024,
                'disk_used_percent': (disk_usage.used / disk_usage.total) * 100,
                'disk_free_gb': disk_usage.free / 1024 / 1024 / 1024,
                'cpu_percent': cpu_percent,
                'system_cpu_percent': system_cpu,
                'num_threads': self.process.num_threads(),
                'num_fds': self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
            }
        except Exception:
            return {
                'memory_mb': 0, 'memory_percent': 0, 'memory_growth_mb': 0,
                'system_memory_percent': 0, 'system_memory_available_gb': 0,
                'disk_used_percent': 0, 'disk_free_gb': 0,
                'cpu_percent': 0, 'system_cpu_percent': 0,
                'num_threads': 0, 'num_fds': 0
            }

    def log_system_checkpoint(self, checkpoint_name: str):
        """Log a system checkpoint with full stats"""
        sys_stats = self._get_system_stats()

        if self.console:
            print(f"\n🔍 SYSTEM CHECKPOINT: {checkpoint_name}")
            print(f"   💾 Process Memory: {sys_stats['memory_mb']:.0f}MB (growth: {sys_stats['memory_growth_mb']:+.0f}MB)")
            print(f"   🖥️  System Memory: {sys_stats['system_memory_percent']:.1f}% used ({sys_stats['system_memory_available_gb']:.1f}GB free)")
            print(f"   💽 Disk Usage: {sys_stats['disk_used_percent']:.1f}% ({sys_stats['disk_free_gb']:.1f}GB free)")
            print(f"   ⚡ CPU: Process {sys_stats['cpu_percent']:.1f}% | System {sys_stats['system_cpu_percent']:.1f}%")
            print(f"   🧵 Threads: {sys_stats['num_threads']} | File Descriptors: {sys_stats['num_fds']}")

        if self.file:
            self._write_to_file({
                'timestamp': datetime.now().isoformat(),
                'type': 'system_checkpoint',
                'checkpoint_name': checkpoint_name,
                'system_stats': sys_stats
            })

    def print_summary(self):
        """Print comprehensive session summary with final system stats"""
        elapsed = time.time() - self.start_time
        final_stats = self._get_system_stats()

        print("\n📊 CLI4 SESSION SUMMARY")
        print("=" * 60)
        print(f"Session ID: {self.session_id}")
        print(f"Duration: {elapsed:.1f}s")
        print(f"API calls: {self.api_calls} ({self.api_errors} errors)")
        print(f"Processed: {self.processed} ({self.errors} errors)")

        print(f"\n🖥️  FINAL SYSTEM STATS:")
        print(f"   💾 Peak Memory: {final_stats['memory_mb']:.0f}MB (growth: {final_stats['memory_growth_mb']:+.0f}MB)")
        print(f"   🖥️  System Memory: {final_stats['system_memory_percent']:.1f}% used")
        print(f"   💽 Disk Usage: {final_stats['disk_used_percent']:.1f}% used")
        print(f"   🧵 Final Threads: {final_stats['num_threads']}")

        if self.file:
            print(f"\n📄 Log file: {self.log_file}")

        print("=" * 60)

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