import React from 'react';
import { SystemService, SystemIncident } from '../types';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  Server,
  Zap,
  ShieldAlert,
  Database,
  Cpu,
  RefreshCw,
} from 'lucide-react';

interface SystemHealthPageProps {
  services: SystemService[];
  incidents: SystemIncident[];
  onRefresh: () => void;
}

export const SystemHealthPage: React.FC<SystemHealthPageProps> = ({
  services,
  incidents,
  onRefresh,
}) => {
  const healthyCount = services.filter((s) => s.status === 'HEALTHY').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            System Health & Infrastructure Observability
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time status monitoring for web scrapers, Celery queues, AI models, state caches and PostgreSQL DB.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-900 border border-emerald-300 font-mono text-xs font-bold px-3 py-1.5 rounded-md">
            <span className="w-2 h-2 rounded-full bg-[#86BC25] animate-ping" />
            <span>{healthyCount} / {services.length} Services Healthy</span>
          </div>

          <button
            onClick={onRefresh}
            className="p-1.5 text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-md shadow-xs"
            title="Refresh Service Status"
          >
            <RefreshCw className="w-4 h-4 text-slate-600" />
          </button>
        </div>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {services.map((srv) => {
          let statusBadge = (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-mono">
              <CheckCircle2 className="w-3 h-3 text-[#007629]" />
              Healthy
            </span>
          );
          if (srv.status === 'DEGRADED') {
            statusBadge = (
              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-mono">
                <AlertTriangle className="w-3 h-3 text-amber-600" />
                Degraded
              </span>
            );
          }
          if (srv.status === 'DOWN') {
            statusBadge = (
              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-red-800 bg-red-50 px-2 py-0.5 rounded border border-red-200 font-mono">
                <XCircle className="w-3 h-3 text-red-600" />
                Down
              </span>
            );
          }

          return (
            <div
              key={srv.id}
              className="bg-white rounded-lg border border-slate-200 shadow-xs p-4 flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] uppercase font-mono font-semibold text-slate-400">
                    {srv.category}
                  </span>
                  {statusBadge}
                </div>

                <h3 className="text-sm font-bold text-slate-900 leading-snug">
                  {srv.name}
                </h3>
              </div>

              <div className="bg-slate-50 p-2.5 rounded border border-slate-200 font-mono text-[11px] space-y-1 text-slate-700">
                <div className="flex justify-between">
                  <span className="text-slate-400">Latency:</span>
                  <strong className="text-slate-900">{srv.latencyMs} ms</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Uptime:</span>
                  <strong className="text-emerald-700">{srv.uptimePercent}%</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">24h Errors:</span>
                  <strong className={srv.errorCount24h > 0 ? 'text-amber-600' : 'text-slate-800'}>
                    {srv.errorCount24h}
                  </strong>
                </div>
              </div>

              <p className="text-[11px] text-slate-500 line-clamp-2 leading-tight">
                {srv.details}
              </p>
            </div>
          );
        })}
      </div>

      {/* Incidents Audit Log Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-100 pb-2">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-slate-700" />
            <h3 className="text-xs font-bold uppercase text-slate-700 tracking-wider">
              Recent System Incidents & Exception Log
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Last 7 Days</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Service</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Incident Description</th>
                <th className="py-2.5 px-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {incidents.map((inc) => (
                <tr key={inc.id} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">{inc.timestamp}</td>
                  <td className="py-2.5 px-3 font-bold text-slate-900 whitespace-nowrap">{inc.service}</td>
                  <td className="py-2.5 px-3 whitespace-nowrap">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800 font-bold">
                      {inc.severity}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-slate-800 font-sans">{inc.message}</td>
                  <td className="py-2.5 px-3 text-right whitespace-nowrap font-bold text-emerald-700">
                    {inc.resolved ? '✓ Resolved' : '● Active'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
