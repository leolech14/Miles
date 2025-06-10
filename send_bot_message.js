// Quick test script to send message to Miles bot
const { spawn } = require("child_process");

console.log("🚀 Testing message sending to Miles bot...");

// First, let's try to get a more complete dialog list
const getDialogs = spawn(
  "npx",
  [
    "-y",
    "@chaindead/telegram-mcp",
    "--app-id",
    "22444301",
    "--api-hash",
    "dc9ef3af0fd90487e05f1953edc8d496",
    "--dry",
  ],
  {
    env: { ...process.env },
  },
);

getDialogs.stdout.on("data", (data) => {
  console.log(`📋 Dialogs: ${data}`);
});

getDialogs.stderr.on("data", (data) => {
  console.log(`🔍 Info: ${data}`);
});

getDialogs.on("close", (code) => {
  console.log(`✅ Dialog check completed with code ${code}`);
});
