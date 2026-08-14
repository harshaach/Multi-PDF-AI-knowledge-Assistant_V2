import { useRef, useEffect, type KeyboardEvent } from 'react';
import { ArrowUp, Square } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onStop?: () => void;
  disabled: boolean;
  loading: boolean;
  placeholder?: string;
}

export function ChatInput({
  value,
  onChange,
  onSend,
  onStop,
  disabled,
  loading,
  placeholder,
}: ChatInputProps) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled) onSend();
    }
  };

  return (
    <div className="px-3 sm:px-6 pb-4 pt-2">
      <div className="max-w-3xl mx-auto">
        <div
          className={`relative flex items-end gap-2 rounded-2xl glass-strong p-2 pl-4
            transition-all duration-200
            ${disabled ? 'opacity-60' : 'focus-within:border-teal-500/40 focus-within:shadow-lg focus-within:shadow-teal-500/10'}`}
        >
          <textarea
            ref={ref}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
            disabled={disabled}
            placeholder={placeholder ?? 'Ask anything about your documents...'}
            className="flex-1 bg-transparent resize-none text-[15px] text-slate-100 placeholder:text-slate-500
                       focus:outline-none py-2 max-h-[200px] scrollbar-thin"
          />
          {loading ? (
            <button
              onClick={onStop}
              className="shrink-0 w-9 h-9 rounded-xl bg-red-500/20 text-red-300 hover:bg-red-500/30
                         flex items-center justify-center transition-colors"
              aria-label="Stop generating"
            >
              <Square size={15} className="fill-current" />
            </button>
          ) : (
            <button
              onClick={onSend}
              disabled={disabled}
              className="shrink-0 w-9 h-9 rounded-xl btn-primary flex items-center justify-center !p-0"
              aria-label="Send message"
            >
              <ArrowUp size={18} />
            </button>
          )}
        </div>
        <p className="text-center text-[11px] text-slate-600 mt-2">
          Answers are sourced from your uploaded PDFs. Press Enter to send, Shift+Enter for a new line.
        </p>
      </div>
    </div>
  );
}
