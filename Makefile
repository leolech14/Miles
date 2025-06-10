# 🛡️ Miles Bot - Quality Gates Makefile
# Battle-tested commands to catch CI failures before pushing

.PHONY: help install quality quick fix test lint format type-check security clean docker-build

# Default target
help: ## Show this help message
	@echo "🛡️ Miles Bot - Quality Gates"
	@echo "================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "🎯 Common workflows:"
	@echo "  make quick          # Fast quality check before commit"
	@echo "  make quality        # Full quality gates (what CI runs)"
	@echo "  make fix            # Auto-fix formatting and linting issues"
	@echo "  make backtest       # Comprehensive deployment readiness test"
	@echo "  make pre-deploy     # Complete pre-deployment validation"

# 📦 Installation and setup
install: ## Install development dependencies
	pip install --upgrade pip
	pip install -e .[dev]
	pre-commit install

install-pre-commit: ## Install pre-commit hooks
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

# 🛡️ Quality gate layers
quality: ## Run all quality gates (what CI runs)
	@echo "🛡️ Running all quality gates..."
	python scripts/quality_gates.py

quick: ## Run quick quality checks (fast feedback)
	@echo "⚡ Running quick quality checks..."
	python scripts/quality_gates.py --fast

fix: ## Auto-fix formatting and linting issues
	@echo "🔧 Auto-fixing issues..."
	python scripts/quality_gates.py --fix

# 🚀 Layer 1: Formatting & Style
format: ## Format code with Ruff and Black
	@echo "✨ Formatting code..."
	ruff format .
	black .

lint: ## Lint code with Ruff
	@echo "🔍 Linting code..."
	ruff check . --fix

lint-check: ## Check linting without fixes
	@echo "🔍 Checking linting..."
	ruff check .
	black --check --diff .

# 🧪 Layer 2: Static Analysis & Tests
type-check: ## Run static type checking with MyPy
	@echo "🔍 Running type checking..."
	mypy --strict miles/ --ignore-missing-imports

security: ## Run security scan with Bandit
	@echo "🛡️ Running security scan..."
	bandit -r miles/ -ll

test: ## Run test suite with coverage
	@echo "🧪 Running test suite..."
	pytest --cov=miles --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage (fast)
	@echo "⚡ Running fast tests..."
	pytest -x --tb=short -q

test-natural: ## Test natural language bot functionality
	@echo "🤖 Testing natural language bot..."
	python test_natural_language.py

# 🔧 Specific layer testing
layer1: ## Run Layer 1: Formatting & Style only
	python scripts/quality_gates.py --layer 1

layer2: ## Run Layer 2: Static Analysis & Tests only
	python scripts/quality_gates.py --layer 2

layer3: ## Run Layer 3: CI & Workflow Validation only
	python scripts/quality_gates.py --layer 3

# 🐳 Docker operations
docker-build: ## Build Docker image (original bot)
	@echo "🐳 Building Docker image..."
	docker build -t miles-bot .

docker-build-natural: ## Build Docker image (natural language bot)
	@echo "🤖 Building natural language Docker image..."
	docker build -f Dockerfile.natural -t miles-bot-natural .

docker-test: ## Test in Docker environment
	@echo "🐳 Testing in Docker..."
	docker-compose -f docker-compose.natural.yml up --build -d
	docker-compose -f docker-compose.natural.yml logs
	docker-compose -f docker-compose.natural.yml down

# 🧹 Cleanup
clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	find . -name "coverage.xml" -delete 2>/dev/null || true

clean-docker: ## Clean up Docker images and containers
	@echo "🐳 Cleaning Docker..."
	docker system prune -f
	docker image prune -f

# 📊 Coverage and reports
coverage: ## Generate coverage report
	@echo "📊 Generating coverage report..."
	pytest --cov=miles --cov-report=html --cov-report=xml
	@echo "📊 Coverage report available at htmlcov/index.html"

