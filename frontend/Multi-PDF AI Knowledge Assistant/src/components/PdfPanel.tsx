import { useRef, useState } from 'react';
import { X, FileText, Loader2, Check, Trash2, UploadCloud } from 'lucide-react';
import type { Pdf } from '@/types';
import { uploadPdfs } from '@/lib/api';

interface PdfPanelProps {
  chatId: string | null;
  pdfs: Pdf[];
  onUploaded: (pdfs: Pdf[]) => void;
  onRemove: (id: string) => void;
  open: boolean;
  onClose: () => void;
}

export function PdfPanel({
  chatId,
  pdfs,
  onUploaded,
  onRemove,
  open,
  onClose,
}: PdfPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);

const [busy, setBusy] = useState(false);

const [error, setError] = useState<string | null>(null);



  const handleFiles = async (files: FileList | null) => {
    console.log("handleFiles called", files);
    if (!files || files.length === 0) return;
    setError(null);
    setBusy(true);
    try {
      const valid = Array.from(files).filter(
        (f) => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'),
      );
      if (valid.length === 0) {
        setError('No valid PDF files selected.');
        return;
      }

      if (!chatId) {
  setError("Please create or open a chat first.");
  return;
}

const results = await uploadPdfs(
  valid,
  chatId,
);

      const newPdfs: Pdf[] = results.map((r, i) => ({
        id: `doc-${Date.now()}-${i}-${r.filename}`,
        name: r.filename,
        size_bytes: valid[i]?.size ?? 0,
        status: 'ready',
        created_at: new Date().toISOString(),
      }));

      onUploaded(newPdfs);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed.');
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const [dragOver, setDragOver] = useState(false);

  return (
    <>
      {open && (
        <div className="fixed inset-0 bg-black/50 z-30 animate-fade-in" onClick={onClose} />
      )}
      <aside
        className={`fixed lg:static z-40 h-full w-80 shrink-0 flex flex-col glass-strong border-l border-white/5
          transition-transform duration-300 ease-out
          ${open ? 'translate-x-0' : 'translate-x-full lg:translate-x-0 lg:hidden'}`}
      >
        {/* Header */}
        <div className="px-5 pt-5 pb-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-gold-400 to-gold-600
                            flex items-center justify-center shadow-lg shadow-gold-500/20">
              <FileText size={17} className="text-white" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-[15px] leading-tight">Documents</h2>
              <p className="text-[11px] text-slate-500 leading-tight">
                {pdfs.length} PDF{pdfs.length !== 1 ? 's' : ''} loaded
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/5"
            aria-label="Close panel"
          >
            <X size={18} />
          </button>
        </div>

        {/* Drop zone */}
        <div className="px-3 pt-2">
          <div
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              handleFiles(e.dataTransfer.files);
            }}
            className={`relative cursor-pointer rounded-xl border-2 border-dashed p-5 text-center
              transition-all duration-200
              ${dragOver
                ? 'border-teal-400 bg-teal-500/10 scale-[1.02]'
                : 'border-white/10 hover:border-teal-500/40 hover:bg-white/5'}`}
          >
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf,.pdf"
              multiple
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            <div className={`mx-auto w-11 h-11 rounded-full flex items-center justify-center mb-2
              ${busy ? 'bg-teal-500/15' : 'bg-gradient-to-br from-teal-500/20 to-emerald-500/20'}`}>
              {busy ? (
                <Loader2 size={20} className="text-teal-300 animate-spin" />
              ) : (
                <UploadCloud size={20} className="text-teal-300" />
              )}
            </div>
            <p className="text-sm text-slate-300 font-medium">
              {busy ? 'Uploading...' : 'Drop PDFs here'}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">or click to browse</p>
          </div>

          {error && (
            <p className="text-xs text-red-400 mt-2 px-1 animate-fade-in">{error}</p>
          )}
        </div>

        {/* PDF list */}
        <div className="flex-1 overflow-y-auto scrollbar-thin px-3 pt-4 pb-4">
          {pdfs.length === 0 ? (
            <div className="text-center py-10 px-4">
              <FileText size={28} className="mx-auto text-slate-600 mb-2" />
              <p className="text-sm text-slate-500">No documents yet</p>
              <p className="text-xs text-slate-600 mt-1">Upload PDFs to build your knowledge base.</p>
            </div>
          ) : (
            <ul className="space-y-2">
              {pdfs.map((pdf) => (
                <li
                  key={pdf.id}
                  className="group glass rounded-xl p-3 hover:border-teal-500/30 transition-colors
                             border border-white/5 animate-scale-in"
                >
                  <div className="flex items-start gap-3">
                    <div className="shrink-0 w-10 h-10 rounded-lg bg-gradient-to-br from-red-500/20 to-gold-500/20
                                    flex items-center justify-center ring-1 ring-white/5">
                      <FileText size={18} className="text-red-300" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 font-medium truncate">{pdf.name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {pdf.size_bytes > 0 && (
                          <span className="text-[11px] text-slate-500">{formatBytes(pdf.size_bytes)}</span>
                        )}
                        <StatusBadge status={pdf.status} />
                      </div>
                    </div>
                    <button
                      onClick={() => onRemove(pdf.id)}
                      className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400
                                 transition-all p-1.5 rounded-lg hover:bg-red-500/10 shrink-0"
                      aria-label="Remove document"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </>
  );
}

function StatusBadge({ status }: { status: Pdf['status'] }) {
  const map = {
    pending: { text: 'Pending', cls: 'bg-slate-500/15 text-slate-400' },
    processing: { text: 'Processing', cls: 'bg-gold-500/15 text-gold-300' },
    ready: { text: 'Ready', cls: 'bg-teal-500/15 text-teal-300' },
    error: { text: 'Error', cls: 'bg-red-500/15 text-red-300' },
  } as const;
  const s = map[status];
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-medium flex items-center gap-1 ${s.cls}`}>
      {status === 'ready' ? <Check size={9} /> : null}
      {s.text}
    </span>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
