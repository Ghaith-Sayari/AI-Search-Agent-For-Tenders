import React, { useState } from 'react';
import { Download, FileText, FileCode, Check, RotateCw } from 'lucide-react';

interface ProposalExportProps {
  proposalId: string;
  onExport: (format: 'pdf' | 'docx' | 'markdown') => Promise<{ fileName: string }>;
  disabled?: boolean;
}

export const ProposalExport: React.FC<ProposalExportProps> = ({
  proposalId,
  onExport,
  disabled = false,
}) => {
  const [selectedFormat, setSelectedFormat] = useState<'pdf' | 'docx' | 'markdown'>('pdf');
  const [isExporting, setIsExporting] = useState(false);
  const [exportedFile, setExportedFile] = useState<string | null>(null);

  const handleTriggerExport = async () => {
    if (disabled || isExporting) return;
    setIsExporting(true);
    setExportedFile(null);
    try {
      const res = await onExport(selectedFormat);
      setExportedFile(res.fileName);
    } catch (err) {
      console.error('Export error:', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs space-y-3">
      <div className="flex items-center gap-1.5 border-b border-slate-100 pb-2">
        <Download className="w-4 h-4 text-[#86BC25]" />
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
          Export Proposal Draft
        </h3>
      </div>

      <div className="space-y-2 text-xs font-sans">
        <label className="font-bold text-slate-700">Select Export Format</label>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => setSelectedFormat('pdf')}
            className={`p-2 rounded border font-mono text-[11px] font-bold transition-all flex flex-col items-center gap-1 ${
              selectedFormat === 'pdf'
                ? 'bg-[#111827] text-[#86BC25] border-[#111827]'
                : 'bg-[#F5F6F7] text-slate-700 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>PDF</span>
          </button>

          <button
            type="button"
            onClick={() => setSelectedFormat('docx')}
            className={`p-2 rounded border font-mono text-[11px] font-bold transition-all flex flex-col items-center gap-1 ${
              selectedFormat === 'docx'
                ? 'bg-[#111827] text-[#86BC25] border-[#111827]'
                : 'bg-[#F5F6F7] text-slate-700 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>DOCX</span>
          </button>

          <button
            type="button"
            onClick={() => setSelectedFormat('markdown')}
            className={`p-2 rounded border font-mono text-[11px] font-bold transition-all flex flex-col items-center gap-1 ${
              selectedFormat === 'markdown'
                ? 'bg-[#111827] text-[#86BC25] border-[#111827]'
                : 'bg-[#F5F6F7] text-slate-700 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <FileCode className="w-4 h-4" />
            <span>MD</span>
          </button>
        </div>

        <button
          onClick={handleTriggerExport}
          disabled={disabled || isExporting}
          className={`w-full py-2.5 px-3 text-xs font-bold rounded transition-all flex items-center justify-center gap-2 shadow-xs ${
            disabled
              ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
              : 'bg-[#007629] hover:bg-[#005f20] text-white active:scale-98'
          }`}
        >
          {isExporting ? (
            <>
              <RotateCw className="w-3.5 h-3.5 animate-spin text-[#86BC25]" />
              <span>Generating Export File...</span>
            </>
          ) : (
            <>
              <Download className="w-3.5 h-3.5 text-[#86BC25]" />
              <span>Export as {selectedFormat.toUpperCase()}</span>
            </>
          )}
        </button>

        {exportedFile && (
          <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded text-[11px] text-emerald-900 flex items-center gap-2 font-mono">
            <Check className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="truncate">Downloaded: {exportedFile}</span>
          </div>
        )}
      </div>
    </div>
  );
};
