"""
CLI4 Dependency Checker
Validates that required populators have been run before executing dependent commands
"""

from cli4.modules import database


class DependencyChecker:
    """Check for required data dependencies before running commands"""

    @staticmethod
    def check_politicians_populated() -> tuple[bool, str]:
        """Check if politicians table has been populated"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM unified_politicians"
        )
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "No politicians found. Run 'populate' first!"
        return True, f"✓ Found {count} politicians"

    @staticmethod
    def check_financial_populated() -> tuple[bool, str]:
        """Check if financial records have been populated"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM unified_financial_records"
        )
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "No financial records found. Run 'populate-financial' first!"
        return True, f"✓ Found {count:,} financial records"

    @staticmethod
    def check_electoral_populated() -> tuple[bool, str]:
        """Check if electoral records have been populated"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM unified_electoral_records"
        )
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "No electoral records found. Run 'populate-electoral' first!"
        return True, f"✓ Found {count:,} electoral records"

    @staticmethod
    def check_networks_populated() -> tuple[bool, str]:
        """Check if network records have been populated"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM unified_political_networks"
        )
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "No network records found. Run 'populate-networks' first!"
        return True, f"✓ Found {count:,} network records"

    @staticmethod
    def check_postprocessing_done() -> tuple[bool, str]:
        """Check if post-processing has been completed"""
        result = database.execute_query("""
            SELECT COUNT(*) as count
            FROM unified_politicians
            WHERE first_election_year IS NOT NULL
               OR last_election_year IS NOT NULL
        """)
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "Post-processing not done. Run 'post-process' first!"
        return True, f"✓ Found {count} politicians with aggregate fields"

    @staticmethod
    def check_wealth_populated() -> tuple[bool, str]:
        """Check if wealth records have been populated"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM unified_wealth_tracking"
        )
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "No wealth records found. Run 'populate-wealth' first!"
        return True, f"✓ Found {count:,} wealth records"

    @staticmethod
    def check_assets_populated() -> tuple[bool, str]:
        """Check if asset records have been populated"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM politician_assets"
        )
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "No asset records found. Run 'populate-assets' first!"
        return True, f"✓ Found {count:,} asset records"

    @staticmethod
    def check_professional_populated() -> tuple[bool, str]:
        """Check if professional background records have been populated"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM politician_professional_background"
        )
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "No professional records found. Run 'populate-professional' first!"
        return True, f"✓ Found {count:,} professional records"

    @staticmethod
    def check_events_populated() -> tuple[bool, str]:
        """Check if parliamentary events records have been populated"""
        result = database.execute_query(
            "SELECT COUNT(*) as count FROM politician_events"
        )
        count = result[0]['count'] if result else 0

        if count == 0:
            return False, "No events records found. Run 'populate-events' first!"
        return True, f"✓ Found {count:,} events records"

    @staticmethod
    def print_dependency_warning(required_steps: list[str], current_step: str):
        """Print a prominent warning about dependencies"""
        print("\n" + "⚠️" * 20)
        print("⚠️                                                                      ⚠️")
        print("⚠️                    DEPENDENCY CHECK WARNING                         ⚠️")
        print("⚠️                                                                      ⚠️")
        print("⚠️" * 20)
        print()
        print(f"🔍 Checking dependencies for: {current_step}")
        print("=" * 70)

        all_ok = True
        messages = []

        for step in required_steps:
            if step == "politicians":
                ok, msg = DependencyChecker.check_politicians_populated()
            elif step == "financial":
                ok, msg = DependencyChecker.check_financial_populated()
            elif step == "electoral":
                ok, msg = DependencyChecker.check_electoral_populated()
            elif step == "networks":
                ok, msg = DependencyChecker.check_networks_populated()
            elif step == "postprocess":
                ok, msg = DependencyChecker.check_postprocessing_done()
            elif step == "wealth":
                ok, msg = DependencyChecker.check_wealth_populated()
            elif step == "assets":
                ok, msg = DependencyChecker.check_assets_populated()
            elif step == "professional":
                ok, msg = DependencyChecker.check_professional_populated()
            elif step == "events":
                ok, msg = DependencyChecker.check_events_populated()
            else:
                continue

            if not ok:
                all_ok = False
                print(f"❌ MISSING: {msg}")
                messages.append(msg)
            else:
                print(f"✅ {msg}")

        if not all_ok:
            print("\n" + "🚨" * 35)
            print("🚨 WARNING: Missing required dependencies!")
            print("🚨 This command may fail or produce incomplete results!")
            print("🚨" * 35)
            print("\n📋 Required order:")
            print("   1. python cli4/main.py populate")
            if "financial" in required_steps:
                print("   2. python cli4/main.py populate-financial")
            if "electoral" in required_steps:
                print("   3. python cli4/main.py populate-electoral")
            if "networks" in required_steps:
                print("   4. python cli4/main.py populate-networks")
            if "assets" in required_steps:
                print("   5. python cli4/main.py populate-assets")
            if "professional" in required_steps:
                print("   6. python cli4/main.py populate-professional")
            if "events" in required_steps:
                print("   7. python cli4/main.py populate-events")
            if "postprocess" in required_steps:
                print("   8. python cli4/main.py post-process")
            if "wealth" in required_steps:
                print("   9. python cli4/main.py populate-wealth")
            print("\n⚠️ Continuing anyway... Press Ctrl+C to abort.")
            print("=" * 70)
            print()

            # Give user time to read and abort if needed
            import time
            time.sleep(3)
        else:
            print("\n✅ All dependencies satisfied! Proceeding...")
            print("=" * 70)
            print()