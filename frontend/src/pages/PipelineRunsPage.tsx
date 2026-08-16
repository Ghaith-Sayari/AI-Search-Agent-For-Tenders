import React, { useState } from 'react';
import { PipelineRun, PipelineStage } from '../types';
import {
  GitBranch,
  Play,
  RotateCw,
  CheckCircle2,
  Clock,
  AlertOctagon,
  ChevronRight,
  Database,
  Filter,
  Sparkles,
  ArrowDown,
  Layers,
  Cpu,
} from 'lucide-react';

interface PipelineRunsPageProps {
  runs: PipelineRun[];
  selectedRunId?: string | null;
  onSelectRun: (id: string) => void;
  onTriggerRun: () => void;
  isRunExecuting?: boolean;
}

export const PipelineRunsPage: React.FC<PipelineRunsPageProps> = ({
  runs,
  selectedRunId,
  onSelectRun,
  onTriggerRun,
  isRunExecuting,
}) => {
  const currentRun = runs.find((r) => r.id === selectedRunId) || (runs.length > 0 ? runs[0] : null);

  const STAGE_STEPS: { stage: PipelineStage; name: string; description: string }[] = [
    { stage: 'INGESTION', name: '1. Ingestion', description: 'Scrape public feeds & webhooks' },
    { stage: 'NORMALIZATION', name: '2. Normalization', description: 'Extract text, PDF tables & schema' },
    { stage: 'GATEKEEPER', name: '3. Gatekeeper', description: 'AI qualification & company rule filter' },
    { stage: 'PRODUCTION', name: '4. Enrichment', description: 'Buyer history & financial stats' },
    { stage: 'OPPORTUNITY_ANALYSIS', name: '5. Fit Analysis', description: 'Multidimensional scoring & reasoning' },
    { stage: 'REVIEW', name: '6. Review Routing', description: 'Human-in-the-loop queue assignment' },
    { stage: 'COMPLETED', name: '7. Completion', description: 'Pipeline run finalized' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Pipeline Execution Runs
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor automated ingestion, AI Gatekeeper filtering, fit scoring jobs, and execution metrics.
          </p>
        </div>

        <button
          onClick={onTriggerRun}
          disabled={isRunExecuting}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-[#111827] hover:bg-[#007629] rounded-md shadow-xs disabled:bg-slate-400"
        >
          {isRunExecuting ? (
            <RotateCw className="w-3.5 h-3.5 animate-spin text-[#86BC25]" />
          ) : (
            <Play className="w-3.5 h-3.5 text-[#86BC25] fill-[#86BC25]" />
          )}
          <span>{isRunExecuting ? 'Executing Run...' : 'Trigger Manual Pipeline Run'}</span>
        </button>
      </div>

      {/* Runs Summary Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-3 px-3">Run ID</th>
                <th className="py-3 px-3">Trigger Source</th>
                <th className="py-3 px-3">Started</th>
                <th className="py-3 px-3">Duration</th>
                <th className="py-3 px-3">Current Stage</th>
                <th className="py-3 px-3">Processed</th>
                <th className="py-3 px-3">Approved</th>
                <th className="py-3 px-3">Review</th>
                <th className="py-3 px-3">LLM Calls</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {runs.map((r) => {
                const isSelected = currentRun?.id === r.id;
                return (
                  <tr
                    key={r.id}
                    onClick={() => onSelectRun(r.id)}
                    className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                      isSelected ? 'bg-emerald-50/50 font-bold border-l-4 border-l-[#86BC25]' : ''
                    }`}
                  >
                    <td className="py-3 px-3 text-slate-900 font-bold">{r.id}</td>
                    <td className="py-3 px-3 text-slate-700 font-sans">{r.triggeredBy}</td>
                    <td className="py-3 px-3 text-slate-600 text-[11px]">{r.startedAt}</td>
                    <td className="py-3 px-3 text-slate-600">{r.durationSeconds}s</td>
                    <td className="py-3 px-3 text-slate-800 uppercase text-[10px] font-bold">
                      {r.currentStage}
                    </td>
                    <td className="py-3 px-3 text-slate-900">{r.processedCount}</td>
                    <td className="py-3 px-3 text-emerald-700 font-bold">{r.approvedCount}</td>
                    <td className="py-3 px-3 text-amber-600 font-bold">{r.reviewCount}</td>
                    <td className="py-3 px-3 text-slate-800">{r.llmCallsCount}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                          r.status === 'COMPLETED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : r.status === 'RUNNING'
                            ? 'bg-amber-100 text-amber-800 animate-pulse'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual Pipeline Stage Timeline Detail */}
      {currentRun && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-5 space-y-5">
          <div className="flex items-center justify-between border-b border-slate-200 pb-3">
            <div>
              <div className="flex items-center gap-2 font-mono text-xs">
                <span className="font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                  {currentRun.id}
                </span>
                <span className="text-slate-500">
                  Started: {currentRun.startedAt}
                </span>
              </div>
              <h3 className="text-base font-extrabold text-slate-900 mt-1">
                Business Pipeline Stage Flow Breakdown
              </h3>
            </div>

            <div className="text-right font-mono text-xs">
              <span className="text-slate-400 block">Total Duration</span>
              <strong className="text-slate-900 text-sm">{currentRun.durationSeconds}s</strong>
            </div>
          </div>

          {/* Visual Vertical / Horizontal Stage Timeline */}
          <div className="grid grid-cols-1 md:grid-cols-7 gap-2 pt-2">
            {STAGE_STEPS.map((step, idx) => {
              const matchedStage = currentRun.stages.find((s) => s.stage === step.stage);
              const status = matchedStage?.status || 'PENDING';

              let statusColor = 'bg-slate-100 border-slate-200 text-slate-400';
              if (status === 'COMPLETED') statusColor = 'bg-emerald-50 border-emerald-300 text-emerald-900';
              if (status === 'RUNNING') statusColor = 'bg-amber-50 border-amber-300 text-amber-900 animate-pulse';
              if (status === 'FAILED') statusColor = 'bg-red-50 border-red-300 text-red-900';

              return (
                <div key={step.stage} className="relative flex flex-col">
                  <div className={`p-3 rounded-lg border text-xs flex flex-col justify-between h-full space-y-2 ${statusColor}`}>
                    <div className="font-bold font-mono text-[11px] tracking-tight">
                      {step.name}
                    </div>
                    <div className="text-[10px] text-slate-600 leading-tight">
                      {step.description}
                    </div>

                    <div className="pt-2 border-t border-slate-200/60 font-mono text-[10px] space-y-0.5">
                      <div className="flex justify-between text-slate-500">
                        <span>Status:</span>
                        <strong className="uppercase">{status}</strong>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Duration:</span>
                        <span>{matchedStage?.durationSeconds || 0}s</span>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Processed:</span>
                        <span>{matchedStage?.processedCount || 0}</span>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Errors:</span>
                        <span className={matchedStage?.errorsCount ? 'text-red-600 font-bold' : ''}>
                          {matchedStage?.errorsCount || 0}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Stage Detail Notes */}
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs font-mono text-slate-700">
            <span className="font-bold text-slate-900 block mb-1 uppercase text-[10px] tracking-wider">
              Stage Log Notes
            </span>
            <ul className="space-y-1">
              {currentRun.stages.map((st) => (
                <li key={st.stage} className="flex items-center gap-2">
                  <span className="text-slate-400 w-32 shrink-0">{st.label}:</span>
                  <span className="text-slate-800">{st.details || 'Stage execution recorded.'}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};
