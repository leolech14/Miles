# 🤖 Miles - Natural Language Edition

**Revolutionary conversational AI assistant for Brazilian mileage programs**

Miles has been transformed from a command-based bot into an intelligent conversational assistant that feels like ChatGPT but with all the power of automated mileage monitoring!

## 🎯 What's New

### **Before (Commands)**
```
User: /ask
Bot:  🔍 Scanning for promotions...

User: /sources
Bot:  1. https://site1.com
      2. https://site2.com
```

### **After (Natural Language)**
```
User: Are there any good bonuses today?
AI:   Let me scan all sources for you! 🔍
      *scanning...*
      Found 3 great bonuses:
      🎯 Livelo 120% to Smiles (ends tonight!)
      🎯 Itaú 100% to Azul (valid until Friday)
      🎯 C6 Bank 90% to LATAM (new promotion!)

      Would you like me to set up alerts for bonuses above 100%?

User: Show me my monitored websites
AI:   You're currently monitoring 15 Brazilian mileage sources
      including Melhores Destinos, Passageiro de Primeira, and
      others. Here's the full list with performance stats...
```

## 🚀 Quick Start

### **Prerequisites**
- Python 3.12+
- OpenAI API key (required for natural language)
- Telegram Bot Token
- Redis (optional, falls back to file storage)

### **1. Environment Setup**
```bash
# Clone and install
git clone https://github.com/leolech14/Miles.git
cd Miles
pip install -e .[dev]

# Configure environment
cp .env.natural .env
# Edit .env with your API keys
```

### **2. Run Migration Check**
```bash
python scripts/migrate_to_natural_language.py
```

### **3. Start Natural Language Bot**
```bash
python natural_language_bot.py
```

### **4. Docker Deployment (Recommended)**
```bash
docker-compose -f docker-compose.natural.yml up -d
```

## 💬 Example Conversations

### **🎯 Finding Bonuses**
- *"What's the best transfer bonus available right now?"*
- *"Check for any Livelo promotions"*
- *"Are there bonuses above 100% today?"*
- *"Find me the highest Smiles transfer bonus"*

### **📊 Managing Sources**
- *"Add this site to monitor: https://newsite.com"*
- *"Remove the third source from my list"*
- *"Show me all websites you're monitoring"*
- *"Which sources find the most bonuses?"*

### **⏰ Scheduling & Optimization**
- *"Check for bonuses every 4 hours"*
- *"Set up scanning at 8 AM and 8 PM"*
- *"When do you usually find the best promotions?"*
- *"Optimize my scan timing for better results"*

### **🔧 Configuration & Analysis**
- *"How is the bot performing?"*
- *"Show me performance statistics"*
- *"What settings should I use for Livelo?"*
- *"Analyze my source quality"*

### **🧠 AI-Powered Features**
- *"Find new mileage websites for me"*
- *"Discover sources I'm missing"*
- *"What's the best strategy for Smiles transfers?"*
- *"Help me optimize my mileage setup"*

### **🖼️ Multimodal Support**
Send images of promotions, websites, or mileage program pages:
- Screenshot of a bonus promotion → AI analyzes and adds to monitoring
- Photo of credit card offer → AI extracts transfer rates
- Image of mileage program rules → AI explains optimal strategy

## 🏗️ Architecture Overview

```mermaid
flowchart TB
    %% User Interface
    USER[User Message<br/>"Find good bonuses"] --> TG[Telegram Bot]

    %% AI Processing Layer
    TG --> OPENAI[OpenAI GPT-4o<br/>Function Calling]
    OPENAI <--> CONTEXT[Context Manager<br/>Conversation + Bot State]
    OPENAI <--> FUNCTIONS[Function Registry<br/>13 Bot Operations]

    %% Action Execution
    FUNCTIONS --> SCAN[Scan Promotions]
    FUNCTIONS --> SOURCES[Manage Sources]
    FUNCTIONS --> CONFIG[Configuration]
    FUNCTIONS --> SCHEDULE[Scheduling]

    %% Existing Infrastructure (Reused)
    SCAN --> CORE[Core Engine<br/>Plugin System]
    SOURCES --> CORE
    CONFIG --> CORE
    SCHEDULE --> CORE

    CORE --> STORAGE[Redis + PostgreSQL<br/>+ File Fallback]
    CORE --> MONITORING[Metrics + Health]

    %% Response Flow
    OPENAI --> TG
    TG --> USER
```

