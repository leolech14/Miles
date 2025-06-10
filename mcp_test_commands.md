# MCP Test Commands for Miles Bot

## After VS Code Setup & Restart

### 1. Check Available Tools

```
list tools
```

**Expected**: Should show tools from all configured servers

### 2. Test Telegram Connection

```
tg_me()
```

**Expected**: Your Telegram account details

### 3. List Telegram Chats

```
tg_dialogs()
```

**Expected**: Your Telegram conversations (look for Miles bot)

### 4. Test Filesystem Access

```
list_files("/Users/lech/Miles")
```

**Expected**: Miles repository files

### 5. Find Your Miles Bot

```
tg_dialogs()
```

Look for Miles bot in output, note the chat ID or username.

### 6. Send /help Command to Bot

```
tg_send("@YourMilesBotUsername", "/help")
```

**OR with chat ID:**

```
tg_send("CHAT_ID", "/help")
```

### 7. Check Bot Response

```
tg_history("@YourMilesBotUsername", 3)
```

**OR:**

```
tg_history("CHAT_ID", 3)
```

### 8. Test Other Bot Commands

```
tg_send("@YourMilesBotUsername", "/ask")
tg_send("@YourMilesBotUsername", "/sources")
tg_send("@YourMilesBotUsername", "/brain analyze")
```

### 9. Monitor Responses

```
tg_history("@YourMilesBotUsername", 10)
```

## Advanced Testing

### Test Natural Language

```
tg_send("@YourMilesBotUsername", "Are there any good bonuses today?")
```

### Test AI Brain

```
tg_send("@YourMilesBotUsername", "/brain discover")
```

### Check Bot Status

```
tg_send("@YourMilesBotUsername", "/debug")
```
