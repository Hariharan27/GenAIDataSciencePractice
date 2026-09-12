CREATE TABLE IF NOT EXISTS project_health_snapshots (
    id BIGSERIAL PRIMARY KEY,
    project_id TEXT NOT NULL,
    health_score DOUBLE PRECISION NOT NULL,
    health_status TEXT NOT NULL,
    risk_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    calculated_at TIMESTAMPTZ NOT NULL,
    evidence_fingerprint TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_project_health_snapshots_project_time
    ON project_health_snapshots (project_id, calculated_at DESC);