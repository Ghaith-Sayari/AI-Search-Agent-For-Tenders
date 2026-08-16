import React, { useState } from 'react';
import { Opportunity } from '../types';
import { FilterBar } from '../components/common/FilterBar';
import { ScoreIndicator } from '../components/common/ScoreIndicator';
import { DecisionBadge } from '../components/common/DecisionBadge';
import { FetchOpportunitiesParams } from '../services/api';
import {
  RotateCw,
  Play,
  Download,
  ExternalLink,
  ChevronRight,
  Eye,
  Sparkles,
  FileSpreadsheet,
} from 'lucide-react';

interface OpportunitiesPageProps {
  opportunities: Opportunity[];
  onFilterChange: (params: FetchOpportunitiesParams) => void;
  onSelectOpportunity: (id: string) => void;
  onReAnalyze: (id: string) => void;
  onRefresh: () => void;
  isAnalyzingId?: string | null;
}

export const OpportunitiesPage: React.FC<OpportunitiesPageProps> = ({
  opportunities,
  onFilterChange,
  onSelectOpportunity,
  onReAnalyze,
  onRefresh,
  isAnalyzingId = null,
}) => {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const handleExport = (format: 'csv' | 'json') => {
    if (opportunities.length === 0) return;
    if (format === 'csv') {
      const headers = ['ID', 'Title', 'Country', 'Source', 'Score', 'Decision', 'Deadline', 'EstimatedValue'];
      const rows = opportunities.map((o) => [
        o.id,
        `"${o.title.replace(/"/g, '""')}"`,
        o.country,
        `"${o.source}"`,
        o.overallScore,
        o.decision,
        o.deadline,
        `"${o.estimatedValue}"`,
      ]);
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', `tender_opportunities_${new Date().toISOString().substring(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === opportunities.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(opportunities.map((o) => o.id));
    }
  };

  const toggleSelectOne = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  return (
    <div className="space-y-4">
      {/* Page Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Opportunities Directory
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time public tender feed qualified and scored by AI Gatekeeper according to corporate profile rules.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 shadow-xs"
          >
            <RotateCw className="w-3.5 h-3.5 text-slate-500" />
            Refresh Feed
          </button>

          <button
            onClick={() => handleExport('csv')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-800 bg-slate-100 border border-slate-300 rounded-md hover:bg-slate-200 shadow-xs"
          >
            <Download className="w-3.5 h-3.5 text-slate-600" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filter Bar Component */}
      <FilterBar
        onFilterChange={onFilterChange}
        onExport={handleExport}
        totalResults={opportunities.length}
      />

      {/* Main Data Table Container */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 border-collapse">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 uppercase font-mono text-[10px] sticky top-0 z-10">
              <tr>
                <th className="py-3 px-3 w-8">
                  <input
                    type="checkbox"
                    checked={opportunities.length > 0 && selectedIds.length === opportunities.length}
                    onChange={toggleSelectAll}
                    className="rounded border-slate-300 text-[#86BC25] focus:ring-[#86BC25]"
                  />
                </th>
                <th className="py-3 px-3">Opportunity & Sector</th>
                <th className="py-3 px-3">Country</th>
                <th className="py-3 px-3">Source Feed</th>
                <th className="py-3 px-3">Est. Value</th>
                <th className="py-3 px-3">Score</th>
                <th className="py-3 px-3">Decision</th>
                <th className="py-3 px-3">Deadline</th>
                <th className="py-3 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {opportunities.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    <FileSpreadsheet className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="font-semibold text-slate-700">No opportunities match the selected criteria.</p>
                    <p className="text-xs text-slate-400 mt-1">Try relaxing filters or search query.</p>
                  </td>
                </tr>
              ) : (
                opportunities.map((opp) => (
                  <tr
                    key={opp.id}
                    className={`hover:bg-slate-50/80 transition-colors ${
                      selectedIds.includes(opp.id) ? 'bg-emerald-50/30' : ''
                    }`}
                  >
                    <td className="py-3 px-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(opp.id)}
                        onChange={() => toggleSelectOne(opp.id)}
                        className="rounded border-slate-300 text-[#86BC25] focus:ring-[#86BC25]"
                      />
                    </td>
                    <td
                      onClick={() => onSelectOpportunity(opp.id)}
                      className="py-3 px-3 max-w-[320px] cursor-pointer"
                    >
                      <div className="font-bold text-slate-900 hover:text-[#007629] transition-colors leading-snug line-clamp-2">
                        {opp.title}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-1 flex items-center gap-2">
                        <span>{opp.externalId}</span>
                        <span>•</span>
                        <span className="text-slate-600 font-sans">{opp.sector}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap font-medium text-slate-800">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-[10px] bg-slate-100 text-slate-600 px-1 py-0.2 rounded border border-slate-200">
                          {opp.countryCode}
                        </span>
                        <span>{opp.country}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap text-slate-600 text-[11px] max-w-[140px] truncate" title={opp.source}>
                      {opp.source}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap font-mono font-bold text-slate-900">
                      {opp.estimatedValue}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <ScoreIndicator score={opp.overallScore} size="sm" showLabel />
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <DecisionBadge decision={opp.decision} size="sm" />
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap font-mono text-[11px] text-slate-600">
                      {opp.deadline}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => onSelectOpportunity(opp.id)}
                          className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded border border-slate-200"
                          title="View Opportunity Detail Workspace"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => onReAnalyze(opp.id)}
                          disabled={isAnalyzingId === opp.id}
                          className="p-1.5 text-slate-600 hover:text-[#007629] hover:bg-emerald-50 rounded border border-slate-200"
                          title="Run AI Fit Re-Analysis"
                        >
                          <Sparkles
                            className={`w-3.5 h-3.5 ${
                              isAnalyzingId === opp.id ? 'animate-spin text-[#86BC25]' : 'text-slate-500'
                            }`}
                          />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Table Footer Stats */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 font-mono">
          <div>
            Showing {opportunities.length} opportunities ({selectedIds.length} selected)
          </div>
          <div>Page 1 of 1 • Enterprise Feed Active</div>
        </div>
      </div>
    </div>
  );
};
