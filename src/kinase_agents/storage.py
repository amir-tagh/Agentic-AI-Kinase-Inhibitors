"""SQLite schema preserving raw source data and source-specific IDs."""
import json
import sqlite3
from datetime import datetime, timezone

SCHEMA = '''
CREATE TABLE IF NOT EXISTS evidence (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  record_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  compound_query TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  UNIQUE(source, record_type, source_id, compound_query)
);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source, record_type);
'''

class EvidenceStore:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        self.connection.executescript(SCHEMA)
    def add(self, source, kind, identifier, query, payload):
        self.connection.execute('''INSERT INTO evidence(source,record_type,source_id,compound_query,retrieved_at,payload_json)
          VALUES(?,?,?,?,?,?) ON CONFLICT(source,record_type,source_id,compound_query)
          DO UPDATE SET retrieved_at=excluded.retrieved_at,payload_json=excluded.payload_json''',
          (source, kind, str(identifier), query, datetime.now(timezone.utc).isoformat(), json.dumps(payload)))
    def commit(self): self.connection.commit()
    def close(self): self.connection.close()
