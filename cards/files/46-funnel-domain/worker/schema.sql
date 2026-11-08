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
