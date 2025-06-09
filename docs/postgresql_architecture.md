# Miles Bot Enhanced Architecture with PostgreSQL

## Database Schema Design

### Core Tables

#### 1. Promotions - Historical bonus tracking
```sql
CREATE TABLE promotions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program VARCHAR(50) NOT NULL,
    bonus_percentage INTEGER NOT NULL CHECK (bonus_percentage > 0),
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    source_url TEXT NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    title TEXT,
    description TEXT,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    hash_fingerprint VARCHAR(64) UNIQUE, -- Deduplication
    user_notified_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    
    -- Indexes for fast querying
    CONSTRAINT valid_date_range CHECK (end_date IS NULL OR end_date > start_date)
);

CREATE INDEX idx_promotions_program_date ON promotions(program, discovered_at DESC);
CREATE INDEX idx_promotions_active ON promotions(is_active, discovered_at DESC) WHERE is_active = true;
CREATE INDEX idx_promotions_bonus ON promotions(bonus_percentage DESC);
```

#### 2. Sources - Source management and quality tracking
```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    domain VARCHAR(255) NOT NULL,
    name VARCHAR(200),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_checked TIMESTAMP WITH TIME ZONE,
    last_successful_check TIMESTAMP WITH TIME ZONE,
    success_rate DECIMAL(5,2) DEFAULT 100.00,
    avg_response_time_ms INTEGER,
    total_checks INTEGER DEFAULT 0,
    successful_checks INTEGER DEFAULT 0,
    promotions_found INTEGER DEFAULT 0,
    quality_score DECIMAL(3,2) DEFAULT 5.0,
    is_active BOOLEAN DEFAULT true,
    check_frequency_minutes INTEGER DEFAULT 60,
    
    -- Plugin-specific configuration
    plugin_config JSONB,
    
    -- Performance tracking
    last_error_message TEXT,
    consecutive_failures INTEGER DEFAULT 0
);

CREATE INDEX idx_sources_domain ON sources(domain);
CREATE INDEX idx_sources_quality ON sources(quality_score DESC, is_active);
CREATE INDEX idx_sources_next_check ON sources(last_checked, check_frequency_minutes) WHERE is_active = true;
```

#### 3. Users - User profiles and preferences
```sql
CREATE TABLE users (
    telegram_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    first_name VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'pt',
    
    -- Preferences
    preferred_programs TEXT[] DEFAULT ARRAY[]::TEXT[],
    min_bonus_threshold INTEGER DEFAULT 80 CHECK (min_bonus_threshold >= 0),
    max_notifications_per_day INTEGER DEFAULT 10,
    notification_hours INTEGER[] DEFAULT ARRAY[8,12,18]::INTEGER[], -- Hours when notifications are allowed
    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    
    -- Settings
    ai_chat_enabled BOOLEAN DEFAULT true,
    notification_preferences JSONB DEFAULT '{"instant": true, "daily_summary": false, "weekly_report": true}'::jsonb,
    
    -- Activity tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_commands_used INTEGER DEFAULT 0,
    total_promotions_received INTEGER DEFAULT 0,
    
    -- AI preferences
    preferred_ai_model VARCHAR(50) DEFAULT 'gpt-4o-mini',
    ai_temperature DECIMAL(2,1) DEFAULT 0.7 CHECK (ai_temperature BETWEEN 0.0 AND 2.0),
    ai_max_tokens INTEGER DEFAULT 1000 CHECK (ai_max_tokens BETWEEN 100 AND 4000)
);

CREATE INDEX idx_users_active ON users(last_active DESC);
CREATE INDEX idx_users_preferences ON users USING GIN(preferred_programs);
```

#### 4. Notifications - Delivery tracking
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
    promotion_id UUID REFERENCES promotions(id) ON DELETE SET NULL,
    
    -- Notification details
    message_text TEXT NOT NULL,
    notification_type VARCHAR(20) DEFAULT 'promotion', -- promotion, summary, alert, system
    
    -- Delivery tracking
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered BOOLEAN DEFAULT false,
    delivery_error TEXT,
    
    -- User interaction
    viewed_at TIMESTAMP WITH TIME ZONE,
    action_taken VARCHAR(20), -- clicked, ignored, saved, shared
    
    -- Metadata
    channel VARCHAR(20) DEFAULT 'telegram', -- telegram, email, push
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10)
);

