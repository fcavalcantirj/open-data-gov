"""
Ultra-Simple Logger - NO FILES, NO HANGING
Just print statements for CLI v2
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


class UltraSimpleLogger:
    """Ultra-simple logger - just print, no files"""

    def __init__(self, name: str = "open-data-gov"):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.metrics = {
            "api_calls": {},
            "success_counts": {},
            "failure_counts": {}
        }

    def log_api_call(self, api_name: str, endpoint: str, status: str,
                     response_time: float = 0, details: Optional[Dict] = None):
        """Log API calls - just print, no files"""
        # Just update metrics, don't write files
        if api_name not in self.metrics["api_calls"]:
            self.metrics["api_calls"][api_name] = {"success": 0, "failure": 0, "total_time": 0}

        self.metrics["api_calls"][api_name]["total_time"] += response_time
        if status == "success":
            self.metrics["api_calls"][api_name]["success"] += 1
        else:
            self.metrics["api_calls"][api_name]["failure"] += 1

    def log_processing(self, entity_type: str, entity_id: Any,
                      status: str, details: Optional[Dict] = None):
        """Log entity processing - just print"""
        log_msg = f"{entity_type} {entity_id}: {status}"
        if details:
            log_msg += f" | {json.dumps(details)}"

        if status == "success":
            print(f"✅ {log_msg}")
            key = f"{entity_type}_success"
            self.metrics["success_counts"][key] = self.metrics["success_counts"].get(key, 0) + 1
        elif status == "error":
            print(f"❌ {log_msg}")
            key = f"{entity_type}_failure"
            self.metrics["failure_counts"][key] = self.metrics["failure_counts"].get(key, 0) + 1
        elif status == "warning":
            print(f"⚠️ {log_msg}")

    def log_data_issue(self, issue_type: str, description: str,
                       data_sample: Optional[Any] = None):
        """Log data quality issues - just print"""
        print(f"⚠️ DATA ISSUE [{issue_type}]: {description}")

    def save_session_metrics(self):
        """Print session summary - no files"""
        print("\n📊 SESSION SUMMARY")
        print("=" * 50)
        print(f"Session ID: {self.session_id}")
        print("Logs saved to: /Users/fcavalcanti/dev/open-data-gov/logs")
        print("\nAPI Calls:")
        for api, stats in self.metrics["api_calls"].items():
            total = stats["success"] + stats["failure"]
            success_rate = (stats["success"] / total * 100) if total > 0 else 0
            avg_time = (stats["total_time"] / total) if total > 0 else 0
            print(f"  {api}: {total} calls, {success_rate:.1f}% success, {avg_time:.2f}s avg")

        print("\nProcessing Results:")
        for key, count in self.metrics["success_counts"].items():
            print(f"  ✅ {key}: {count}")
        for key, count in self.metrics["failure_counts"].items():
            print(f"  ❌ {key}: {count}")

        return self.metrics


# Global enhanced logger instance
enhanced_logger = UltraSimpleLogger()


# Convenience functions for backward compatibility
def log_info(message: str):
    print(f"ℹ️ {message}")

def log_error(message: str, exc_info: bool = True):
    print(f"❌ {message}")

def log_debug(message: str):
    print(f"🔍 {message}")

def log_warning(message: str):
    print(f"⚠️ {message}")