coverage-open: coverage ## Generate and open coverage report
	@echo "🌐 Opening coverage report..."
	python -c "import webbrowser; webbrowser.open('htmlcov/index.html')"

# 🚀 CI simulation
ci-simulation: ## Simulate CI pipeline locally
	@echo "🤖 Simulating CI pipeline..."
	@echo "This runs the same checks as GitHub Actions"
	make quality
	make docker-build
	make docker-build-natural
	@echo "✅ CI simulation complete!"

# 🔄 Deployment Backtesting
backtest: ## Run comprehensive deployment readiness backtest
	@echo "🔄 Running deployment backtest..."
	python scripts/backtest_deployment.py

backtest-quick: ## Run quick deployment readiness check
	@echo "🚀 Running quick backtest..."
	python scripts/backtest_deployment.py --quiet

backtest-monitor: ## Start continuous monitoring (Ctrl+C to stop)
	@echo "🔄 Starting continuous monitoring..."
	python scripts/continuous_monitor.py

backtest-monitor-fast: ## Start fast continuous monitoring (1 min intervals)
	@echo "🚀 Starting fast monitoring..."
	python scripts/continuous_monitor.py --interval 60

# 🎯 Pre-deployment validation
pre-deploy: backtest docker-build docker-build-natural ## Complete pre-deployment validation
	@echo "🎯 Pre-deployment validation complete!"
	@echo "✅ Ready for deployment!"

# 🔧 Setup enhanced pre-commit hooks
setup-hooks: ## Setup enhanced pre-commit hooks
	@echo "🔧 Setting up enhanced pre-commit hooks..."
	cp .pre-commit-config-enhanced.yaml .pre-commit-config.yaml
	pre-commit install
	pre-commit install --hook-type pre-push
	@echo "✅ Enhanced hooks installed!"

# 🔄 Pre-commit operations
pre-commit-run: ## Run pre-commit hooks on all files
	@echo "🔄 Running pre-commit hooks..."
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks to latest versions
	@echo "🔄 Updating pre-commit hooks..."
	pre-commit autoupdate

# 📈 Performance and benchmarks
benchmark: ## Run performance benchmarks
	@echo "📈 Running benchmarks..."
	python -m pytest tests/ -k "benchmark" --benchmark-only || echo "No benchmark tests found"

profile: ## Profile the application
	@echo "📈 Profiling application..."
	python -m cProfile -o profile.stats -m miles.bonus_alert_bot || echo "Run with proper entry point"

# 🎯 Development workflows
dev-setup: install install-pre-commit ## Complete development setup
	@echo "🎯 Development environment ready!"

ready-to-push: quality ## Check if code is ready to push
	@echo "🚀 Code quality check complete!"
	@echo "✅ Ready to push to repository"

# 📋 Information commands
versions: ## Show tool versions
	@echo "📋 Tool versions:"
	@python --version || echo "Python: not found"
	@ruff --version || echo "Ruff: not found"
	@black --version || echo "Black: not found"
	@mypy --version || echo "MyPy: not found"
	@pytest --version || echo "Pytest: not found"
	@bandit --version || echo "Bandit: not found"

check-deps: ## Check if all dependencies are installed
	@echo "🔧 Checking dependencies..."
	@python scripts/quality_gates.py --help > /dev/null && echo "✅ Quality gates script ready"

# 🌟 Special targets
first-time: dev-setup quality ## First-time setup and validation
	@echo "🌟 Welcome to Miles development!"
	@echo "✅ Environment setup complete"
	@echo "✅ Quality gates passing"
	@echo "🚀 You're ready to develop!"

# Environment file setup
env-setup: ## Create sample environment files
	@echo "📄 Creating sample environment files..."
	@cp .env.natural .env.sample 2>/dev/null || echo ".env.natural not found"
	@echo "✅ Edit .env.sample with your values, then copy to .env"