## 🎯 Key Features

### **🧠 Intelligent Conversation**
- **Context awareness**: Remembers conversation history
- **Intent understanding**: Knows what you want without exact commands
- **Proactive suggestions**: Offers helpful recommendations
- **Explanation mode**: Explains what it's doing as it works

### **⚡ All Original Functionality**
- **Promotion scanning**: 50+ Brazilian mileage sources
- **Source management**: Add, remove, and organize monitoring
- **AI discovery**: Automatically finds new mileage websites
- **Scheduling control**: Set optimal scan timing
- **Plugin system**: Modular, extensible architecture

### **🎨 Enhanced User Experience**
- **Natural language**: Chat like with ChatGPT
- **Multimodal support**: Send images for analysis
- **Rich responses**: Formatted, contextual replies
- **Error recovery**: Graceful handling of issues

### **🔧 Advanced Configuration**
- **Per-user preferences**: Custom AI settings
- **Performance optimization**: AI-powered tuning
- **Real-time monitoring**: Health checks and metrics
- **Comprehensive logging**: Full audit trail

## 📋 Function Registry

The bot understands these natural language intents through OpenAI function calling:

| Function | Natural Language Examples |
|----------|--------------------------|
| `scan_for_promotions` | "Check for bonuses", "Any good deals today?" |
| `list_sources` | "Show my sources", "What sites are monitored?" |
| `add_source` | "Add this URL", "Monitor this website" |
| `remove_source` | "Remove that site", "Stop monitoring #3" |
| `discover_new_sources` | "Find new sources", "Discover more sites" |
| `get_schedule` | "Show schedule", "When do scans run?" |
| `set_scan_times` | "Scan every 4 hours", "Check at 8 AM and 8 PM" |
| `get_bot_status` | "How's it going?", "Show bot health" |
| `manage_plugins` | "List plugins", "Test the Smiles plugin" |
| `analyze_performance` | "How am I doing?", "Optimize my setup" |

## 🔧 Configuration

### **Environment Variables**

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
OPENAI_API_KEY=sk-proj-your_key

# AI Configuration (optimized for conversation)
OPENAI_MODEL=gpt-4o                    # Best for function calling
OPENAI_TEMPERATURE=0.7                 # Balanced creativity
OPENAI_MAX_TOKENS=2000                 # Longer responses
CONVERSATION_TIMEOUT=1800              # 30 minutes

# Enhanced Features
ENABLE_PROACTIVE_SUGGESTIONS=true
ENABLE_PERFORMANCE_INSIGHTS=true
ENABLE_MULTIMODAL=true
ENABLE_FUNCTION_EXPLANATIONS=true

# Rate Limiting (generous for conversation)
RATE_LIMIT_MESSAGES=30                 # Messages per minute
RATE_LIMIT_FUNCTIONS=20                # Function calls per minute
RATE_LIMIT_OPENAI=60                   # OpenAI requests per minute

# Optional
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/miles
MIN_BONUS=80
METRICS_ENABLED=true
```

### **Docker Compose**

```yaml
version: "3.9"
services:
  natural-language-bot:
    build:
      dockerfile: Dockerfile.natural
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres
    ports:
      - "8080:8080"

  redis:
    image: redis:7-alpine

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=miles
```

## 🚀 Deployment Options

### **Local Development**
```bash
pip install -e .[dev]
python natural_language_bot.py
```

### **Docker (Recommended)**
```bash
docker-compose -f docker-compose.natural.yml up -d
```

### **Fly.io Production**
```bash
# Set secrets
fly secrets set OPENAI_API_KEY=sk-proj-...
fly secrets set TELEGRAM_BOT_TOKEN=...

