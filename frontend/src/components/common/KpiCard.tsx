import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  icon?: LucideIcon;
  accentColor?: string; // Deloitte green accent bar
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  accentColor = 'bg-[#86BC25]',
}) => {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-xs p-4 relative overflow-hidden flex flex-col justify-between">
      <div className={`absolute top-0 left-0 right-0 h-1 ${accentColor}`} />
      
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs uppercase font-semibold text-slate-500 tracking-wider">
          {title}
        </span>
        {Icon && (
          <div className="p-1.5 rounded-md bg-slate-100 text-slate-700">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between mt-1">
        <div className="text-2xl font-extrabold text-slate-900 tracking-tight font-mono">
          {value}
        </div>
        {trend && (
          <span
            className={`inline-flex items-center text-xs font-semibold px-1.5 py-0.5 rounded ${
              trend.isPositive !== false
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-amber-50 text-amber-800 border border-amber-200'
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-xs text-slate-500 mt-2 border-t border-slate-100 pt-1.5">
          {subtitle}
        </p>
      )}
    </div>
  );
};
