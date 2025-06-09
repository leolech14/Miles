#!/usr/bin/env python3
"""
Test script to verify MCP setup and database connections.
"""

import subprocess
import sqlite3
import duckdb
import sys
from typing import Dict, Any

def test_postgresql_connection() -> Dict[str, Any]:
    """Test PostgreSQL connection via Docker."""
    try:
        result = subprocess.run([
            "docker", "exec", "itau-postgres", 
            "psql", "-U", "postgres", "-d", "itau_parser", 
            "-c", "SELECT 'PostgreSQL Connected' as status;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return {"status": "success", "message": "PostgreSQL connection successful"}
        else:
            return {"status": "error", "message": f"PostgreSQL error: {result.stderr}"}
    except Exception as e:
        return {"status": "error", "message": f"PostgreSQL test failed: {str(e)}"}

def test_sqlite_connection() -> Dict[str, Any]:
    """Test local SQLite database."""
    try:
        conn = sqlite3.connect('miles_analytics.db')
        result = conn.execute("SELECT 'SQLite Connected' as status").fetchone()
        conn.close()
        return {"status": "success", "message": f"SQLite: {result[0]}"}
    except Exception as e:
        return {"status": "error", "message": f"SQLite test failed: {str(e)}"}

def test_duckdb_connection() -> Dict[str, Any]:
    """Test local DuckDB database."""
    try:
        conn = duckdb.connect('miles_analytics.duckdb')
        result = conn.execute("SELECT 'DuckDB Connected' as status").fetchone()
        conn.close()
        return {"status": "success", "message": f"DuckDB: {result[0]}"}
    except Exception as e:
        return {"status": "error", "message": f"DuckDB test failed: {str(e)}"}

def test_playwright_mcp() -> Dict[str, Any]:
    """Test Playwright MCP server."""
    try:
        result = subprocess.run([
            "npx", "-y", "@playwright/mcp", "--help"
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            return {"status": "success", "message": "Playwright MCP server available"}
        else:
            return {"status": "error", "message": f"Playwright MCP error: {result.stderr}"}
    except Exception as e:
        return {"status": "error", "message": f"Playwright MCP test failed: {str(e)}"}

def test_postgres_mcp() -> Dict[str, Any]:
    """Test PostgreSQL MCP server."""
    try:
        # Just test if the package is available
        result = subprocess.run([
            "npx", "-y", "@modelcontextprotocol/server-postgres", "--help"
        ], capture_output=True, text=True, timeout=15)
        
        # The server might exit with an error for --help, but package should be found
        if "Cannot find module" not in result.stderr:
            return {"status": "success", "message": "PostgreSQL MCP server package available"}
        else:
            return {"status": "error", "message": f"PostgreSQL MCP package not found"}
    except Exception as e:
        return {"status": "error", "message": f"PostgreSQL MCP test failed: {str(e)}"}

def main():
    """Run all tests and report results."""
    print("🧪 Testing MCP Setup...")
    print("=" * 50)
    
    tests = [
        ("PostgreSQL Connection", test_postgresql_connection),
        ("SQLite Database", test_sqlite_connection),
        ("DuckDB Database", test_duckdb_connection),
        ("Playwright MCP", test_playwright_mcp),
        ("PostgreSQL MCP", test_postgres_mcp),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
        
        if result["status"] == "success":
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    success_count = sum(1 for _, result in results if result["status"] == "success")
    total_count = len(results)
    
    for test_name, result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"  {status_icon} {test_name}")
    
    print(f"\n🎯 {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        print("\n🚀 All systems ready! Your MCP setup is working perfectly.")
        print("\n📋 Next steps:")
        print("  1. Restart VS Code to load new MCP configuration")
        print("  2. Check VS Code Output → Amp for MCP connection status")
        print("  3. Test MCP servers with simple queries")
        print("  4. Add PDFs to all_pdfs/ directory and process them")
    else:
        print(f"\n⚠️  {total_count - success_count} test(s) failed. Check error messages above.")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
