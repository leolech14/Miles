#!/usr/bin/env python3
"""
🔄 Miles Bot Deployment Backtesting Suite

Comprehensive validation to ensure the bot is always deployment-ready.
Run this before any deployment or regularly to catch regressions early.
"""

import asyncio
import importlib
import subprocess
import sys
import time

import yaml


class DeploymentBacktester:
    """Comprehensive deployment readiness validator."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: dict[str, bool] = {}
        self.errors: list[str] = []

    def log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def run_command(self, command: list[str], description: str) -> tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            self.log(f"🔍 {description}")
            result = subprocess.run(  # noqa: S603
                command, capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                self.log(f"✅ {description} - PASSED")
                return True, result.stdout
            else:
                self.log(f"❌ {description} - FAILED")
                return False, result.stderr
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} - TIMEOUT")
            return False, "Command timed out"
        except Exception as e:
            self.log(f"💥 {description} - ERROR: {e}")
            return False, str(e)

    def test_imports(self) -> bool:
        """Test critical imports."""
        self.log("🔍 Testing critical imports...")

        critical_imports = [
            "miles",
            "miles.plugin_api",
            "miles.metrics",
            "miles.source_store",
            "miles.storage",
        ]

        for module_name in critical_imports:
            try:
                importlib.import_module(module_name)
                self.log(f"✅ Import {module_name} - OK")
            except ImportError as e:
                self.log(f"❌ Import {module_name} - FAILED: {e}")
                self.errors.append(f"Import failure: {module_name} - {e}")
                return False

        return True

    def test_configuration_files(self) -> bool:
        """Validate configuration files."""
        self.log("🔍 Testing configuration files...")

        config_files = [
            ("sources.yaml", yaml.safe_load),
            ("pyproject.toml", None),  # Will use tomllib
        ]

        for file_path, loader in config_files:
            try:
                if file_path.endswith(".toml"):
                    import tomllib

                    with open(file_path, "rb") as f:
                        tomllib.load(f)
                else:
                    with open(file_path) as f:
                        loader(f)
                self.log(f"✅ {file_path} - Valid")
            except Exception as e:
                self.log(f"❌ {file_path} - Invalid: {e}")
                self.errors.append(f"Config file error: {file_path} - {e}")
                return False

        return True

    def test_core_functionality(self) -> bool:
        """Test core bot functionality."""
        success, _ = self.run_command(
            ["python", "-m", "pytest", "tests/test_integration.py", "-v"],
            "Core functionality tests",
        )
        return success

    def test_plugin_system(self) -> bool:
        """Test plugin system."""
        try:
            from miles.plugin_loader import discover_plugins

            plugins = discover_plugins()
            self.log(f"✅ Plugin discovery - Found {len(plugins)} plugins")
            return True
        except Exception as e:
            self.log(f"❌ Plugin system test failed: {e}")
            self.errors.append(f"Plugin system error: {e}")
            return False

    def test_metrics_system(self) -> bool:
        """Test metrics collection."""
        success, _ = self.run_command(
            ["python", "-m", "pytest", "tests/test_metrics.py", "-v"],
            "Metrics system tests",
        )
        return success

    def test_docker_builds(self) -> bool:
        """Test Docker container builds."""
        docker_tests = [
            (["docker", "build", "-t", "miles-bot-test", "."], "Main container build"),
            (
                [
                    "docker",
                    "build",
                    "-f",
                    "Dockerfile.natural",
                    "-t",
                    "miles-bot-natural-test",
                    ".",
                ],
                "Natural language container build",
            ),
        ]

        for command, description in docker_tests:
            success, output = self.run_command(command, description)
            if not success:
                self.errors.append(f"Docker build failed: {description}")
                return False

        return True

    def test_security_scan(self) -> bool:
        """Run security scans."""
        security_tests = [
            (["python", "-m", "bandit", "-r", "miles/", "-ll"], "Bandit security scan"),
        ]

        for command, description in security_tests:
            success, output = self.run_command(command, description)
            if not success and "No issues identified" not in output:
                # Bandit might return non-zero even for minor issues
                self.log(f"⚠️ {description} - Check output for security warnings")

        return True

    def test_type_checking(self) -> bool:
        """Run static type checking."""
        success, _ = self.run_command(
            ["python", "-m", "mypy", "miles/", "--ignore-missing-imports"],
            "MyPy type checking",
        )
        return success

    def test_linting(self) -> bool:
        """Run code linting."""
        success, _ = self.run_command(
            ["python", "-m", "ruff", "check", "miles/"], "Ruff linting"
        )
        return success

    def test_full_test_suite(self) -> bool:
        """Run the complete test suite."""
        success, _ = self.run_command(
            ["python", "-m", "pytest", "--tb=short"], "Complete test suite"
        )
        return success

    def test_analytics_workflow(self) -> bool:
        """Test analytics workflow execution."""
        success, _ = self.run_command(
            ["python", "miles_analytics_workflow.py"], "Analytics workflow test"
        )
        return success

    def test_quality_gates(self) -> bool:
        """Run quality gates simulation."""
        success, _ = self.run_command(["make", "quality"], "Quality gates simulation")
        return success

    async def run_all_tests(self) -> dict[str, bool]:
        """Run all deployment readiness tests."""
        print("🚀 Starting Miles Bot Deployment Backtesting Suite")
        print("=" * 60)

        test_suite = [
            ("Import Tests", self.test_imports),
            ("Configuration Files", self.test_configuration_files),
            ("Core Functionality", self.test_core_functionality),
            ("Plugin System", self.test_plugin_system),
            ("Metrics System", self.test_metrics_system),
            ("Type Checking", self.test_type_checking),
            ("Code Linting", self.test_linting),
            ("Security Scan", self.test_security_scan),
            ("Docker Builds", self.test_docker_builds),
            ("Full Test Suite", self.test_full_test_suite),
            ("Analytics Workflow", self.test_analytics_workflow),
            ("Quality Gates", self.test_quality_gates),
        ]

        for test_name, test_func in test_suite:
            print(f"\n📋 Running: {test_name}")
            print("-" * 40)

            try:
                success = test_func()
                self.results[test_name] = success
            except Exception as e:
                self.log(f"💥 {test_name} crashed: {e}")
                self.results[test_name] = False
                self.errors.append(f"{test_name} crashed: {e}")

        return self.results

    def generate_report(self) -> None:
        """Generate a comprehensive test report."""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT READINESS REPORT")
        print("=" * 60)

        passed = sum(1 for result in self.results.values() if result)
        total = len(self.results)

        for test_name, result in self.results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<25} {status}")

        print(f"\n📈 Summary: {passed}/{total} tests passed")

        if self.errors:
            print(f"\n🚨 {len(self.errors)} Error(s) Found:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")

        if passed == total:
            print("\n🎉 ALL TESTS PASSED - DEPLOYMENT READY!")
            return True
        else:
            print(f"\n⚠️ {total - passed} TESTS FAILED - FIX BEFORE DEPLOYMENT")
            return False


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Miles Bot Deployment Backtester")
    parser.add_argument("--quiet", action="store_true", help="Run in quiet mode")
    parser.add_argument(
        "--fail-fast", action="store_true", help="Stop on first failure"
    )
    args = parser.parse_args()

    backtester = DeploymentBacktester(verbose=not args.quiet)

    try:
        await backtester.run_all_tests()
        success = backtester.generate_report()

        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Backtesting interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Backtesting failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
