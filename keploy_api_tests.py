#!/usr/bin/env python3
"""
Keploy API Test Client

This script makes API calls to the Miles bot test server
that Keploy can record and replay for automated testing.
"""

import requests
import time
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8080"


def make_request(
    method: str, endpoint: str, data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Make HTTP request and return JSON response"""
    url = f"{BASE_URL}{endpoint}"

    print(f"🌐 {method} {endpoint}")

    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, json=data)
    else:
        raise ValueError(f"Unsupported method: {method}")

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
        return result
    else:
        print(f"   Error: {response.text}")
        return {"error": response.text}


def run_api_tests():
    """Run a series of API tests for Keploy to record"""

    print("🧪 Running Miles Bot API Tests for Keploy Recording\n")

    # Test 1: Health check
    print("=" * 50)
    print("TEST 1: Health Check")
    make_request("GET", "/")
    time.sleep(1)

    # Test 2: Get sources
    print("\n" + "=" * 50)
    print("TEST 2: Get Sources")
    make_request("GET", "/sources")
    time.sleep(1)

    # Test 3: Add a new source
    print("\n" + "=" * 50)
    print("TEST 3: Add Source")
    make_request("POST", "/sources", {"url": "https://test-keploy.com"})
    time.sleep(1)

    # Test 4: Get sources again (should include new one)
    print("\n" + "=" * 50)
    print("TEST 4: Get Sources (Updated)")
    make_request("GET", "/sources")
    time.sleep(1)

    # Test 5: Run manual scan
    print("\n" + "=" * 50)
    print("TEST 5: Manual Scan")
    make_request("POST", "/scan", {"min_bonus": 90})
    time.sleep(1)

    # Test 6: Get plugins
    print("\n" + "=" * 50)
    print("TEST 6: Get Plugins")
    make_request("GET", "/plugins")
    time.sleep(1)

    # Test 7: Get metrics
    print("\n" + "=" * 50)
    print("TEST 7: Get Metrics")
    make_request("GET", "/metrics")
    time.sleep(1)

    # Test 8: Test notification
    print("\n" + "=" * 50)
    print("TEST 8: Test Notification")
    make_request("POST", "/test-notification")
    time.sleep(1)

    print("\n🎉 All API tests completed!")
    print("📝 Keploy should have recorded these interactions")


if __name__ == "__main__":
    try:
        run_api_tests()
    except requests.exceptions.ConnectionError:
        print(
            "❌ Connection error: Make sure the test server is running on localhost:8080"
        )
        print("💡 Start it with: python keploy_test_server.py")
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
