# Telegram MCP Troubleshooting

## Common Issues & Solutions

### 🔴 Grey Dot (Not Connected)

**Symptoms**: Grey dot next to "telegram" in MCP servers
**Solutions**:

1. Check VS Code Output → Amp for error messages
2. Verify environment variables are exactly correct
3. Restart VS Code completely
4. Re-run authentication command

### 🔴 "Session file not found"

**Symptoms**: Error about missing session
**Solutions**:

1. Re-run the auth command: `npx -y @chaindead/telegram-mcp auth ...`
2. Make sure you completed the verification code step

### 🔴 "Invalid API credentials"

**Symptoms**: 401 errors or authentication failures
**Solutions**:

1. Double-check App ID: `22444301`
2. Double-check API Hash: `dc9ef3af0fd90487e05f1953edc8d496`
3. Verify these match your Telegram app configuration

### 🔴 "No tools found"

**Symptoms**: `list tools` doesn't show Telegram tools
**Solutions**:

1. Wait 30 seconds after VS Code restart
2. Check MCP server status in Amp
3. Verify settings.json syntax is correct

### 🔴 "Cannot send message"

**Symptoms**: `tg_send` fails
**Solutions**:

1. Verify chat ID is correct (use `tg_dialogs()` to find it)
2. Check if you have permission to message that chat
3. Ensure bot username is correct (should start with @)

## Success Indicators

✅ Green dot next to "telegram" in MCP servers
✅ `tg_me()` returns your account info
✅ `tg_dialogs()` shows your chats
✅ `tg_send()` successfully sends messages
