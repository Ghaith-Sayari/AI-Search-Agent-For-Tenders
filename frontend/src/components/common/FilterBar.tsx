import React, { useState } from 'react';
import { Search, Filter, RotateCcw, ChevronDown, ChevronUp, Download } from 'lucide-react';
import { FetchOpportunitiesParams } from '../../services/api';

interface FilterBarProps {
  onFilterChange: (params: FetchOpportunitiesParams) => void;
  onExport?: (format: 'csv' | 'json') => void;
  totalResults?: number;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  onFilterChange,
  onExport,
  totalResults,
}) => {
  const [search, setSearch] = useState('');
  const [country, setCountry] = useState('ALL');
  const [source, setSource] = useState('ALL');
  const [decision, setDecision] = useState('ALL');
  const [scoreRange, setScoreRange] = useState<'ALL' | '80-100' | '60-79' | '0-59'>('ALL');
  const [sortBy, setSortBy] = useState<'score' | 'deadline' | 'published'>('score');
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  const applyFilters = (overrides?: Partial<{
    search: string;
    country: string;
    source: string;
    decision: string;
    scoreRange: string;
    sortBy: 'score' | 'deadline' | 'published';
  }>) => {
    const activeSearch = overrides?.search !== undefined ? overrides.search : search;
    const activeCountry = overrides?.country !== undefined ? overrides.country : country;
    const activeSource = overrides?.source !== undefined ? overrides.source : source;
    const activeDecision = overrides?.decision !== undefined ? overrides.decision : decision;
    const activeScoreRange = overrides?.scoreRange !== undefined ? overrides.scoreRange : scoreRange;
    const activeSortBy = overrides?.sortBy !== undefined ? overrides.sortBy : sortBy;

    let minScore: number | undefined;
    let maxScore: number | undefined;

    if (activeScoreRange === '80-100') {
      minScore = 80;
      maxScore = 100;
    } else if (activeScoreRange === '60-79') {
      minScore = 60;
      maxScore = 79;
    } else if (activeScoreRange === '0-59') {
      minScore = 0;
      maxScore = 59;
    }

    onFilterChange({
      search: activeSearch,
      country: activeCountry,
      source: activeSource,
      decision: activeDecision,
      minScore,
      maxScore,
      sortBy: activeSortBy,
      sortOrder: 'desc',
    });
  };

  const handleReset = () => {
    setSearch('');
    setCountry('ALL');
    setSource('ALL');
    setDecision('ALL');
    setScoreRange('ALL');
    setSortBy('score');
    onFilterChange({ sortBy: 'score', sortOrder: 'desc' });
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-3 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Search input */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search tender title, sector, keyword or reference ID..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              applyFilters({ search: e.target.value });
            }}
            className="w-full pl-9 pr-3 py-1.5 text-sm bg-slate-50 border border-slate-300 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25] focus:border-[#86BC25]"
          />
        </div>

        {/* Quick Decision Filter */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-md border border-slate-200 text-xs font-medium">
          {['ALL', 'GOOD_FIT', 'NEEDS_REVIEW', 'NOT_FIT', 'FAILED'].map((dec) => (
            <button
              key={dec}
              onClick={() => {
                setDecision(dec);
                applyFilters({ decision: dec });
              }}
              className={`px-2.5 py-1 rounded tracking-tight transition-colors ${
                decision === dec
                  ? 'bg-slate-900 text-white font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {dec === 'ALL' ? 'All Decisions' : dec.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Filter Toggle & Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50"
          >
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            Filters
            {isAdvancedOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {onExport && (
            <button
              onClick={() => onExport('csv')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-800 bg-slate-100 border border-slate-300 rounded-md hover:bg-slate-200"
            >
              <Download className="w-3.5 h-3.5 text-slate-600" />
              Export
            </button>
          )}

          <button
            onClick={handleReset}
            title="Reset Filters"
            className="p-1.5 text-slate-500 hover:text-slate-900 bg-slate-50 border border-slate-200 rounded-md hover:bg-slate-100"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Advanced Filters Expandable Panel */}
      {isAdvancedOpen && (
        <div className="pt-3 border-t border-slate-200 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          {/* Country */}
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Country</label>
            <select
              value={country}
              onChange={(e) => {
                setCountry(e.target.value);
                applyFilters({ country: e.target.value });
              }}
              className="w-full bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
            >
              <option value="ALL">All Countries</option>
              <option value="Germany">Germany (DE)</option>
              <option value="United Kingdom">United Kingdom (UK)</option>
              <option value="France">France (FR)</option>
              <option value="Netherlands">Netherlands (NL)</option>
              <option value="Sweden">Sweden (SE)</option>
              <option value="Belgium">Belgium (BE)</option>
              <option value="EU">Multilateral / NATO / EU</option>
            </select>
          </div>

          {/* Source Feed */}
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Source Feed</label>
            <select
              value={source}
              onChange={(e) => {
                setSource(e.target.value);
                applyFilters({ source: e.target.value });
              }}
              className="w-full bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
            >
              <option value="ALL">All Sources</option>
              <option value="TED">TED (EU Official)</option>
              <option value="Contracts Finder">Contracts Finder (UK)</option>
              <option value="BOAMP">BOAMP (France)</option>
              <option value="TenderNed">TenderNed (NL)</option>
              <option value="NATO">NATO NCIA</option>
              <option value="TendSign">TendSign Sweden</option>
            </select>
          </div>

          {/* Score Tier */}
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Score Range</label>
            <select
              value={scoreRange}
              onChange={(e) => {
                const val = e.target.value as any;
                setScoreRange(val);
                applyFilters({ scoreRange: val });
              }}
              className="w-full bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
            >
              <option value="ALL">All Scores (0 - 100)</option>
              <option value="80-100">80 - 100 (High Fit)</option>
              <option value="60-79">60 - 79 (Medium / Review)</option>
              <option value="0-59">0 - 59 (Low / Reject)</option>
            </select>
          </div>

          {/* Sort Order */}
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => {
                const val = e.target.value as any;
                setSortBy(val);
                applyFilters({ sortBy: val });
              }}
              className="w-full bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
            >
              <option value="score">Highest Fit Score</option>
              <option value="deadline">Nearest Deadline</option>
              <option value="published">Recently Published</option>
            </select>
          </div>
        </div>
      )}

      {totalResults !== undefined && (
        <div className="text-xs text-slate-500 flex items-center justify-between pt-1">
          <span>Showing <strong className="text-slate-800 font-mono">{totalResults}</strong> tender opportunities</span>
          <span className="text-[11px] text-slate-400">Profile: Deloitte Digital EMEA</span>
        </div>
      )}
    </div>
  );
};
