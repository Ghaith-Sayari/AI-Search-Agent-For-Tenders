import React, { useState } from 'react';
import { CompanyProfile } from '../types';
import {
  Building2,
  Sliders,
  CheckCircle2,
  Save,
  Globe,
  DollarSign,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

interface SettingsPageProps {
  profile: CompanyProfile;
  onSaveProfile: (updated: CompanyProfile) => Promise<void>;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ profile, onSaveProfile }) => {
  const [formData, setFormData] = useState<CompanyProfile>({ ...profile });
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  React.useEffect(() => {
    setFormData({ ...profile });
  }, [profile]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveError(null);
    try {
      await onSaveProfile(formData);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save profile.');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Company Profile & AI Threshold Configuration
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure the corporate capabilities and qualification thresholds evaluated by the AI Gatekeeper.
          </p>
        </div>

        {savedSuccess && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-900 border border-emerald-300 rounded-md text-xs font-bold">
            <CheckCircle2 className="w-4 h-4 text-[#007629]" />
            <span>Profile Configuration Saved</span>
          </div>
        )}
      </div>

      {saveError && (
        <div className="px-3 py-2 rounded-md border border-red-300 bg-red-50 text-red-800 text-xs font-semibold">
          {saveError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Company Identity */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
            <Building2 className="w-4 h-4 text-[#86BC25]" />
            <h3 className="text-xs font-bold uppercase text-slate-800 tracking-wider">
              1. Corporate Entity Identity
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-600 font-bold mb-1">Company Practice Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              />
            </div>

            <div>
              <label className="block text-slate-600 font-bold mb-1">Primary Sector</label>
              <input
                type="text"
                value={formData.primarySector}
                onChange={(e) => setFormData({ ...formData, primarySector: e.target.value })}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-600 font-bold mb-1 text-xs">Company Description</label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full p-2 bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-600 font-bold mb-1">Sub-Sectors (comma separated)</label>
              <input
                type="text"
                value={formData.subSectors.join(', ')}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    subSectors: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })
                }
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              />
            </div>

            <div>
              <label className="block text-slate-600 font-bold mb-1">Core Services (comma separated)</label>
              <input
                type="text"
                value={formData.coreServices.join(', ')}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    coreServices: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })
                }
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              />
            </div>
          </div>
        </div>

        {/* Contract Value & Targets */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
            <DollarSign className="w-4 h-4 text-emerald-600" />
            <h3 className="text-xs font-bold uppercase text-slate-800 tracking-wider">
              2. Contract Value Tiers & Target Geographies
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-slate-600 font-bold mb-1">Min Contract Budget (€)</label>
              <input
                type="number"
                value={formData.minContractValueEur}
                onChange={(e) => setFormData({ ...formData, minContractValueEur: Number(e.target.value) })}
                className="w-full p-2 font-mono bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              />
            </div>

            <div>
              <label className="block text-slate-600 font-bold mb-1">Max Target Budget (€)</label>
              <input
                type="number"
                value={formData.maxContractValueEur}
                onChange={(e) => setFormData({ ...formData, maxContractValueEur: Number(e.target.value) })}
                className="w-full p-2 font-mono bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              />
            </div>

            <div>
              <label className="block text-slate-600 font-bold mb-1">Target Countries (ISO)</label>
              <input
                type="text"
                value={formData.targetCountries.join(', ')}
                onChange={(e) => setFormData({ ...formData, targetCountries: e.target.value.split(',').map((s) => s.trim()) })}
                className="w-full p-2 font-mono bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
              />
            </div>
          </div>
        </div>

        {/* AI Gatekeeper Threshold Controls */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
            <Sliders className="w-4 h-4 text-[#86BC25]" />
            <h3 className="text-xs font-bold uppercase text-slate-800 tracking-wider">
              3. AI Gatekeeper Qualification Thresholds
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            <div className="space-y-2">
              <div className="flex justify-between font-bold">
                <label className="text-slate-700">Min Gatekeeper Qualification Score</label>
                <span className="font-mono text-[#007629] font-bold">{formData.gatekeeperMinScore} / 100</span>
              </div>
              <input
                type="range"
                min={40}
                max={90}
                value={formData.gatekeeperMinScore}
                onChange={(e) => setFormData({ ...formData, gatekeeperMinScore: Number(e.target.value) })}
                className="w-full accent-[#007629]"
              />
              <p className="text-[11px] text-slate-500">
                Tenders scoring below this threshold are marked as <strong>NOT FIT</strong> automatically.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between font-bold">
                <label className="text-slate-700">Auto-Approval Threshold</label>
                <span className="font-mono text-emerald-700 font-bold">{formData.autoApproveThreshold} / 100</span>
              </div>
              <input
                type="range"
                min={70}
                max={98}
                value={formData.autoApproveThreshold}
                onChange={(e) => setFormData({ ...formData, autoApproveThreshold: Number(e.target.value) })}
                className="w-full accent-[#86BC25]"
              />
              <p className="text-[11px] text-slate-500">
                Tenders scoring at or above this score skip human review and are flagged as <strong>GOOD FIT</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#111827] hover:bg-[#007629] text-white font-bold text-xs rounded-md shadow-xs transition-colors"
          >
            <Save className="w-4 h-4 text-[#86BC25]" />
            <span>Save Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
};
