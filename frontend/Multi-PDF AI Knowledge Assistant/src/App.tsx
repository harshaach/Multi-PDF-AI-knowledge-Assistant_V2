import { useState, useEffect, useRef, useCallback } from 'react';
import { Menu, PanelRightOpen, PanelRightClose, Sparkles, AlertCircle } from 'lucide-react';
import { Sidebar } from '@/components/Sidebar';
import { PdfPanel } from '@/components/PdfPanel';
import { MessageBubble, TypingIndicator } from '@/components/MessageBubble';
import { ChatInput } from '@/components/ChatInput';
import { Welcome } from '@/components/Welcome';
import { queryKnowledgeBase, fetchDocuments } from '@/lib/api';
import type { ChatSession, ChatMessage, Pdf } from '@/types';

/* ---------- localStorage chat persistence ---------- */

const SESSIONS_KEY = 'pdf-assistant:sessions';
const MESSAGES_KEY = 'pdf-assistant:messages';

function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as ChatSession[];
  } catch {
    return [];
  }
}

function saveSessions(sessions: ChatSession[]): void {
  try {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  } catch {
    /* ignore quota errors */
  }
}

function loadMessages(): Record<string, ChatMessage[]> {
  try {
    const raw = localStorage.getItem(MESSAGES_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as Record<string, ChatMessage[]>;
  } catch {
    return {};
  }
}

function saveMessages(map: Record<string, ChatMessage[]>): void {
  try {
    localStorage.setItem(MESSAGES_KEY, JSON.stringify(map));
  } catch {
    /* ignore quota errors */
  }
}

function App() {
  // Sessions
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  // Messages (stored in a map keyed by session id)
  const [messagesMap, setMessagesMap] = useState<Record<string, ChatMessage[]>>({});
  const [messagesLoading, setMessagesLoading] = useState(false);

  // Input
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // PDFs
  const [pdfs, setPdfs] = useState<Pdf[]>([]);

  // UI panels
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pdfPanelOpen, setPdfPanelOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  /* ---------- Load sessions + messages from localStorage ---------- */
useEffect(() => {
  const loadedSessions = loadSessions();
  const loadedMessages = loadMessages();

  setSessions(loadedSessions);
  setMessagesMap(loadedMessages);

  // Don't automatically open an old chat
  setActiveSessionId(null);

  setSessionsLoading(false);
}, []);

  /* ---------- Load PDFs from FastAPI ---------- */
  useEffect(() => {
    (async () => {
      try {
        const docs = activeSessionId
        ? await fetchDocuments(activeSessionId)
        : [];
        const loadedPdfs: Pdf[] = docs.map((name, i) => ({
          id: `doc-${i}-${name}`,
          name,
          size_bytes: 0,
          status: 'ready',
          created_at: new Date().toISOString(),
        }));
        setPdfs(loadedPdfs);
      } catch {
        // Backend not reachable — keep empty list
      }
    })();
  }, [activeSessionId]);

  /* ---------- Auto-scroll ---------- */
  const activeMessages = activeSessionId ? messagesMap[activeSessionId] ?? [] : [];
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeMessages.length, sending]);

  /* ---------- New chat ---------- */
  const handleNewChat = useCallback(() => {
    const session: ChatSession = {
      id: crypto.randomUUID(),
      title: 'New chat',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    setSessions((prev) => {
      const next = [session, ...prev];
      saveSessions(next);
      return next;
    });
    setMessagesMap((prev) => {
      const next = { ...prev, [session.id]: [] };
      saveMessages(next);
      return next;
    });
    setActiveSessionId(session.id);
    setInput('');
    setError(null);
    setSidebarOpen(false);
  }, []);

  /* ---------- Select session ---------- */
  const handleSelectSession = useCallback((id: string) => {
    setActiveSessionId(id);
    setError(null);
    setSidebarOpen(false);
  }, []);

  /* ---------- Delete session ---------- */
  const handleDeleteSession = useCallback((id: string) => {
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id);
      saveSessions(next);
      return next;
    });
    setMessagesMap((prev) => {
      const next = { ...prev };
      delete next[id];
      saveMessages(next);
      return next;
    });
    setActiveSessionId((curr) => (curr === id ? null : curr));
  }, []);

  /* ---------- Send message ---------- */
  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    setError(null);
    let sessionId = activeSessionId;

    // Create a session if none active
    if (!sessionId) {
      const session: ChatSession = {
        id: crypto.randomUUID(),
        title: text.slice(0, 50),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      sessionId = session.id;
      setSessions((prev) => {
        const next = [session, ...prev];
        saveSessions(next);
        return next;
      });
      setMessagesMap((prev) => {
        const next = { ...prev, [session.id]: [] };
        saveMessages(next);
        return next;
      });
      setActiveSessionId(sessionId);
    }

    const sid = sessionId;
    const now = new Date().toISOString();

    // Optimistic user message
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: sid,
      role: 'user',
      content: text,
      sources: null,
      created_at: now,
    };

    setMessagesMap((prev) => {
      const list = prev[sid] ?? [];
      const next = { ...prev, [sid]: [...list, userMsg] };
      saveMessages(next);
      return next;
    });

    // Update session title + updated_at if first message
    const isFirstMessage = (messagesMap[sid]?.length ?? 0) === 0;
    setSessions((prev) => {
      const next = prev.map((s) =>
        s.id === sid
          ? {
              ...s,
              title: isFirstMessage ? text.slice(0, 50) : s.title,
              updated_at: now,
            }
          : s,
      );
      saveSessions(next);
      return next;
    });

    setInput('');
    setSending(true);

    // Query FastAPI backend
    try {
      const result = await queryKnowledgeBase(text, sid);

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: sid,
        role: 'assistant',
        content: result.answer,
        sources: result.sources ?? [],
        created_at: new Date().toISOString(),
      };

      setMessagesMap((prev) => {
        const list = prev[sid] ?? [];
        const next = { ...prev, [sid]: [...list, assistantMsg] };
        saveMessages(next);
        return next;
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Something went wrong.';
      setError(msg);
      const errMsg: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: sid,
        role: 'assistant',
        content: `I couldn't retrieve an answer. ${msg}`,
        sources: [],
        created_at: new Date().toISOString(),
      };
      setMessagesMap((prev) => {
        const list = prev[sid] ?? [];
        const next = { ...prev, [sid]: [...list, errMsg] };
        saveMessages(next);
        return next;
      });
    } finally {
      setSending(false);
    }
  }, [input, sending, activeSessionId, messagesMap]);

  /* ---------- PDF handlers ---------- */
  const handlePdfUploaded = useCallback((newPdfs: Pdf[]) => {
    setPdfs((prev) => {
      // Merge, dedup by name
      const existing = new Set(prev.map((p) => p.name));
      const additions = newPdfs.filter((p) => !existing.has(p.name));
      return [...additions, ...prev];
    });
  }, []);

  const handlePdfRemove = useCallback((id: string) => {
    setPdfs((prev) => prev.filter((p) => p.id !== id));
  }, []);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const showWelcome = !activeSessionId && activeMessages.length === 0 && !sending;

  return (
    <div className="mesh-bg h-screen flex overflow-hidden text-slate-200">
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        activeId={activeSessionId}
        loading={sessionsLoading}
        onSelect={handleSelectSession}
        onNew={handleNewChat}
        onDelete={handleDeleteSession}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0 relative">
        {/* Top bar */}
        <header className="shrink-0 h-14 flex items-center justify-between px-3 sm:px-5
                           glass border-b border-white/5 z-20">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-slate-400 hover:text-white p-2 rounded-lg hover:bg-white/5"
              aria-label="Open chats"
            >
              <Menu size={19} />
            </button>
            <div className="flex items-center gap-2 min-w-0">
              <Sparkles size={16} className="text-teal-400 shrink-0" />
              <h2 className="text-sm font-medium text-slate-300 truncate">
                {activeSession?.title ?? 'New conversation'}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setPdfPanelOpen((o) => !o)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors
                ${pdfPanelOpen
                  ? 'bg-teal-500/15 text-teal-300 ring-1 ring-teal-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'}`}
            >
              {pdfPanelOpen ? <PanelRightClose size={16} /> : <PanelRightOpen size={16} />}
              <span className="hidden sm:inline">Documents</span>
              {pdfs.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-teal-500/20 text-teal-300 font-medium">
                  {pdfs.length}
                </span>
              )}
            </button>
          </div>
        </header>

        {/* Error banner */}
        {error && (
          <div className="mx-4 sm:mx-6 mt-3 flex items-center gap-2 px-4 py-2.5 rounded-xl
                          bg-red-500/10 border border-red-500/20 text-red-300 text-sm animate-fade-in-up">
            <AlertCircle size={16} className="shrink-0" />
            <span className="flex-1">{error}</span>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200 text-xs">
              Dismiss
            </button>
          </div>
        )}

        {/* Chat scroll area */}
        {showWelcome ? (
          <Welcome
            hasPdfs={pdfs.length > 0}
            onPick={(q) => {
              setInput(q);
            }}
          />
        ) : (
          <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-6">
              {messagesLoading ? (
                <div className="space-y-6">
                  {[0, 1, 2].map((n) => (
                    <div key={n} className="flex gap-4 animate-pulse">
                      <div className="w-9 h-9 rounded-xl bg-ink-700/60" />
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-ink-700/60 rounded w-3/4" />
                        <div className="h-4 bg-ink-700/40 rounded w-1/2" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                activeMessages.map((m) => <MessageBubble key={m.id} message={m} />)
              )}
              {sending && <TypingIndicator />}
              <div ref={bottomRef} />
            </div>
          </div>
        )}

        {/* Input */}
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          onStop={() => setSending(false)}
          disabled={sending}
          loading={sending}
        />
      </main>

      {/* PDF panel */}
     <PdfPanel
  chatId={activeSessionId}
  pdfs={pdfs}
  onUploaded={handlePdfUploaded}
  onRemove={handlePdfRemove}
  open={pdfPanelOpen}
  onClose={() => setPdfPanelOpen(false)}
/>
    </div>
  );
}

export default App;
