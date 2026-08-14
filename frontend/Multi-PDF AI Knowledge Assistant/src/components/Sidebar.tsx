import { useState } from 'react';
import { MessageSquarePlus, Search, Trash2, MessageSquare, X } from 'lucide-react';
import type { ChatSession } from '@/types';

interface SidebarProps {
  sessions: ChatSession[];
  activeId: string | null;
  loading: boolean;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  open: boolean;
  onClose: () => void;
}

export function Sidebar({
  sessions,
  activeId,
  loading,
  onSelect,
  onNew,
  onDelete,
  open,
  onClose,
}: SidebarProps) {
  const [query, setQuery] = useState('');

  const filtered = sessions.filter((s) =>
    s.title.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden animate-fade-in"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed lg:static z-40 h-full w-72 shrink-0 flex flex-col glass-strong border-r border-white/5
          transition-transform duration-300 ease-out
          ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Brand */}
        <div className="px-5 pt-5 pb-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-600
                            flex items-center justify-center shadow-lg shadow-teal-500/30">
              <span className="text-white font-bold text-lg">K</span>
              <div className="absolute inset-0 rounded-xl ring-1 ring-white/20" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-[15px] leading-tight">Knowledge</h1>
              <p className="text-[11px] text-slate-500 leading-tight">PDF Assistant</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/5"
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        {/* New chat */}
        <div className="px-3 pt-2">
          <button
            onClick={onNew}
            className="w-full btn-primary flex items-center justify-center gap-2 py-2.5 text-sm"
          >
            <MessageSquarePlus size={17} />
            New chat
          </button>
        </div>

        {/* Search */}
        <div className="px-3 pt-3">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full bg-ink-800/60 border border-white/5 rounded-lg pl-9 pr-3 py-2 text-sm
                         text-slate-200 placeholder:text-slate-500
                         focus:outline-none focus:border-teal-500/40 focus:bg-ink-800
                         transition-colors"
            />
          </div>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-2 pt-3 pb-4">
          {loading ? (
            <div className="space-y-2 px-1">
              {[0, 1, 2, 3].map((n) => (
                <div key={n} className="h-11 rounded-lg bg-ink-800/40 animate-pulse" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-10 px-4">
              <MessageSquare size={28} className="mx-auto text-slate-600 mb-2" />
              <p className="text-sm text-slate-500">
                {query ? 'No chats match your search.' : 'No conversations yet.'}
              </p>
              {!query && (
                <p className="text-xs text-slate-600 mt-1">Start a new chat to begin.</p>
              )}
            </div>
          ) : (
            <ul className="space-y-0.5">
              {filtered.map((s) => (
                <li key={s.id}>
                  <div
                    className={`group flex items-center gap-2 rounded-lg px-2.5 py-2 cursor-pointer
                      transition-colors duration-150
                      ${activeId === s.id
                        ? 'bg-teal-500/10 text-teal-100 ring-1 ring-teal-500/20'
                        : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'}`}
                    onClick={() => onSelect(s.id)}
                  >
                    <MessageSquare
                      size={15}
                      className={`shrink-0 ${activeId === s.id ? 'text-teal-300' : 'text-slate-500'}`}
                    />
                    <span className="flex-1 text-sm truncate">{s.title}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(s.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400
                                 transition-opacity p-1 rounded hover:bg-red-500/10"
                      aria-label="Delete chat"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <div className="w-2 h-2 rounded-full bg-teal-400 animate-pulse-glow" />
            <span>Connected to knowledge base</span>
          </div>
        </div>
      </aside>
    </>
  );
}
