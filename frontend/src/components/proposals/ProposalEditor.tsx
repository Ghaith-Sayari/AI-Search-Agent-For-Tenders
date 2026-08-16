import React, { useState, useEffect } from 'react';
import { ProposalSection } from '../../types/proposal';
import { RotateCw, Sparkles, Undo, Redo, Save, FileText, Info } from 'lucide-react';

interface ProposalEditorProps {
  section: ProposalSection;
  onContentChange: (newContent: string) => void;
  onSaveSection: () => void;
  onSectionAiAction: (action: 'Regenerate' | 'Improve' | 'Shorten' | 'Expand') => Promise<void>;
  isRegenerating: string | null;
  autosaveStatus: 'Saved' | 'Saving...' | 'Unsaved changes';
}

export const ProposalEditor: React.FC<ProposalEditorProps> = ({
  section,
  onContentChange,
  onSaveSection,
  onSectionAiAction,
  isRegenerating,
  autosaveStatus,
}) => {
  const [contentHistory, setContentHistory] = useState<string[]>([section.content]);
  const [historyIndex, setHistoryIndex] = useState<number>(0);

  useEffect(() => {
    setContentHistory([section.content]);
    setHistoryIndex(0);
  }, [section.id]);

  const handleTextChange = (text: string) => {
    onContentChange(text);
    const newHistory = contentHistory.slice(0, historyIndex + 1);
    newHistory.push(text);
    setContentHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const prev = contentHistory[historyIndex - 1];
      setHistoryIndex(historyIndex - 1);
      onContentChange(prev);
    }
  };

  const handleRedo = () => {
    if (historyIndex < contentHistory.length - 1) {
      const next = contentHistory[historyIndex + 1];
      setHistoryIndex(historyIndex + 1);
      onContentChange(next);
    }
  };

  const wordsCount = section.content.trim() ? section.content.trim().split(/\s+/).length : 0;
  const charsCount = section.content.length;

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4 flex flex-col justify-between min-h-[580px]">
      <div className="space-y-3">
        {/* Section Header & Toolbar */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-bold">
                Active Section
              </span>
              <span className="text-xs text-slate-400 font-mono">
                Last updated: {section.lastUpdated}
              </span>
            </div>
            <h2 className="text-base font-extrabold text-slate-900 mt-0.5">
              {section.title}
            </h2>
          </div>

          {/* Section AI Actions Toolbar */}
          <div className="flex flex-wrap items-center gap-1.5 bg-slate-50 p-1.5 rounded border border-slate-200 text-xs">
            <span className="text-[10px] font-mono font-bold text-slate-400 px-1 uppercase hidden sm:inline">
              Section AI:
            </span>

            <button
              onClick={() => onSectionAiAction('Regenerate')}
              disabled={isRegenerating !== null}
              className="px-2.5 py-1 text-[11px] font-bold text-slate-800 bg-white hover:bg-slate-100 border border-slate-200 rounded transition-colors flex items-center gap-1"
              title="Regenerate this section only"
            >
              {isRegenerating === 'Regenerate' ? (
                <RotateCw className="w-3 h-3 animate-spin text-[#86BC25]" />
              ) : (
                <RotateCw className="w-3 h-3 text-[#86BC25]" />
              )}
              <span>Regenerate</span>
            </button>

            <button
              onClick={() => onSectionAiAction('Improve')}
              disabled={isRegenerating !== null}
              className="px-2.5 py-1 text-[11px] font-bold text-slate-800 bg-white hover:bg-slate-100 border border-slate-200 rounded transition-colors"
            >
              Improve
            </button>

            <button
              onClick={() => onSectionAiAction('Shorten')}
              disabled={isRegenerating !== null}
              className="px-2.5 py-1 text-[11px] font-bold text-slate-800 bg-white hover:bg-slate-100 border border-slate-200 rounded transition-colors"
            >
              Shorten
            </button>

            <button
              onClick={() => onSectionAiAction('Expand')}
              disabled={isRegenerating !== null}
              className="px-2.5 py-1 text-[11px] font-bold text-slate-800 bg-white hover:bg-slate-100 border border-slate-200 rounded transition-colors"
            >
              Expand
            </button>
          </div>
        </div>

        {/* AI Resource Usage Small Indication */}
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-mono bg-slate-50 px-2.5 py-1 rounded border border-slate-200/80">
          <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span>AI regeneration operates on this section and consumes generation resources.</span>
        </div>

        {/* Text Manipulation Toolbar (Undo / Redo / Save) */}
        <div className="flex items-center justify-between bg-[#F5F6F7] p-2 rounded border border-slate-200 text-xs">
          <div className="flex items-center gap-1">
            <button
              onClick={handleUndo}
              disabled={historyIndex <= 0}
              className={`p-1.5 rounded transition-colors ${
                historyIndex > 0 ? 'text-slate-700 hover:bg-slate-200' : 'text-slate-300 cursor-not-allowed'
              }`}
              title="Undo"
            >
              <Undo className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={handleRedo}
              disabled={historyIndex >= contentHistory.length - 1}
              className={`p-1.5 rounded transition-colors ${
                historyIndex < contentHistory.length - 1
                  ? 'text-slate-700 hover:bg-slate-200'
                  : 'text-slate-300 cursor-not-allowed'
              }`}
              title="Redo"
            >
              <Redo className="w-3.5 h-3.5" />
            </button>

            <span className="text-slate-300 px-1">|</span>

            <span className="text-[11px] font-mono text-slate-500">
              Status: <strong className={autosaveStatus === 'Unsaved changes' ? 'text-amber-700' : 'text-slate-700'}>{autosaveStatus}</strong>
            </span>
          </div>

          <button
            onClick={onSaveSection}
            className="inline-flex items-center gap-1 px-3 py-1 bg-[#111827] text-white text-[11px] font-bold rounded hover:bg-[#007629] transition-colors"
          >
            <Save className="w-3 h-3 text-[#86BC25]" />
            <span>Save Section</span>
          </button>
        </div>

        {/* Textarea Document Editor View */}
        <textarea
          rows={16}
          value={section.content}
          onChange={(e) => handleTextChange(e.target.value)}
          className="w-full p-4 text-xs font-sans text-slate-900 bg-white border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-[#86BC25] leading-relaxed resize-y shadow-inner"
        />
      </div>

      {/* Footer Word Count & Save Status */}
      <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-[11px] font-mono text-slate-500">
        <span>
          Words: <strong className="text-slate-800">{wordsCount}</strong> | Characters: <strong className="text-slate-800">{charsCount}</strong>
        </span>

        <button
          onClick={onSaveSection}
          className="text-xs font-bold text-[#007629] hover:underline"
        >
          Save Section Changes
        </button>
      </div>
    </div>
  );
};
