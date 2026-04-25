-- Sprint 6.5: Bot / anomali tespiti icin audit tablosu

CREATE TABLE IF NOT EXISTS anomaly_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    device_key VARCHAR(512) NOT NULL,
    ip_address VARCHAR(64) NOT NULL,
    user_agent VARCHAR(255),
    request_path VARCHAR(255),
    action_taken VARCHAR(50) NOT NULL,
    reason VARCHAR(500) NOT NULL,
    observed_identifier VARCHAR(64),
    distinct_value_count INTEGER,
    window_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly_events_event_type
    ON anomaly_events(event_type);

CREATE INDEX IF NOT EXISTS idx_anomaly_events_created_at
    ON anomaly_events(created_at DESC);
