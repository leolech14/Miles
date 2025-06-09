# 🚀 MCP Setup Guide for Miles Repository

## Status: Ready for Implementation

This guide provides step-by-step instructions for setting up Model Context Protocol (MCP) servers for enhanced development capabilities.

## ✅ Completed Items

- [x] Fixed CI/CD pipeline Trivy action version (v0.28.0)
- [x] Created PDF processing script foundation
- [x] Created all_pdfs/ directory structure
- [x] Committed baseline changes

## 🎯 Next Steps (In Priority Order)

### 1. 🗄️ Alternative Database Setup (Start Here)

Since DuckDB MCP is complex to set up, let's start with a local SQLite approach:

```bash
# Install Python dependencies for local database work
pip install sqlite3 duckdb pandas

# Create local database for testing
python -c "
import sqlite3
import duckdb

# Create SQLite database
conn = sqlite3.connect('miles_analytics.db')
conn.execute('CREATE TABLE IF NOT EXISTS test_data (id INTEGER, name TEXT)')
conn.execute('INSERT INTO test_data VALUES (1, \"test\")')
conn.commit()
conn.close()
print('✅ SQLite database created')

# Create DuckDB database
duck_conn = duckdb.connect('miles_analytics.duckdb')
duck_conn.execute('CREATE TABLE IF NOT EXISTS test_data (id INTEGER, name VARCHAR)')
duck_conn.execute('INSERT INTO test_data VALUES (1, \"test\")')
duck_conn.close()
print('✅ DuckDB database created')
"
```

### 2. 🎭 Playwright Setup (Most Likely to Work)

```bash
# Install Playwright
npm install -g playwright
npx playwright install chromium

# Test Playwright
npx playwright --version
```

### 3. 🐘 PostgreSQL Docker Setup

```bash
# Start PostgreSQL with Docker
docker run --name miles-postgres \
  -e POSTGRES_PASSWORD=password123 \
  -e POSTGRES_DB=miles_analytics \
  -p 5432:5432 \
  -d postgres:15

# Test connection
docker exec -it miles-postgres psql -U postgres -d miles_analytics -c "SELECT version();"
```

### 4. 🔧 VS Code Configuration

Create/update your VS Code `settings.json`:

```json
{
  "amp.mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y", "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:password123@localhost:5432/miles_analytics"
      ]
    }
  }
}
```

## 🔍 Verification Steps

1. **Test PostgreSQL Connection**:
   ```bash
   docker ps | grep postgres
   docker logs miles-postgres
   ```

2. **Test Playwright**:
   ```bash
   npx playwright install
   ```

3. **Test VS Code MCP**:
   - Open VS Code
   - Press `Ctrl+Shift+P` → "Developer: Reload Window"
   - Check Output → Amp for connection status

## 🚧 Current Blockers

1. **DuckDB MCP**: Package name unclear, requires investigation
2. **Microsandbox**: Needs global installation and port configuration
3. **Settings.json**: Need to locate VS Code settings file path

## 📋 Manual Tasks for User

1. **Add PDFs**: Place PDF files in `all_pdfs/` directory
2. **Run PDF Processing**: `python process_pdfs.py`
3. **Configure VS Code**: Update settings.json with MCP servers
4. **Start Docker**: Run PostgreSQL container

## 🎯 Success Criteria

- [ ] PostgreSQL MCP server connected in VS Code
- [ ] Playwright working for screenshot testing
- [ ] Local database (SQLite/DuckDB) accessible
- [ ] PDF processing script working with real files
- [ ] Data import/export functionality verified

## 🔄 Next Actions

1. Start PostgreSQL container
2. Configure VS Code settings.json
3. Test MCP connection
4. Process sample PDFs
5. Import data into database
6. Run analytical queries

---

**Ready to proceed with any of these steps when you're ready!**
