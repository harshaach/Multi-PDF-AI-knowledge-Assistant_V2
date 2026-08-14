import { useState } from 'react';
import { renderMarkdown } from '@/lib/markdown';
import type { ChatMessage } from '@/types';
import { User, Sparkles, Copy, Check, FileText, ChevronDown, ChevronUp } from 'lucide-react';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const sources = message.sources ?? [];

  return (
    <div className={`flex gap-3 sm:gap-4 animate-fade-in-up ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center shadow-md
          ${isUser
            ? 'bg-gradient-to-br from-ink-600 to-ink-800 ring-1 ring-white/10'
            : 'bg-gradient-to-br from-teal-400 to-emerald-600 shadow-teal-500/20'}`}
      >
        {isUser ? (
          <User size={17} className="text-slate-300" />
        ) : (
          <Sparkles size={17} className="text-white" />
        )}
      </div>

      {/* Body */}
      <div className={`flex flex-col gap-1.5 min-w-0 max-w-[calc(100%-3.5rem)] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-[14.5px] leading-relaxed
            ${isUser
              ? 'bg-gradient-to-br from-ink-700 to-ink-850 text-slate-100 rounded-tr-md ring-1 ring-white/5'
              : 'glass text-slate-200 rounded-tl-md'}`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            <div className="md-content break-words">{renderMarkdown(message.content)}</div>
          )}
        </div>

        {/* Actions + sources (assistant only) */}
        {!isUser && (
          <div className="flex items-center gap-1 pl-1">
            <button
              onClick={copy}
              className="text-slate-500 hover:text-teal-300 transition-colors p-1.5 rounded-lg hover:bg-white/5"
              aria-label="Copy answer"
            >
              {copied ? <Check size={14} className="text-teal-400" /> : <Copy size={14} />}
            </button>

            {sources.length > 0 && (
              <button
                onClick={() => setSourcesOpen((o) => !o)}
                className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300
                           transition-colors px-2 py-1.5 rounded-lg hover:bg-white/5"
              >
                <FileText size={13} />
                {sources.length} source{sources.length > 1 ? 's' : ''}
                {sourcesOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>
            )}
          </div>
        )}

        {/* Source citations */}
        {!isUser && sourcesOpen && sources.length > 0 && (
          <div className="w-full space-y-2 animate-fade-in">
            {sources.map((src, idx) => (
              <div
                key={idx}
                className="glass rounded-xl p-3 border-l-2 border-teal-500/40 hover:border-teal-400
                           transition-colors group"
              >
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-teal-500/15 flex items-center justify-center">
                    <FileText size={12} className="text-teal-300" />
                  </div>
                  <span className="text-xs font-medium text-slate-300 truncate">{src}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 sm:gap-4 animate-fade-in">
      <div className="shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-600
                      flex items-center justify-center shadow-md shadow-teal-500/20">
        <Sparkles size={17} className="text-white" />
      </div>
      <div className="glass rounded-2xl rounded-tl-md px-4 py-4 flex items-center gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-2 h-2 rounded-full bg-teal-400 animate-bounce-dot"
            style={{ animationDelay: `${i * 0.16}s` }}
          />
        ))}
      </div>
    </div>
  );
}
