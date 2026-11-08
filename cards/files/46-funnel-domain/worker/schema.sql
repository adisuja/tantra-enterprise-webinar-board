CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  event TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  host TEXT,
  body TEXT NOT NULL,
  forwarded INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS events_email ON events(email);
CREATE INDEX IF NOT EXISTS events_event ON events(event, ts);
-- WebinarJam handoff (added 2026-11-08)
ALTER TABLE events ADD COLUMN wj_status TEXT;
ALTER TABLE events ADD COLUMN wj_join_url TEXT;
ALTER TABLE events ADD COLUMN wj_thank_you_url TEXT;
ALTER TABLE events ADD COLUMN wj_error TEXT;
ALTER TABLE events ADD COLUMN wj_attempts INTEGER NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS wj_events (id TEXT PRIMARY KEY, ts TEXT NOT NULL, trigger TEXT, email TEXT, body TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS wj_events_email ON wj_events(email);
-- CRM sync (added 2026-11-08)
ALTER TABLE events ADD COLUMN crm_status TEXT;
ALTER TABLE events ADD COLUMN crm_error TEXT;
ALTER TABLE events ADD COLUMN crm_attempts INTEGER NOT NULL DEFAULT 0;
ALTER TABLE wj_events ADD COLUMN crm_status TEXT;
ALTER TABLE wj_events ADD COLUMN crm_error TEXT;
ALTER TABLE wj_events ADD COLUMN crm_attempts INTEGER NOT NULL DEFAULT 0;
