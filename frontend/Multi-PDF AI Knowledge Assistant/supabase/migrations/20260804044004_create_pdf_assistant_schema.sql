/*
# Multi-PDF AI Knowledge Assistant — schema (single-tenant, no auth)

1. Purpose
   - Stores chat sessions and their messages for a multi-PDF AI knowledge assistant.
   - Also stores metadata about uploaded PDFs (name, size, page count, status).
   - Single-tenant: no user accounts, no user_id. Data is intentionally shared/public,
     so policies are open to anon + authenticated.

2. New Tables
   - `pdfs`
     - `id` (uuid, pk)
     - `name` (text, not null) — original filename
     - `size_bytes` (bigint, not null) — file size in bytes
     - `page_count` (int, nullable) — number of pages once processed
     - `status` (text, not null default 'pending') — pending | processing | ready | error
     - `created_at` (timestamptz, default now())
   - `chat_sessions`
     - `id` (uuid, pk)
     - `title` (text, not null default 'New chat')
     - `created_at` (timestamptz, default now())
     - `updated_at` (timestamptz, default now())
   - `chat_messages`
     - `id` (uuid, pk)
     - `session_id` (uuid, not null, fk -> chat_sessions(id) on delete cascade)
     - `role` (text, not null) — 'user' | 'assistant'
     - `content` (text, not null) — message text
     - `sources` (jsonb, nullable) — array of source citations {doc, page, snippet}
     - `created_at` (timestamptz, default now())

3. Security
   - RLS enabled on all tables.
   - All CRUD open to anon + authenticated (intentionally shared single-tenant app, no sign-in).

4. Notes
   - Indexes on session_id (chat_messages) and created_at for fast ordering.
   - updated_at auto-refreshes on message insert via trigger.
*/

CREATE TABLE IF NOT EXISTS pdfs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  size_bytes bigint NOT NULL,
  page_count int,
  status text NOT NULL DEFAULT 'pending',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE pdfs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_pdfs" ON pdfs;
CREATE POLICY "anon_select_pdfs" ON pdfs FOR SELECT
  TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "anon_insert_pdfs" ON pdfs;
CREATE POLICY "anon_insert_pdfs" ON pdfs FOR INSERT
  TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "anon_update_pdfs" ON pdfs;
CREATE POLICY "anon_update_pdfs" ON pdfs FOR UPDATE
  TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "anon_delete_pdfs" ON pdfs;
CREATE POLICY "anon_delete_pdfs" ON pdfs FOR DELETE
  TO anon, authenticated USING (true);

CREATE TABLE IF NOT EXISTS chat_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL DEFAULT 'New chat',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_chat_sessions" ON chat_sessions;
CREATE POLICY "anon_select_chat_sessions" ON chat_sessions FOR SELECT
  TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "anon_insert_chat_sessions" ON chat_sessions;
CREATE POLICY "anon_insert_chat_sessions" ON chat_sessions FOR INSERT
  TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "anon_update_chat_sessions" ON chat_sessions;
CREATE POLICY "anon_update_chat_sessions" ON chat_sessions FOR UPDATE
  TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "anon_delete_chat_sessions" ON chat_sessions;
CREATE POLICY "anon_delete_chat_sessions" ON chat_sessions FOR DELETE
  TO anon, authenticated USING (true);

CREATE TABLE IF NOT EXISTS chat_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('user', 'assistant')),
  content text NOT NULL,
  sources jsonb,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_select_chat_messages" ON chat_messages;
CREATE POLICY "anon_select_chat_messages" ON chat_messages FOR SELECT
  TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "anon_insert_chat_messages" ON chat_messages;
CREATE POLICY "anon_insert_chat_messages" ON chat_messages FOR INSERT
  TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "anon_update_chat_messages" ON chat_messages;
CREATE POLICY "anon_update_chat_messages" ON chat_messages FOR UPDATE
  TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "anon_delete_chat_messages" ON chat_messages;
CREATE POLICY "anon_delete_chat_messages" ON chat_messages FOR DELETE
  TO anon, authenticated USING (true);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);

-- Auto-update chat_sessions.updated_at when a message is inserted
CREATE OR REPLACE FUNCTION touch_session_updated_at()
RETURNS trigger AS $$
BEGIN
  UPDATE chat_sessions SET updated_at = now() WHERE id = NEW.session_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_touch_session ON chat_messages;
CREATE TRIGGER trg_touch_session
  AFTER INSERT ON chat_messages
  FOR EACH ROW EXECUTE FUNCTION touch_session_updated_at();
