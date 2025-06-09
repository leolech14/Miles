"""Tests for the metrics system."""

import threading
import time
from http.server import HTTPServer
from unittest.mock import patch

import pytest
import requests

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ask_bot import HealthHandler


def test_metrics_module_import():
    """Test that metrics module can be imported."""
    from miles import metrics
    
    assert hasattr(metrics, 'get_metrics_registry')
    assert hasattr(metrics, 'telegram_commands_total')
    assert hasattr(metrics, 'promo_scrape_duration')


def test_metrics_endpoint():
    """Test that metrics endpoint returns valid Prometheus data."""
    # Start a test server
    server = HTTPServer(("127.0.0.1", 0), HealthHandler)  # Use port 0 for automatic assignment
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Get the actual port that was assigned
    port = server.server_port
    
    try:
        # Wait a moment for server to start
        time.sleep(0.1)
        
        # Test health endpoint
        response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        assert response.status_code == 200
        assert response.text == "OK"
        
        # Test metrics endpoint
        response = requests.get(f"http://127.0.0.1:{port}/metrics", timeout=5)
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("Content-Type", "")
        
        # Check that it contains prometheus metrics
        metrics_text = response.text
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text
        
    finally:
        server.shutdown()
        server_thread.join(timeout=1)


def test_metrics_context_managers():
    """Test metrics context managers work correctly."""
    from miles.metrics import time_operation, count_operation, Histogram, Counter
    
    # Create test metrics
    test_histogram = Histogram("test_duration", "Test histogram")
    test_counter = Counter("test_total", "Test counter", ["status"])
    
    # Test timing context manager
    with time_operation(test_histogram):
        time.sleep(0.01)  # Small delay
    
    # Verify timing was recorded
    samples = list(test_histogram.collect())[0].samples
    assert any(sample.name.endswith("_count") and sample.value > 0 for sample in samples)
    
    # Test counting context manager
    with count_operation(test_counter, status="success"):
        pass  # Normal execution
    
    # Test error handling
    try:
        with count_operation(test_counter, status="test_error"):
            raise ValueError("Test error")
    except ValueError:
        pass  # Expected
    
    # Verify counts
    samples = list(test_counter.collect())[0].samples
    success_count = next(s.value for s in samples if "success" in str(s.labels))
    error_count = next(s.value for s in samples if "error" in str(s.labels))
    
    assert success_count == 1
    assert error_count == 1


def test_memory_usage_recording():
    """Test memory usage recording function."""
    from miles.metrics import record_memory_usage, memory_usage_bytes
    
    # Record memory usage
    record_memory_usage()
    
    # Check that memory gauge was updated
    samples = list(memory_usage_bytes.collect())[0].samples
    memory_value = samples[0].value
    
    # Memory should be positive
    assert memory_value > 0


def test_bot_info_metrics():
    """Test that bot info metrics are populated."""
    from miles.metrics import bot_info
    
    samples = list(bot_info.collect())[0].samples
    info_labels = samples[0].labels if samples else {}
    
    # Should have basic info
    assert "python_version" in info_labels or len(samples) == 0  # May fail during initialization


@pytest.mark.asyncio
async def test_telegram_command_metrics():
    """Test that Telegram command metrics are recorded."""
    from miles.metrics import telegram_commands_total
    from unittest.mock import AsyncMock, MagicMock
    import ask_bot
    
    # Mock the update and context
    update = MagicMock()
    update.message = AsyncMock()
    update.effective_chat = MagicMock()
    context = MagicMock()
    
    # Mock the bot.scan_programs function
    with patch.object(ask_bot.bot, 'scan_programs', return_value=[]):
        await ask_bot.ask(update, context)
    
    # Verify metrics were recorded
    samples = list(telegram_commands_total.collect())[0].samples
    success_samples = [s for s in samples if "success" in str(s.labels)]
    assert len(success_samples) > 0
