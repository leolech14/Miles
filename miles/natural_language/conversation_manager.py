"""
Natural Language Conversation Manager

Handles all user interactions through OpenAI function calling,
making the bot feel like ChatGPT while maintaining all functionalities.
"""

from __future__ import annotations

import json
import os
from typing import Any, cast

from openai import AsyncOpenAI
from telegram import Update
from telegram.ext import ContextTypes

from miles.chat_store import ChatMemory
from miles.logging_config import setup_logging
from miles.natural_language.function_registry import function_registry

logger = setup_logging().getChild(__name__)


class ConversationManager:
    """Manages natural language conversations with function calling."""

    def __init__(self) -> None:
        self.memory = ChatMemory()
        self.openai_client: AsyncOpenAI | None = None
        self._initialize_openai()

    def _initialize_openai(self) -> None:
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "not_set":
            logger.warning(
                "OpenAI API key not configured - natural language features disabled"
            )
            return

        self.openai_client = AsyncOpenAI(api_key=api_key)
        logger.info("✅ Natural Language Conversation Manager initialized")

    def get_system_prompt(self) -> str:
        """Get the comprehensive system prompt for the AI."""
        return """You are Miles, an intelligent Brazilian mileage program monitoring assistant. You help users track transfer bonus promotions and manage their mileage strategies through natural conversation.

🎯 YOUR CORE PURPOSE:
You monitor 50+ Brazilian mileage sources (Livelo, Smiles, Azul, LATAM, etc.) for transfer bonus promotions and help users never miss lucrative deals.

🧠 YOUR CAPABILITIES:
- Scan all sources for current bonus promotions
- Manage the list of monitored sources (add/remove)
- Discover new mileage sources using AI
- Configure scan schedules and timing
- Analyze performance and provide optimization tips
- Manage the plugin system
- Export/import source configurations

🎨 CONVERSATION STYLE:
- Be friendly, helpful, and conversational like ChatGPT
- Use emojis and clear formatting for better readability
- Provide context and explanations, not just results
- Ask clarifying questions when needed
- Proactively suggest helpful actions
- Always explain what you're doing when calling functions

💡 EXAMPLE INTERACTIONS:
User: "Are there any good bonuses today?"
→ Call scan_for_promotions() and present results conversationally

User: "Add this site to monitor: https://example.com"
→ Call add_source() and confirm addition

User: "I want to check for bonuses every 4 hours"
→ Call set_scan_times() with appropriate hours

User: "Show me my sources"
→ Call list_sources() and present in a readable format

🔧 WHEN TO USE FUNCTIONS:
- Always call functions to perform actual bot operations
- Use multiple functions in sequence when needed
- Explain what each function does as you call it
- Provide helpful context about the results

🌟 BE PROACTIVE:
- Suggest related actions after completing requests
- Offer optimization tips based on current configuration
- Alert users to potential issues or improvements
- Help users discover features they might not know about

Remember: You're not just executing commands - you're having a conversation while helping users optimize their mileage strategy!"""

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle incoming messages with natural language processing."""
        if not update.message or not update.message.text or not update.effective_user:
            return

        if not self.openai_client:
            await update.message.reply_text(
                "❌ Natural language features are not available. OpenAI API key not configured."
            )
            return

        user_id = update.effective_user.id
        user_message = update.message.text.strip()

        try:
            # Show typing indicator
            if update.effective_chat:
                await update.effective_chat.send_action(action="typing")

            # Get conversation history
            conversation = self.memory.get(user_id)

            # Add system prompt if this is a new conversation
            if not conversation:
                conversation.append(
                    {"role": "system", "content": self.get_system_prompt()}
                )

            # Add user message
            conversation.append({"role": "user", "content": user_message})

            # Get user preferences
            model = self.memory.get_user_preference(user_id, "model") or "gpt-4o"
            temperature = float(
                self.memory.get_user_preference(user_id, "temperature") or "0.7"
            )
            max_tokens = int(
                self.memory.get_user_preference(user_id, "max_tokens") or "2000"
            )

            # Call OpenAI with function calling
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=cast(
                    Any, conversation[-20:]
                ),  # Keep last 20 messages for context
                temperature=temperature,
                max_tokens=max_tokens,
                tools=cast(
                    Any,
                    [
                        {"type": "function", "function": func}
                        for func in function_registry.get_function_definitions()
                    ],
                ),
                tool_choice="auto",
            )

            choice = response.choices[0]
            message = choice.message

            # Handle tool calls (updated for new API)
            if message.tool_calls:
                await self._handle_tool_calls(message, conversation, update, user_id)
            else:
                # Regular response without function call
                if message.content:
                    conversation.append(
                        {"role": "assistant", "content": message.content}
                    )
                    self.memory.save(user_id, conversation[-20:])
                    await update.message.reply_text(message.content)
                else:
                    await update.message.reply_text(
                        "I'm not sure how to help with that. Could you please rephrase your request?"
                    )

        except Exception as e:
            logger.exception(f"Error in conversation handling: {e}")
            await update.message.reply_text(
                f"❌ Sorry, I encountered an error: {e!s}\n\nPlease try again or rephrase your request."
            )

    async def _handle_tool_calls(
        self,
        message: Any,
        conversation: list[dict[str, Any]],
        update: Update,
        user_id: int,
    ) -> None:
        """Handle tool call execution and response."""
        if not message.tool_calls:
            return

        # Process each tool call
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            logger.info(
                f"Executing function: {function_name} with args: {function_args}"
            )

            # Add the assistant's tool call to conversation
            conversation.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    ],
                }
            )

            # Execute the function
            function_result = function_registry.execute_function(
                function_name, function_args
            )

            # Add function result to conversation
            conversation.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(function_result),
                }
            )

        # Get AI response to the function result
        try:
            if not self.openai_client:
                await self._send_fallback_response(
                    update, function_name, function_result
                )
                return

            follow_up_response = await self.openai_client.chat.completions.create(
                model=self.memory.get_user_preference(user_id, "model") or "gpt-4o",
                messages=cast(Any, conversation[-20:]),
                temperature=float(
                    self.memory.get_user_preference(user_id, "temperature") or "0.7"
                ),
                max_tokens=int(
                    self.memory.get_user_preference(user_id, "max_tokens") or "2000"
                ),
            )

            ai_response = follow_up_response.choices[0].message.content
            if ai_response and update.message:
                conversation.append({"role": "assistant", "content": ai_response})
                self.memory.save(user_id, conversation[-20:])
                await update.message.reply_text(ai_response)

        except Exception as e:
            logger.exception(f"Error in follow-up response: {e}")
            # Fallback: format the function result manually
            await self._send_fallback_response(update, function_name, function_result)

    async def _send_fallback_response(
        self, update: Update, function_name: str, function_result: dict[str, Any]
    ) -> None:
        """Send a fallback response when AI processing fails."""
        if not update.message:
            return

        if function_result.get("success"):
            if function_name == "scan_for_promotions":
                promos = function_result.get("promotions", [])
                if promos:
                    message = f"🎯 Found {len(promos)} promotions:\n\n"
                    for promo in promos[:5]:  # Show first 5
                        message += f"• {promo['bonus_percentage']}% bonus from {promo['source']}\n"
                else:
                    message = "✅ Scan complete. No new promotions found."

            elif function_name == "list_sources":
                count = function_result.get("total_sources", 0)
                message = f"📋 Currently monitoring {count} sources"

            elif function_name == "add_source":
                url = function_result.get("url", "")
                message = f"✅ Successfully added: {url}"

            else:
                message = f"✅ {function_name.replace('_', ' ').title()} completed successfully"
        else:
            error = function_result.get("error", "Unknown error")
            message = f"❌ {function_name.replace('_', ' ').title()} failed: {error}"

        await update.message.reply_text(message)

    async def handle_image_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle image messages with multimodal AI."""
        if not self.openai_client:
            if update.message:
                await update.message.reply_text(
                    "❌ Image analysis not available. OpenAI API key not configured."
                )
            return

        if not update.message or not update.message.photo or not update.effective_user:
            return

        user_id = update.effective_user.id

        try:
            # Get the largest photo
            photo = update.message.photo[-1]
            file = await photo.get_file()
            file_url = file.file_path

            # Get conversation history
            conversation = self.memory.get(user_id)

            if not conversation:
                conversation.append(
                    {"role": "system", "content": self.get_system_prompt()}
                )

            # Prepare message content with image
            content: list[dict[str, Any]] = [
                {"type": "image_url", "image_url": {"url": file_url}}
            ]

            # Add text caption if provided
            if update.message.caption:
                content.insert(0, {"type": "text", "text": update.message.caption})
            else:
                content.insert(
                    0,
                    {
                        "type": "text",
                        "text": "I sent you an image. What do you see and how can you help me with this mileage-related content?",
                    },
                )

            conversation.append({"role": "user", "content": cast(Any, content)})

            # Use GPT-4o for vision capabilities
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",  # Force vision-capable model
                messages=cast(Any, conversation[-10:]),  # Fewer messages for vision
                temperature=0.7,
                max_tokens=1500,
                tools=cast(
                    Any,
                    [
                        {"type": "function", "function": func}
                        for func in function_registry.get_function_definitions()
                    ],
                ),
                tool_choice="auto",
            )

            choice = response.choices[0]
            message = choice.message

            # Handle tool calls or regular response
            if message.tool_calls:
                await self._handle_tool_calls(message, conversation, update, user_id)
            else:
                if message.content:
                    conversation.append(
                        {"role": "assistant", "content": message.content}
                    )
                    self.memory.save(user_id, conversation[-10:])
                    await update.message.reply_text(message.content)

        except Exception as e:
            logger.exception(f"Error in image handling: {e}")
            if update.message:
                await update.message.reply_text(f"❌ Image analysis failed: {e!s}")

    def clear_conversation(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        self.memory.clear(user_id)


# Global instance
conversation_manager = ConversationManager()