CREATE INDEX idx_notifications_user_date ON notifications(user_id, sent_at DESC);
CREATE INDEX idx_notifications_promotion ON notifications(promotion_id);
CREATE INDEX idx_notifications_delivery ON notifications(delivered, sent_at) WHERE delivered = false;
```

### Analytics Tables

#### 5. Source Performance Metrics
```sql
CREATE TABLE source_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
    
    -- Performance data
    check_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time_ms INTEGER,
    status_code INTEGER,
    content_length INTEGER,
    promotions_found INTEGER DEFAULT 0,
    
    -- Quality indicators
    content_hash VARCHAR(64), -- Track content changes
    parsing_errors INTEGER DEFAULT 0,
    
    -- Metadata
    user_agent VARCHAR(200),
    plugin_name VARCHAR(100)
);

CREATE INDEX idx_source_metrics_source_time ON source_metrics(source_id, check_timestamp DESC);
CREATE INDEX idx_source_metrics_performance ON source_metrics(response_time_ms, status_code);

-- Partition by month for better performance
-- CREATE TABLE source_metrics_y2025m01 PARTITION OF source_metrics
-- FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

#### 6. ML Predictions and Training Data
```sql
CREATE TABLE bonus_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program VARCHAR(50) NOT NULL,
    
    -- Prediction details
    predicted_bonus_range INTEGER[] NOT NULL, -- [min, max]
    prediction_confidence DECIMAL(3,2) CHECK (prediction_confidence BETWEEN 0 AND 1),
    predicted_for_date DATE NOT NULL,
    prediction_window_days INTEGER DEFAULT 7,
    
    -- Model information
    model_version VARCHAR(20),
    model_features JSONB, -- Features used for prediction
    
    -- Verification
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    actual_bonus INTEGER, -- Filled when prediction is verified
    actual_date DATE,
    prediction_accuracy DECIMAL(3,2),
    verified_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_predictions_program_date ON bonus_predictions(program, predicted_for_date);
CREATE INDEX idx_predictions_accuracy ON bonus_predictions(prediction_accuracy DESC) WHERE prediction_accuracy IS NOT NULL;
```

### Application Benefits

#### 1. Advanced Querying Capabilities
- **Trend Analysis**: Identify seasonal patterns in bonus offerings
- **Source Intelligence**: Automatically prioritize high-quality sources
- **User Segmentation**: Personalize notifications based on behavior
- **Performance Optimization**: Data-driven source checking frequencies

#### 2. Business Intelligence
- **Success Metrics**: Track bot effectiveness and user satisfaction
- **Predictive Analytics**: Machine learning on historical patterns
- **A/B Testing**: Compare notification strategies
- **ROI Analysis**: Measure value delivered to users

#### 3. Operational Excellence
- **Audit Trails**: Complete history of all operations
- **Error Tracking**: Systematic monitoring of failures
- **Capacity Planning**: Data-driven scaling decisions
- **Quality Assurance**: Automated source reliability scoring

#### 4. Enhanced Features Enabled
- **Smart Notifications**: Learn optimal timing per user
- **Trend Reports**: Weekly/monthly summaries with insights
- **Recommendation Engine**: Suggest relevant programs
- **Prediction Service**: Forecast upcoming bonus opportunities
- **Advanced Search**: Complex queries across historical data

### Implementation Strategy

#### Phase 1: Core Migration (Week 1)
1. Set up PostgreSQL with connection pooling
2. Migrate existing sources from YAML to database
3. Implement promotion storage with deduplication
4. Basic user preference storage

#### Phase 2: Analytics Foundation (Week 2)
1. Historical data collection for existing promotions
2. Source performance tracking
3. User interaction analytics
4. Basic reporting dashboard

#### Phase 3: Intelligence Layer (Week 3-4)
1. ML pipeline for bonus prediction
2. Smart notification timing
3. Automated source quality scoring
4. Advanced user personalization

This PostgreSQL integration would transform Miles from a simple notification bot into an intelligent mileage optimization platform with predictive capabilities! 🚀
