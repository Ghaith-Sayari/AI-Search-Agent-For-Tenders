import React from 'react';
import { Opportunity, PipelineRun, CostMetrics } from '../types';
import { KpiCard } from '../components/common/KpiCard';
import { ScoreIndicator } from '../components/common/ScoreIndicator';
import { DecisionBadge } from '../components/common/DecisionBadge';
import {
  Target,
  CheckCircle2,
  AlertTriangle,
  Award,
  GitBranch,
  DollarSign,
  ArrowRight,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

interface DashboardPageProps {
  opportunities: Opportunity[];
  pipelineRuns: PipelineRun[];
  costMetrics: CostMetrics;
  onNavigate: (route: any) => void;
  onSelectOpportunity: (id: string) => void;
  onSelectRun: (id: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  opportunities,
  pipelineRuns,
  costMetrics,
  onNavigate,
  onSelectOpportunity,
  onSelectRun,
}) => {
  // KPI Calculations
  const totalOpps = opportunities.length;
  const goodFitCount = opportunities.filter((o) => o.decision === 'GOOD_FIT').length;
  const needsReviewCount = opportunities.filter((o) => o.decision === 'NEEDS_REVIEW').length;
  const notFitCount = opportunities.filter((o) => o.decision === 'NOT_FIT').length;
  const failedCount = opportunities.filter((o) => o.decision === 'FAILED').length;

  const avgScore =
    totalOpps > 0
      ? Math.round(opportunities.reduce((acc, o) => acc + o.overallScore, 0) / totalOpps)
      : 0;

  // Chart Data Preparation - Deloitte Palette
  // Deloitte Green = #86BC25, Dark Deloitte Green = #007629, Amber = #F59E0B, Gray = #64748B, Red = #EF4444
  const decisionChartData = [
    { name: 'Good Fit', value: goodFitCount, color: '#86BC25' },
    { name: 'Needs Review', value: needsReviewCount, color: '#F59E0B' },
    { name: 'Not Fit', value: notFitCount, color: '#64748B' },
    { name: 'Failed', value: failedCount, color: '#EF4444' },
  ];

  const scoreRangeData = [
    { range: '80 - 100 (High)', count: opportunities.filter((o) => o.overallScore >= 80).length, fill: '#86BC25' },
    { range: '60 - 79 (Medium)', count: opportunities.filter((o) => o.overallScore >= 60 && o.overallScore < 80).length, fill: '#F59E0B' },
    { range: '40 - 59 (Low)', count: opportunities.filter((o) => o.overallScore >= 40 && o.overallScore < 60).length, fill: '#94A3B8' },
    { range: '0 - 39 (Unfit)', count: opportunities.filter((o) => o.overallScore < 40).length, fill: '#EF4444' },
  ];

  const recentOpps = opportunities.slice(0, 5);
  const recentRuns = pipelineRuns.slice(0, 4);

  return (
    <div className="space-y-6">
      {/* Page Title Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
              Opportunity Intelligence
            </h2>
            <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-900 text-white">
              EMEA Executive View
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Monitor tender ingestion, AI qualification, opportunity fit analysis and review activity across public sector feeds.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('opportunities')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-800 bg-white border border-slate-300 rounded-md hover:bg-slate-50 shadow-xs"
          >
            <span>View All Opportunities</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
          </button>
        </div>
      </div>

      {/* Top 6 KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard
          title="Total Opportunities"
          value={totalOpps}
          subtitle="Monitored tender notices"
          icon={Target}
          accentColor="bg-slate-800"
        />
        <KpiCard
          title="Good Fit"
          value={goodFitCount}
          subtitle={`${Math.round((goodFitCount / (totalOpps || 1)) * 100)}% of total qualified`}
          trend={{ value: '+12% this week', isPositive: true }}
          icon={CheckCircle2}
          accentColor="bg-[#86BC25]"
        />
        <KpiCard
          title="Needs Review"
          value={needsReviewCount}
          subtitle="Pending human override"
          trend={{ value: `${needsReviewCount} items in queue`, isPositive: false }}
          icon={AlertTriangle}
          accentColor="bg-amber-500"
        />
        <KpiCard
          title="Avg Opportunity Score"
          value={`${avgScore} / 100`}
          subtitle="Multidimensional fit average"
          icon={Award}
          accentColor="bg-slate-700"
        />
        <KpiCard
          title="Pipeline Runs"
          value={pipelineRuns.length}
          subtitle="Total ingestion executions"
          icon={GitBranch}
          accentColor="bg-slate-800"
        />
        <KpiCard
          title="LLM Cost (24h)"
          value={`$${costMetrics.estimatedCostUsd.toFixed(2)}`}
          subtitle={`$${costMetrics.costPerOpportunityUsd.toFixed(2)} / opportunity`}
          icon={DollarSign}
          accentColor="bg-emerald-600"
        />
      </div>

      {/* Chart Visualizations Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Opportunity Distribution Donut Chart */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
              Opportunity Decision Breakdown
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">Real-time Classification</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={decisionChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {decisionChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', borderRadius: '6px', color: '#FFF', fontSize: '12px' }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  formatter={(value) => <span className="text-xs text-slate-700 font-medium">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Opportunity Score Distribution Bar Chart */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
              Score Range Distribution
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">0 - 100 Fit Tiers</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRangeData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <XAxis dataKey="range" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', borderRadius: '6px', color: '#FFF', fontSize: '12px' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {scoreRangeData.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Opportunities & Pipeline Activity Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Opportunities (2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 shadow-xs p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
                  Recent Opportunity Matches
                </h3>
                <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono font-semibold">
                  Latest 5
                </span>
              </div>
              <button
                onClick={() => onNavigate('opportunities')}
                className="text-xs font-semibold text-[#007629] hover:underline flex items-center gap-1"
              >
                View All <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-y border-slate-200 uppercase font-mono text-[10px]">
                  <tr>
                    <th className="py-2.5 px-3">Opportunity</th>
                    <th className="py-2.5 px-2">Country</th>
                    <th className="py-2.5 px-2">Score</th>
                    <th className="py-2.5 px-2">Decision</th>
                    <th className="py-2.5 px-2">Deadline</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentOpps.map((opp) => (
                    <tr
                      key={opp.id}
                      onClick={() => {
                        onSelectOpportunity(opp.id);
                        onNavigate('opportunities');
                      }}
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="py-2.5 px-3 max-w-[280px]">
                        <div className="font-bold text-slate-900 truncate" title={opp.title}>
                          {opp.title}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {opp.externalId} • {opp.sector}
                        </div>
                      </td>
                      <td className="py-2.5 px-2 whitespace-nowrap">
                        <span className="font-medium text-slate-800">{opp.country}</span>
                      </td>
                      <td className="py-2.5 px-2 whitespace-nowrap">
                        <ScoreIndicator score={opp.overallScore} size="sm" />
                      </td>
                      <td className="py-2.5 px-2 whitespace-nowrap">
                        <DecisionBadge decision={opp.decision} size="sm" />
                      </td>
                      <td className="py-2.5 px-2 whitespace-nowrap font-mono text-slate-600 text-[11px]">
                        {opp.deadline}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Pipeline Activity (1 Col) */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
                Pipeline Activity
              </h3>
              <button
                onClick={() => onNavigate('runs')}
                className="text-xs font-semibold text-[#007629] hover:underline flex items-center gap-1"
              >
                All Runs <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-3">
              {recentRuns.map((run) => (
                <div
                  key={run.id}
                  onClick={() => {
                    onSelectRun(run.id);
                    onNavigate('runs');
                  }}
                  className="p-3 rounded-md border border-slate-200 hover:border-[#86BC25] bg-slate-50 hover:bg-white cursor-pointer transition-all text-xs"
                >
                  <div className="flex items-center justify-between font-mono font-bold text-slate-900 mb-1">
                    <span>{run.id}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-mono ${
                        run.status === 'COMPLETED'
                          ? 'bg-emerald-100 text-emerald-800'
                          : run.status === 'RUNNING'
                          ? 'bg-amber-100 text-amber-800 animate-pulse'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {run.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mb-2">
                    {run.triggeredBy} • {run.startedAt}
                  </div>
                  <div className="grid grid-cols-3 gap-1 text-[11px] font-mono text-center bg-white p-1.5 rounded border border-slate-200">
                    <div>
                      <div className="text-slate-400 text-[9px] uppercase">Processed</div>
                      <div className="font-bold text-slate-800">{run.processedCount}</div>
                    </div>
                    <div>
                      <div className="text-slate-400 text-[9px] uppercase">Approved</div>
                      <div className="font-bold text-emerald-700">{run.approvedCount}</div>
                    </div>
                    <div>
                      <div className="text-slate-400 text-[9px] uppercase font-semibold">Review</div>
                      <div className="font-bold text-amber-600">{run.reviewCount}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
