# 🔄 Deployment Backtesting System

Comprehensive automated validation to ensure Miles bot is always deployment-ready.

## 🎯 Overview

The backtesting system provides multiple layers of validation to catch issues before they reach production:

1. **Continuous Monitoring** - Lightweight checks every few minutes during development
2. **Pre-commit Hooks** - Validation before code commits
3. **GitHub Actions** - Automated CI/CD pipeline validation
4. **Manual Backtesting** - On-demand comprehensive validation

## 🚀 Quick Start

### Run Full Backtest

```bash
make backtest
```

### Quick Health Check

```bash
make backtest-quick
```

### Pre-deployment Validation

```bash
make pre-deploy
```

### Start Continuous Monitoring

```bash
make backtest-monitor
```

## 🛠️ Available Commands

| Command                      | Description                            | Duration   |
| ---------------------------- | -------------------------------------- | ---------- |
| `make backtest`              | Full deployment readiness test         | ~5-10 min  |
| `make backtest-quick`        | Quick health check                     | ~30 sec    |
| `make backtest-monitor`      | Continuous monitoring (5min intervals) | Ongoing    |
| `make backtest-monitor-fast` | Fast monitoring (1min intervals)       | Ongoing    |
| `make pre-deploy`            | Complete pre-deployment validation     | ~10-15 min |
| `make setup-hooks`           | Install enhanced pre-commit hooks      | ~30 sec    |

## 🔍 What Gets Tested

### Core Functionality

- ✅ **Import Tests** - All critical modules load correctly
- ✅ **Configuration Validation** - YAML/TOML files are valid
- ✅ **Plugin System** - Plugin discovery and loading
- ✅ **Metrics Collection** - Analytics and monitoring systems

### Code Quality

- ✅ **Type Checking** - MyPy static analysis
- ✅ **Linting** - Ruff code quality checks
- ✅ **Security Scanning** - Bandit vulnerability detection
- ✅ **Test Suite** - Full pytest execution with coverage

### Deployment Readiness

- ✅ **Docker Builds** - Both main and natural language containers
- ✅ **Analytics Workflow** - Data processing pipeline
- ✅ **Quality Gates** - All CI checks pass

## 🔄 GitHub Actions Integration

### Automatic Triggers

- **Push to main** - Full validation pipeline
- **Pull requests** - Comprehensive testing
- **Scheduled** - Every 4 hours for regression detection
- **Manual** - On-demand workflow dispatch

### Pipeline Stages

1. **🎯 Smoke Tests** - Quick validation (5 min timeout)
2. **📊 Integration Tests** - Core functionality validation
3. **🐳 Container Tests** - Docker build validation
4. **🔍 Performance Tests** - Regression detection
5. **🌐 E2E Tests** - Complete workflow validation

## 📊 Monitoring & Alerts

### Continuous Monitoring

```bash
# Monitor with default 5-minute intervals
make backtest-monitor

# Fast monitoring with 1-minute intervals
make backtest-monitor-fast
```

### Failure Handling

- **Automatic Issue Creation** - On scheduled test failures
- **Consecutive Failure Alerts** - When multiple checks fail
- **Slack Notifications** - For critical failures (when configured)

## 🔧 Configuration

### Enhanced Pre-commit Hooks

```bash
make setup-hooks
```

This installs enhanced hooks that run:

- Code formatting (Ruff, Black)
- Security scanning (Bandit)
- Type checking (MyPy)
- Quick tests on push
- Docker build validation

### Environment Variables

```bash
# Optional: Configure Slack alerts
export SLACK_WEBHOOK_URL="your-webhook-url"

# Optional: Adjust monitoring intervals
export MONITOR_INTERVAL=300  # seconds
```

## 🎯 Best Practices

### Before Committing

```bash
make backtest-quick  # Quick validation
```

### Before Pushing

```bash
make quality         # Full quality gates
make backtest       # Comprehensive validation
```

### Before Deploying

```bash
make pre-deploy     # Complete pre-deployment validation
```

### During Development

```bash
make backtest-monitor  # Keep running in background
```

## 🚨 Troubleshooting

### Common Issues

**Import Errors**

```bash
pip install -e .[dev]  # Reinstall dependencies
```

**Docker Build Failures**

```bash
make clean-docker      # Clean Docker cache
docker system prune -f # Remove unused containers
```

**Test Failures**

```bash
pytest -v              # Run tests with verbose output
pytest --lf            # Run only last failed tests
```

### Debug Mode

```bash
python scripts/backtest_deployment.py --verbose
```

### Fast Failure Detection

```bash
python scripts/backtest_deployment.py --fail-fast
```

## 📈 Performance Optimization

### Skip Heavy Tests in Development

Use `backtest-quick` for frequent checks during development:

```bash
make backtest-quick
```

### Parallel Testing

The system automatically runs tests in parallel where possible to minimize execution time.

### Caching

- Docker layer caching reduces build times
- pip caching speeds up dependency installation
- pytest caching improves test performance

## 🔮 Advanced Features

### Custom Test Scenarios

Add custom validation by extending `scripts/backtest_deployment.py`:

```python
def test_custom_feature(self) -> bool:
    """Test your custom functionality."""
    # Your validation logic here
    return True
```

### Integration with External Services

Monitor external dependencies and API health as part of the validation pipeline.

### Performance Benchmarking

Track performance metrics over time to detect regressions:

```bash
make benchmark
```

## 🎉 Success Indicators

When all systems are healthy, you'll see:

```
🎉 ALL TESTS PASSED - DEPLOYMENT READY!
✅ Smoke tests: PASSED
✅ Integration tests: PASSED
✅ Container builds: PASSED
✅ Performance benchmarks: PASSED
✅ Quality gates: PASSED
🚀 Miles bot is deployment-ready!
```

This comprehensive backtesting system ensures your Miles bot remains reliable, secure, and ready for production deployment at all times.
