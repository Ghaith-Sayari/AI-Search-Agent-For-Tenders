import React, { useState } from 'react';
import { Opportunity } from '../types';
import { ScoreIndicator } from '../components/common/ScoreIndicator';
import { DecisionBadge } from '../components/common/DecisionBadge';
import { ScoreBreakdownBars } from '../components/common/ScoreBreakdownBars';
import {
  BarChart3,
  Search,
  Filter,
  Eye,
  X,
  Sparkles,
  Award,
  Globe,
  Briefcase,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

interface AnalysesPageProps {
  opportunities: Opportunity[];
  onSelectOpportunity: (id: string) => void;
}

export const AnalysesPage: React.FC<AnalysesPageProps> = ({
  opportunities,
  onSelectOpportunity,
}) => {
  const [selectedAnalysis, setSelectedAnalysis] = useState<Opportunity | null>(null);
  const [search, setSearch] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState<'score' | 'confidence' | 'date'>('score');

  let filtered = opportunities.filter((o) => {
    if (search) {
      const q = search.toLowerCase();
      if (
        !o.title.toLowerCase().includes(q) &&
        !o.sector.toLowerCase().includes(q) &&
        !o.country.toLowerCase().includes(q)
      ) {
        return false;
      }
    }
    if (decisionFilter !== 'ALL' && o.decision !== decisionFilter) {
      return false;
    }
    return true;
  });

  filtered.sort((a, b) => {
    if (sortBy === 'score') return b.overallScore - a.overallScore;
    if (sortBy === 'confidence') return b.confidence - a.confidence;
    if (sortBy === 'date') return new Date(b.lastAnalyzedAt).getTime() - new Date(a.lastAnalyzedAt).getTime();
    return 0;
  });

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Opportunity Fit Workspace
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Multidimensional vector evaluation across Sector, Services, Geography, Eligibility, and Strategy dimensions.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono bg-slate-100 p-1.5 rounded-md border border-slate-200">
          <span className="text-slate-500">Evaluated:</span>
          <strong className="text-slate-900">{opportunities.length} tenders</strong>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search tender title, sector or country..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-300 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value)}
            className="bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
          >
            <option value="ALL">All Decisions</option>
            <option value="GOOD_FIT">Good Fit</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="NOT_FIT">Not Fit</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
          >
            <option value="score">Sort by Overall Score</option>
            <option value="confidence">Sort by AI Confidence</option>
            <option value="date">Sort by Last Analyzed</option>
          </select>
        </div>
      </div>

      {/* Analysis Matrix Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 border-collapse">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 uppercase font-mono text-[10px] sticky top-0">
              <tr>
                <th className="py-3 px-3">Opportunity</th>
                <th className="py-3 px-2 text-center">Overall</th>
                <th className="py-3 px-2 text-center">Sector</th>
                <th className="py-3 px-2 text-center">Services</th>
                <th className="py-3 px-2 text-center">Geography</th>
                <th className="py-3 px-2 text-center">Eligibility</th>
                <th className="py-3 px-2 text-center">Strategic</th>
                <th className="py-3 px-3">Decision</th>
                <th className="py-3 px-3">Confidence</th>
                <th className="py-3 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {filtered.map((opp) => (
                <tr
                  key={opp.id}
                  className="hover:bg-slate-50 transition-colors cursor-pointer"
                  onClick={() => setSelectedAnalysis(opp)}
                >
                  <td className="py-3 px-3 max-w-[260px] font-sans">
                    <div className="font-bold text-slate-900 truncate" title={opp.title}>
                      {opp.title}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      {opp.country} • {opp.sector}
                    </div>
                  </td>
                  <td className="py-3 px-2 text-center font-extrabold text-slate-900">
                    <ScoreIndicator score={opp.overallScore} size="sm" />
                  </td>
                  <td className="py-3 px-2 text-center font-bold text-slate-800">
                    {opp.scoreBreakdown.sectorRelevance}
                  </td>
                  <td className="py-3 px-2 text-center font-bold text-slate-800">
                    {opp.scoreBreakdown.servicesRelevance}
                  </td>
                  <td className="py-3 px-2 text-center font-bold text-slate-800">
                    {opp.scoreBreakdown.geographyRelevance}
                  </td>
                  <td className="py-3 px-2 text-center font-bold text-slate-800">
                    {opp.scoreBreakdown.eligibilityFit}
                  </td>
                  <td className="py-3 px-2 text-center font-bold text-slate-800">
                    {opp.scoreBreakdown.strategicFit}
                  </td>
                  <td className="py-3 px-3 font-sans">
                    <DecisionBadge decision={opp.decision} size="sm" />
                  </td>
                  <td className="py-3 px-3 text-slate-600 text-[11px]">
                    {opp.confidence}%
                  </td>
                  <td className="py-3 px-3 text-right font-sans">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAnalysis(opp);
                      }}
                      className="px-2.5 py-1 text-xs font-semibold text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Side Modal/Drawer */}
      {selectedAnalysis && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-xl bg-white h-full shadow-2xl p-6 overflow-y-auto space-y-6 flex flex-col justify-between">
            <div className="space-y-5">
              <div className="flex items-start justify-between border-b border-slate-200 pb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <DecisionBadge decision={selectedAnalysis.decision} />
                    <span className="text-xs font-mono text-slate-400">{selectedAnalysis.externalId}</span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 leading-snug">
                    {selectedAnalysis.title}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedAnalysis(null)}
                  className="p-1 rounded text-slate-400 hover:text-slate-900 hover:bg-slate-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase font-bold text-slate-500 font-mono">
                    Overall Fit Score
                  </span>
                  <ScoreIndicator score={selectedAnalysis.overallScore} size="lg" showLabel />
                </div>
                <ScoreBreakdownBars scoreBreakdown={selectedAnalysis.scoreBreakdown} />
              </div>

              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
                  AI Qualification Findings
                </h4>
                <div className="bg-emerald-50 p-3 rounded border border-emerald-200 text-xs space-y-1.5">
                  <div className="font-bold text-emerald-900 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Key Matched Strengths
                  </div>
                  {selectedAnalysis.aiReasoning.matched.map((m, idx) => (
                    <p key={idx} className="text-emerald-800 text-[11px] pl-4">
                      • {m}
                    </p>
                  ))}
                </div>

                <div className="bg-amber-50 p-3 rounded border border-amber-200 text-xs space-y-1.5">
                  <div className="font-bold text-amber-900 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    Missing / Qualification Risk
                  </div>
                  {selectedAnalysis.aiReasoning.missingOrRisk.map((r, idx) => (
                    <p key={idx} className="text-amber-800 text-[11px] pl-4">
                      • {r}
                    </p>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-2">
              <button
                onClick={() => setSelectedAnalysis(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md"
              >
                Close
              </button>
              <button
                onClick={() => {
                  const id = selectedAnalysis.id;
                  setSelectedAnalysis(null);
                  onSelectOpportunity(id);
                }}
                className="px-4 py-2 text-xs font-bold text-white bg-[#111827] hover:bg-[#007629] rounded-md"
              >
                Open Full Detail Workspace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
