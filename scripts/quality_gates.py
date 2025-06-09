#!/usr/bin/env python3
"""
🛡️ Miles Quality Gates - Battle-tested CI/CD Protection

This script runs the same quality checks that CI runs, catching 95% of
"why-did-CI-break?" problems before you push.

Usage:
    python scripts/quality_gates.py          # Run all checks
    python scripts/quality_gates.py --fast   # Skip slow tests
    python scripts/quality_gates.py --fix    # Auto-fix issues where possible
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_banner():
    """Print the quality gates banner."""
    print(
        f"""
    {Colors.CYAN}╔═══════════════════════════════════════════════════════════════╗{Colors.END}
    {Colors.CYAN}║                                                               ║{Colors.END}
    {Colors.CYAN}║   {Colors.BOLD}🛡️  Miles Quality Gates - Battle-tested Protection{Colors.END}    {Colors.CYAN}║{Colors.END}
    {Colors.CYAN}║                                                               ║{Colors.END}
    {Colors.CYAN}║   {Colors.WHITE}Catch 95% of CI failures before you push{Colors.END}               {Colors.CYAN}║{Colors.END}
    {Colors.CYAN}║                                                               ║{Colors.END}
    {Colors.CYAN}╚═══════════════════════════════════════════════════════════════╝{Colors.END}
    """
    )


def run_command(
    cmd: list[str], description: str, fix_mode: bool = False
) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"\n{Colors.BLUE}🔍 {description}...{Colors.END}")

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )  # User command execution
        duration = time.time() - start_time

        if result.returncode == 0:
            print(
                f"{Colors.GREEN}✅ {description} passed ({duration:.1f}s){Colors.END}"
            )
            return True, result.stdout
        else:
            print(f"{Colors.RED}❌ {description} failed ({duration:.1f}s){Colors.END}")
            if result.stdout:
                print(f"{Colors.WHITE}STDOUT:{Colors.END}\n{result.stdout}")
            if result.stderr:
                print(f"{Colors.WHITE}STDERR:{Colors.END}\n{result.stderr}")
            return False, result.stderr

    except FileNotFoundError:
        print(f"{Colors.RED}❌ Command not found: {' '.join(cmd)}{Colors.END}")
        print(f"{Colors.YELLOW}💡 Try: pip install -e .[dev]{Colors.END}")
        return False, f"Command not found: {' '.join(cmd)}"


def layer_1_formatting_style(fix_mode: bool = False) -> list[tuple[bool, str]]:
    """🚀 Layer 1: Formatting & Style (Ultra-fast)."""
    print(f"\n{Colors.MAGENTA}{'=' * 60}{Colors.END}")
    print(f"{Colors.MAGENTA}🚀 Layer 1: Formatting & Style{Colors.END}")
    print(f"{Colors.MAGENTA}{'=' * 60}{Colors.END}")

    results = []

    # Ruff linting with optional fixes
    ruff_cmd = ["ruff", "check", "."]
    if fix_mode:
        ruff_cmd.extend(["--fix", "--show-fixes"])
    results.append(run_command(ruff_cmd, "Ruff linting", fix_mode))

    # Ruff formatting
    ruff_format_cmd = ["ruff", "format"]
    if not fix_mode:
        ruff_format_cmd.append("--check")
    results.append(run_command(ruff_format_cmd, "Ruff formatting", fix_mode))

    # Black formatting (backup)
    black_cmd = ["black"]
    if fix_mode:
        black_cmd.append(".")
    else:
        black_cmd.extend(["--check", "--diff", "."])
    results.append(run_command(black_cmd, "Black formatting", fix_mode))

    return results


def layer_2_static_analysis_tests(fast_mode: bool = False) -> list[tuple[bool, str]]:
    """🧪 Layer 2: Static Analysis & Tests."""
    print(f"\n{Colors.MAGENTA}{'=' * 60}{Colors.END}")
    print(f"{Colors.MAGENTA}🧪 Layer 2: Static Analysis & Tests{Colors.END}")
    print(f"{Colors.MAGENTA}{'=' * 60}{Colors.END}")

    results = []

    # MyPy static type checking
    mypy_cmd = ["mypy", "--strict", "miles/", "--ignore-missing-imports"]
    results.append(run_command(mypy_cmd, "MyPy static analysis"))

    # Bandit security scanning
    bandit_cmd = ["bandit", "-r", "miles/", "-ll"]
    results.append(run_command(bandit_cmd, "Bandit security scan"))

    # Pytest with coverage
    if fast_mode:
        pytest_cmd = ["pytest", "-x", "--tb=short", "-q"]
        results.append(run_command(pytest_cmd, "Fast test suite"))
    else:
        pytest_cmd = [
            "pytest",
            "--cov=miles",
            "--cov-report=term-missing",
            "--tb=short",
        ]
        results.append(run_command(pytest_cmd, "Full test suite with coverage"))

    return results


def layer_3_ci_workflow_validation() -> list[tuple[bool, str]]:
    """🔧 Layer 3: CI & Workflow Validation."""
    print(f"\n{Colors.MAGENTA}{'=' * 60}{Colors.END}")
    print(f"{Colors.MAGENTA}🔧 Layer 3: CI & Workflow Validation{Colors.END}")
    print(f"{Colors.MAGENTA}{'=' * 60}{Colors.END}")

    results = []

    # YAML validation
    yaml_files = list(Path(".").rglob("*.yml")) + list(Path(".").rglob("*.yaml"))
    yaml_files = [
        f for f in yaml_files if "test/" not in str(f) and ".venv" not in str(f)
    ]

    for yaml_file in yaml_files[:5]:  # Limit to first 5 files
        yaml_cmd = ["python", "-c", f"import yaml; yaml.safe_load(open('{yaml_file}'))"]
        results.append(run_command(yaml_cmd, f"YAML validation: {yaml_file.name}"))

    # TOML validation (pyproject.toml)
    if Path("pyproject.toml").exists():
        toml_cmd = [
            "python",
            "-c",
            "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))",
        ]
        results.append(run_command(toml_cmd, "TOML validation: pyproject.toml"))

    return results


def test_natural_language_bot() -> list[tuple[bool, str]]:
    """🤖 Test Natural Language Bot specific functionality."""
    print(f"\n{Colors.MAGENTA}{'=' * 60}{Colors.END}")
    print(f"{Colors.MAGENTA}🤖 Natural Language Bot Tests{Colors.END}")
    print(f"{Colors.MAGENTA}{'=' * 60}{Colors.END}")

    results = []

    # Test function registry
    test_cmd = [
        "python",
        "-c",
        "from miles.natural_language.function_registry import function_registry; print(f'✅ {len(function_registry.get_function_definitions())} functions loaded')",
    ]
    results.append(run_command(test_cmd, "Function registry loading"))

    # Test conversation manager
    test_cmd = [
        "python",
        "-c",
        "from miles.natural_language.conversation_manager import conversation_manager; print('✅ Conversation manager initialized')",
    ]
    results.append(run_command(test_cmd, "Conversation manager initialization"))

    # Test natural language configuration
    test_cmd = [
        "python",
        "-c",
        "from natural_language_config import get_natural_language_config; config = get_natural_language_config(); errors = config.validate(); print('✅ Config valid' if not errors else f'❌ Config errors: {errors}')",
    ]
    results.append(run_command(test_cmd, "Natural language configuration"))

    return results


def check_dependencies() -> bool:
    """Check if all required tools are installed."""
    print(f"\n{Colors.BLUE}🔧 Checking dependencies...{Colors.END}")

    required_tools = [
        ("python", "Python interpreter"),
        ("ruff", "Ruff linter/formatter"),
        ("black", "Black formatter"),
        ("mypy", "MyPy type checker"),
        ("pytest", "Pytest test runner"),
        ("bandit", "Bandit security scanner"),
    ]

    missing_tools = []
    for tool, description in required_tools:
        try:
            subprocess.run(
                [tool, "--version"], capture_output=True, check=True
            )  # Tool availability check
            print(f"{Colors.GREEN}✅ {description}{Colors.END}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{Colors.RED}❌ {description} not found{Colors.END}")
            missing_tools.append(tool)

    if missing_tools:
        print(f"\n{Colors.YELLOW}💡 Install missing tools with:{Colors.END}")
        print(f"{Colors.WHITE}pip install -e .[dev]{Colors.END}")
        return False

    return True


def main():
    """Main quality gates runner."""
    parser = argparse.ArgumentParser(description="Run Miles quality gates")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues where possible"
    )
    parser.add_argument(
        "--layer", choices=["1", "2", "3"], help="Run specific layer only"
    )
    args = parser.parse_args()

    print_banner()

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    all_results = []
    start_time = time.time()

    # Run quality gate layers
    if not args.layer or args.layer == "1":
        all_results.extend(layer_1_formatting_style(args.fix))

    if not args.layer or args.layer == "2":
        all_results.extend(layer_2_static_analysis_tests(args.fast))
        all_results.extend(test_natural_language_bot())

    if not args.layer or args.layer == "3":
        all_results.extend(layer_3_ci_workflow_validation())

    # Summary
    total_time = time.time() - start_time
    passed = sum(1 for success, _ in all_results if success)
    total = len(all_results)

    print(f"\n{Colors.MAGENTA}{'=' * 60}{Colors.END}")
    print(f"{Colors.MAGENTA}📊 Quality Gates Summary{Colors.END}")
    print(f"{Colors.MAGENTA}{'=' * 60}{Colors.END}")

    if passed == total:
        print(
            f"{Colors.GREEN}🎉 All {total} checks passed! ({total_time:.1f}s){Colors.END}"
        )
        print(f"{Colors.GREEN}✅ Ready to push to CI{Colors.END}")
        sys.exit(0)
    else:
        failed = total - passed
        print(
            f"{Colors.RED}❌ {failed}/{total} checks failed ({total_time:.1f}s){Colors.END}"
        )
        print(f"{Colors.YELLOW}💡 Fix issues above before pushing{Colors.END}")

        if not args.fix:
            print(
                f"{Colors.YELLOW}💡 Try running with --fix to auto-fix some issues{Colors.END}"
            )

        sys.exit(1)


if __name__ == "__main__":
    main()
