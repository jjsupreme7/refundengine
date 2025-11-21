#!/usr/bin/env python3
"""
Setup Verification Script
Checks that all 4 critical components are properly installed and configured
"""
import os
import subprocess
import sys
from pathlib import Path


def print_header(text):
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def check_command(command, name):
    """Check if a command exists"""
    try:
        result = subprocess.run(
            [command, "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(f"✅ {name}: Installed")
            return True
        else:
            print(f"❌ {name}: Not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"❌ {name}: Not found")
        return False


def check_python_package(package, name):
    """Check if Python package is installed"""
    try:
        __import__(package)
        print(f"✅ {name}: Installed")
        return True
    except ImportError:
        print(f"❌ {name}: Not installed")
        return False


def check_file(filepath, name):
    """Check if file exists"""
    if Path(filepath).exists():
        print(f"✅ {name}: Found")
        return True
    else:
        print(f"❌ {name}: Missing")
        return False


def check_env_var(var, name):
    """Check if environment variable is set"""
    if os.getenv(var):
        print(f"✅ {name}: Set")
        return True
    else:
        print(f"❌ {name}: Not set")
        return False


def main():
    print_header("Refund Engine Setup Verification")

    all_checks = []

    # 1. Testing Framework
    print_header("1. Testing Framework")
    all_checks.append(check_python_package("pytest", "pytest"))
    all_checks.append(check_python_package("coverage", "coverage"))
    all_checks.append(check_file("pytest.ini", "pytest.ini"))
    all_checks.append(check_file("tests/conftest.py", "Test fixtures"))
    all_checks.append(check_file("tests/test_refund_calculations.py", "Refund tests"))

    # 2. Message Queue
    print_header("2. Message Queue (Celery + Redis)")
    all_checks.append(check_python_package("celery", "Celery"))
    all_checks.append(check_python_package("redis", "Redis Python client"))
    all_checks.append(check_file("tasks.py", "Celery tasks"))
    all_checks.append(check_file("scripts/async_analyzer.py", "Async analyzer"))

    # Check if Redis is running
    try:
        import redis as redis_pkg

        r = redis_pkg.Redis(host="localhost", port=6379, socket_connect_timeout=1)
        r.ping()
        print("✅ Redis server: Running")
        all_checks.append(True)
    except Exception:
        print("❌ Redis server: Not running (start with: redis-server)")
        all_checks.append(False)

    # 3. Docker
    print_header("3. Docker")
    all_checks.append(check_command("docker", "Docker"))
    all_checks.append(check_command("docker-compose", "Docker Compose"))
    all_checks.append(check_file("Dockerfile", "Dockerfile"))
    all_checks.append(check_file("docker-compose.yml", "docker-compose.yml"))
    all_checks.append(check_file(".dockerignore", ".dockerignore"))

    # 4. CI/CD
    print_header("4. CI/CD (GitHub Actions)")
    all_checks.append(check_file(".github/workflows/test.yml", "Test workflow"))
    all_checks.append(check_file(".github/workflows/docker.yml", "Docker workflow"))

    # 5. Environment Configuration
    print_header("5. Environment Configuration")
    all_checks.append(check_file(".env", ".env file"))
    all_checks.append(check_env_var("OPENAI_API_KEY", "OPENAI_API_KEY"))
    all_checks.append(check_env_var("SUPABASE_URL", "SUPABASE_URL"))
    all_checks.append(check_env_var("SUPABASE_KEY", "SUPABASE_KEY"))

    # 6. Core Dependencies
    print_header("6. Core Dependencies")
    all_checks.append(check_python_package("openai", "OpenAI"))
    all_checks.append(check_python_package("supabase", "Supabase"))
    all_checks.append(check_python_package("pandas", "Pandas"))
    all_checks.append(check_python_package("pdfplumber", "PDF parsing"))

    # 7. Documentation
    print_header("7. Documentation")
    all_checks.append(check_file("TESTING_GUIDE.md", "Testing guide"))
    all_checks.append(check_file("ASYNC_PROCESSING_GUIDE.md", "Async guide"))
    all_checks.append(check_file("DOCKER_GUIDE.md", "Docker guide"))
    all_checks.append(check_file("PRODUCTION_SETUP.md", "Production guide"))
    all_checks.append(check_file("SIMPLE_EXPLANATION.md", "Simple explanation"))

    # Summary
    print_header("Setup Verification Summary")

    passed = sum(all_checks)
    total = len(all_checks)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"Passed: {passed}/{total} ({percentage:.1f}%)\n")

    if percentage == 100:
        print("🎉 Perfect! All components are installed and configured.")
        print("\n📚 Next Steps:")
        print("   1. Run tests: pytest")
        print("   2. Start Docker: docker-compose up")
        print(
            "   3. Process invoices: docker-compose run app python scripts/async_analyzer.py --excel file.xlsx"
        )
        print(
            "\n📖 Read: SIMPLE_EXPLANATION.md for details on what each component does"
        )
        return 0
    elif percentage >= 80:
        print("⚠️  Most components ready, but some are missing.")
        print("\n📖 Check the ❌ items above and:")
        print("   - Install missing packages: pip install -r requirements.txt")
        print("   - Create .env file: cp .env.example .env")
        print("   - Start Redis: redis-server (or docker-compose up redis)")
        return 1
    else:
        print("❌ Setup incomplete. Several components are missing.")
        print("\n📖 Follow: PRODUCTION_SETUP.md for complete installation guide")
        return 1


if __name__ == "__main__":
    sys.exit(main())
