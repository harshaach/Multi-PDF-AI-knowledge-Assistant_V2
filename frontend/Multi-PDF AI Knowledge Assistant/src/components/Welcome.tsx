import { FileText, MessageSquare, Sparkles, ShieldCheck, Zap } from 'lucide-react';

interface WelcomeProps {
  onPick: (q: string) => void;
  hasPdfs: boolean;
}

const SUGGESTIONS = [
  'Summarize the key points from the uploaded documents.',
  'What are the main findings mentioned across all PDFs?',
  'Explain the methodology described in the documents.',
  'List all recommendations and action items.',
];

export function Welcome({ onPick, hasPdfs }: WelcomeProps) {
  return (
    <div className="flex-1 flex items-center justify-center px-6 py-10 overflow-y-auto scrollbar-thin">
      <div className="max-w-2xl w-full text-center animate-fade-in-up">
        {/* Logo */}
        <div className="relative inline-flex mb-6">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-teal-400 via-emerald-500 to-teal-600
                          flex items-center justify-center shadow-2xl shadow-teal-500/30 animate-float">
            <Sparkles size={36} className="text-white" />
          </div>
          <div className="absolute -inset-3 rounded-3xl bg-teal-500/20 blur-2xl -z-10 animate-pulse-glow" />
        </div>

        <h1 className="text-3xl sm:text-4xl font-bold text-white text-balance">
          Your <span className="gradient-text">PDF Knowledge</span> Assistant
        </h1>
        <p className="mt-3 text-slate-400 text-balance max-w-lg mx-auto">
          Upload PDFs and ask questions in plain language. I'll search through your documents
          and answer with verifiable source citations.
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2.5 mt-6">
          <FeaturePill icon={<FileText size={14} />} label="Multi-PDF search" />
          <FeaturePill icon={<ShieldCheck size={14} />} label="Source citations" />
          <FeaturePill icon={<MessageSquare size={14} />} label="Chat history" />
          <FeaturePill icon={<Zap size={14} />} label="Instant answers" />
        </div>

        {/* Suggestions */}
        <div className="grid sm:grid-cols-2 gap-3 mt-8 text-left">
          {SUGGESTIONS.map((q, i) => (
            <button
              key={i}
              onClick={() => onPick(q)}
              className="group glass rounded-xl p-4 hover:border-teal-500/30 hover:bg-white/5
                         transition-all duration-200 hover:scale-[1.02] text-left"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center
                                group-hover:bg-teal-500/20 transition-colors shrink-0">
                  <Sparkles size={14} className="text-teal-300" />
                </div>
                <p className="text-sm text-slate-300 group-hover:text-white transition-colors pt-1">
                  {q}
                </p>
              </div>
            </button>
          ))}
        </div>

        {!hasPdfs && (
          <p className="mt-6 text-xs text-gold-400/70">
            Tip: open the Documents panel on the right to upload your first PDF.
          </p>
        )}
      </div>
    </div>
  );
}

function FeaturePill({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs text-slate-300">
      <span className="text-teal-300">{icon}</span>
      {label}
    </div>
  );
}
