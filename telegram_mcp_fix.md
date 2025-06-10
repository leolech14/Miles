# 🔧 Telegram MCP Server Fix

## Problem Identified

The Telegram MCP server has a deadlock issue causing "connection closed unexpectedly" errors.

## Solution Options

### Option 1: Alternative MCP Configuration (Recommended)

Try this modified VS Code configuration:

```json
{
  "amp.mcpServers": {
    "telegram": {
      "command": "node",
      "args": [
        "-e",
        "const { spawn } = require('child_process'); const proc = spawn('npx', ['-y', '@chaindead/telegram-mcp'], { env: { ...process.env, TG_APP_ID: '22444301', TG_API_HASH: 'dc9ef3af0fd90487e05f1953edc8d496' }, stdio: 'inherit' }); proc.on('close', () => process.exit(0));"
      ],
      "env": {
        "TG_APP_ID": "22444301",
        "TG_API_HASH": "dc9ef3af0fd90487e05f1953edc8d496"
      }
    }
  }
}
```

### Option 2: Simpler Working Configuration

```json
{
  "amp.mcpServers": {
    "telegram": {
      "command": "npx",
      "args": ["-y", "@chaindead/telegram-mcp"],
      "env": {
        "TG_APP_ID": "22444301",
        "TG_API_HASH": "dc9ef3af0fd90487e05f1953edc8d496",
        "TG_SESSION_PATH": "/Users/lech/.telegram-mcp/session.json"
      },
      "restart": true,
      "timeout": 30000
    }
  }
}
```

### Option 3: Manual Testing First

Before VS Code, test manually:

```bash
export TG_APP_ID=22444301
export TG_API_HASH=dc9ef3af0fd90487e05f1953edc8d496
npx -y @chaindead/telegram-mcp
```

## Next Steps

1. Try Option 2 first (simplest)
2. If still fails, try Option 1
3. Report back the results
