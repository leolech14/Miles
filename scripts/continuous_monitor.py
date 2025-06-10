#!/usr/bin/env python3
"""
🔄 Continuous Deployment Readiness Monitor

Runs lightweight checks every few minutes to ensure the codebase
remains deployment-ready. Great for development environments.
"""

import asyncio
from datetime import datetime

from backtest_deployment import DeploymentBacktester


class ContinuousMonitor:
    """Lightweight continuous monitoring for deployment readiness."""

    def __init__(self, check_interval: int = 300):  # 5 minutes default
        self.check_interval = check_interval
        self.last_check = None
        self.consecutive_failures = 0
        self.max_failures = 3

    async def quick_health_check(self) -> dict[str, bool]:
        """Run a quick subset of tests for continuous monitoring."""
        backtester = DeploymentBacktester(verbose=False)

        # Only run fast, essential checks
        quick_tests = [
            ("Imports", backtester.test_imports),
            ("Config Files", backtester.test_configuration_files),
            ("Plugin System", backtester.test_plugin_system),
            ("Type Checking", backtester.test_type_checking),
        ]

        results = {}
        for test_name, test_func in quick_tests:
            try:
                results[test_name] = test_func()
            except Exception:
                results[test_name] = False

        return results

    def log_status(self, results: dict[str, bool]) -> None:
        """Log current status with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        passed = sum(1 for result in results.values() if result)
        total = len(results)

        if passed == total:
            status = "🟢 HEALTHY"
            self.consecutive_failures = 0
        else:
            status = "🔴 ISSUES DETECTED"
            self.consecutive_failures += 1

        print(f"[{timestamp}] {status} - {passed}/{total} checks passed")

        # Show failed tests
        for test_name, result in results.items():
            if not result:
                print(f"  ❌ {test_name}")

        # Alert on consecutive failures
        if self.consecutive_failures >= self.max_failures:
            print(f"🚨 ALERT: {self.consecutive_failures} consecutive failures!")
            print(
                "Consider running full backtest: python scripts/backtest_deployment.py"
            )

    async def run_monitoring_loop(self) -> None:
        """Run continuous monitoring loop."""
        print("🔄 Starting continuous deployment readiness monitoring...")
        print(f"⏰ Check interval: {self.check_interval} seconds")
        print("Press Ctrl+C to stop")
        print("-" * 50)

        while True:
            try:
                results = await self.quick_health_check()
                self.log_status(results)
                self.last_check = datetime.now()

                await asyncio.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"💥 Monitor error: {e}")
                await asyncio.sleep(30)  # Wait before retrying


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Continuous Deployment Monitor")
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)",
    )
    args = parser.parse_args()

    monitor = ContinuousMonitor(check_interval=args.interval)
    await monitor.run_monitoring_loop()


if __name__ == "__main__":
    asyncio.run(main())