# Deploy
fly deploy --dockerfile Dockerfile.natural
```

### **With Monitoring Stack**
```bash
# Includes Prometheus + Grafana
docker-compose -f docker-compose.natural.yml up -d

# Access dashboards
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus
```

## 📊 Monitoring & Health

### **Health Endpoints**
- `http://localhost:8080/health` - Basic health check
- `http://localhost:8080/metrics` - Prometheus metrics

### **Key Metrics**
- Conversation success rate
- Function call latency
- OpenAI API usage
- Source scan performance
- User engagement stats

### **Performance Optimization**
The AI automatically monitors and suggests optimizations for:
- Scan timing based on historical data
- Source quality scoring
- Rate limit adjustment
- Resource usage optimization

## 🔄 Migration from Command Version

### **Automatic Migration**
```bash
python scripts/migrate_to_natural_language.py
```

This script:
- ✅ Validates your environment
- ✅ Tests OpenAI connectivity
- ✅ Verifies function registry
- ✅ Provides deployment guidance
- ✅ Shows example conversations

### **Data Compatibility**
- ✅ All existing sources preserved
- ✅ User preferences maintained
- ✅ Historical data intact
- ✅ Plugin configurations unchanged

## 🛡️ Security & Privacy

### **Data Protection**
- Conversations auto-expire after 30 minutes
- No sensitive data stored permanently
- API keys encrypted in environment
- Rate limiting prevents abuse

### **Function Calling Safety**
- All functions validate input parameters
- Read-only operations by default
- Explicit confirmation for destructive actions
- Comprehensive audit logging

## 🤝 Contributing

The natural language version maintains all original architecture while adding:

```
miles/natural_language/
├── conversation_manager.py    # Handles all user interactions
├── function_registry.py       # Defines bot operations as OpenAI functions
└── __init__.py               # Module exports

natural_language_bot.py       # New entry point
natural_language_config.py    # Optimized configuration
Dockerfile.natural            # Optimized container
docker-compose.natural.yml    # Full stack deployment
```

### **Adding New Functions**
1. Add function definition to `function_registry.py`
2. Implement execution logic
3. Update AI system prompt with new capabilities
4. Test with natural language examples

## 📈 Performance Comparison

| Metric | Command Version | Natural Language |
|--------|----------------|------------------|
| User Learning Curve | High (must learn commands) | Low (natural conversation) |
| Interaction Speed | Fast (direct commands) | Moderate (AI processing) |
| Feature Discovery | Poor (hidden commands) | Excellent (AI suggests) |
| Error Recovery | Manual (user must retry) | Automatic (AI clarifies) |
| Contextual Help | Limited (/help) | Comprehensive (AI explains) |
| Multimodal Support | None | Full (images + text) |

## 🎯 Roadmap

### **Short Term**
- [ ] Voice message support
- [ ] Advanced conversation flows
- [ ] Custom AI personalities
- [ ] Integration with more mileage programs

### **Medium Term**
- [ ] Predictive bonus forecasting
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Mobile app companion

### **Long Term**
- [ ] AI agent ecosystem
- [ ] Cross-platform integration
- [ ] Community source sharing
- [ ] Machine learning optimization

## 🆘 Troubleshooting

### **Common Issues**

**"Natural language features not available"**
```bash
# Check OpenAI API key
echo $OPENAI_API_KEY
# Validate key format (should start with sk-proj-)
```

**"Function execution failed"**
```bash
# Check function registry
python -c "from miles.natural_language.function_registry import function_registry; print(len(function_registry.get_function_definitions()))"
```

**"Conversation timeout"**
```bash
# Adjust timeout in environment
export CONVERSATION_TIMEOUT=3600  # 1 hour
```

### **Performance Tuning**
- Use `gpt-4o-mini` for faster responses
- Reduce `max_tokens` for shorter replies
- Increase rate limits for heavy usage
- Enable Redis for better caching

## 📞 Support

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: General questions and community
- **Email**: Critical security issues

---

**Transform your mileage monitoring experience with the power of conversational AI!** 🚀

*"Miles - where traditional automation meets cutting-edge AI"*
