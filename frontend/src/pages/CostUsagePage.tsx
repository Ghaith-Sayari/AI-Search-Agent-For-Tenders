import React from 'react';
import { CostMetrics } from '../types';
import { KpiCard } from '../components/common/KpiCard';
import {
  DollarSign,
  Cpu,
  Layers,
  Zap,
  ShieldCheck,
  TrendingUp,
  BarChart2,
  Database,
  PieChart as PieIcon,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface CostUsagePageProps {
  metrics: CostMetrics;
}

export const CostUsagePage: React.FC<CostUsagePageProps> = ({ metrics }) => {
  const COLORS = ['#86BC25', '#111827', '#F59E0B', '#64748B'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            AI Pipeline Cost & LLM Token Observability
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Monitor API expenditure, prompt token density, cache efficiency, and cost per qualified tender opportunity.
          </p>
        </div>

        <div className="bg-emerald-50 text-emerald-900 border border-emerald-300 px-3 py-1.5 rounded-md text-xs font-mono font-bold">
          Optimization Efficiency: <strong className="text-[#007629]">High ({metrics.cacheHitRatePercent}% Cache Hit)</strong>
        </div>
      </div>

      {/* Top 6 KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard
          title="Total LLM Calls"
          value={metrics.totalLlmCalls.toLocaleString()}
          subtitle="Model invocations"
          icon={Cpu}
          accentColor="bg-slate-800"
        />
        <KpiCard
          title="Input Tokens"
          value={`${(metrics.inputTokens / 1000000).toFixed(2)}M`}
          subtitle="Prompt token volume"
          icon={Layers}
          accentColor="bg-slate-700"
        />
        <KpiCard
          title="Output Tokens"
          value={`${(metrics.outputTokens / 1000000).toFixed(2)}M`}
          subtitle="Generated completions"
          icon={Zap}
          accentColor="bg-slate-700"
        />
        <KpiCard
          title="Estimated Cost"
          value={`$${metrics.estimatedCostUsd.toFixed(2)}`}
          subtitle="24h cumulative expense"
          trend={{ value: 'Under Budget ($180)', isPositive: true }}
          icon={DollarSign}
          accentColor="bg-[#86BC25]"
        />
        <KpiCard
          title="Cost / Opportunity"
          value={`$${metrics.costPerOpportunityUsd.toFixed(2)}`}
          subtitle="Per qualified tender"
          icon={TrendingUp}
          accentColor="bg-emerald-600"
        />
        <KpiCard
          title="Avg Tokens / Req"
          value={metrics.avgTokensPerRequest.toLocaleString()}
          subtitle="Tokens per call"
          icon={BarChart2}
          accentColor="bg-slate-800"
        />
      </div>

      {/* Optimization & Efficiency Highlight Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase text-slate-400 block">
              Prompt Cache Hit Rate
            </span>
            <span className="text-xl font-extrabold text-[#007629] font-mono">
              {metrics.cacheHitRatePercent}%
            </span>
          </div>
          <div className="p-2 bg-emerald-50 rounded-md border border-emerald-200 text-[#007629]">
            <Zap className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase text-slate-400 block">
              Calls Avoided via Rules
            </span>
            <span className="text-xl font-extrabold text-slate-900 font-mono">
              {metrics.llmCallsAvoidedByRules.toLocaleString()}
            </span>
          </div>
          <div className="p-2 bg-slate-100 rounded-md border border-slate-200 text-slate-700">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase text-slate-400 block">
              Avg Prompt Size
            </span>
            <span className="text-xl font-extrabold text-slate-900 font-mono">
              {metrics.avgPromptSizeTokens} <span className="text-xs font-normal text-slate-500">tokens</span>
            </span>
          </div>
          <div className="p-2 bg-slate-100 rounded-md border border-slate-200 text-slate-700">
            <Layers className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase text-slate-400 block">
              Model API Retries
            </span>
            <span className="text-xl font-extrabold text-slate-900 font-mono">
              {metrics.retryCount}
            </span>
          </div>
          <div className="p-2 bg-amber-50 rounded-md border border-amber-200 text-amber-700">
            <Cpu className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Cost Over Time Area Chart */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
              Daily LLM Cost ($)
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">7-Day Expenditure</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics.costOverTime} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#86BC25" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#86BC25" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', borderRadius: '6px', color: '#FFF', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="cost" stroke="#007629" strokeWidth={2} fillOpacity={1} fill="url(#costGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* LLM Calls by Stage Pie Chart */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
              LLM Usage & Cost by Pipeline Stage
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">Stage Breakdown</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.callsByStage}
                  dataKey="cost"
                  nameKey="stage"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {metrics.callsByStage.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', borderRadius: '6px', color: '#FFF', fontSize: '12px' }}
                />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => <span className="text-xs text-slate-700 font-medium">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
