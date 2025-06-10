# VS Code MCP Configuration for Telegram

## Step 1: Open VS Code Settings

1. **Open VS Code**
2. **Press**: `Cmd+,` (Mac) or `Ctrl+,` (Windows)
3. **Click**: "Open Settings (JSON)" icon (top right corner)

## Step 2: Add MCP Server Configuration

Add this to your `settings.json`:

```json
{
  "amp.mcpServers": {
    "telegram": {
      "command": "npx",
      "args": ["-y", "@chaindead/telegram-mcp"],
      "env": {
        "TG_APP_ID": "22444301",
        "TG_API_HASH": "dc9ef3af0fd90487e05f1953edc8d496"
      }
    }
  }
}
```

## Step 3: Restart VS Code

- **Close VS Code completely**
- **Reopen VS Code**
- **Wait 10-15 seconds** for MCP server to initialize

## Step 4: Check Connection Status

In VS Code:

1. **Open Amp chat**
2. **Look for green dot** next to "telegram" in MCP servers list
3. **If grey/red**: Check Output → Amp for error messages

## Step 5: Test Connection

In Amp chat, type:

```
list tools
```

You should see Telegram tools like:

- `tg_me`
- `tg_dialogs`
- `tg_send`
- `tg_history`
