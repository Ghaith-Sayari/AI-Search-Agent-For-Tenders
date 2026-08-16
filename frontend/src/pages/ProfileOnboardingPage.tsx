import React, { useState } from 'react';
import { CompanyProfile } from '../types';
import { Building2, Save } from 'lucide-react';

interface ProfileOnboardingPageProps {
  profile: CompanyProfile;
  onSaveProfile: (updated: CompanyProfile) => Promise<void>;
}

export const ProfileOnboardingPage: React.FC<ProfileOnboardingPageProps> = ({
  profile,
  onSaveProfile,
}) => {
  const [formData, setFormData] = useState<CompanyProfile>({ ...profile });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSaving(true);
    try {
      await onSaveProfile(formData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-2xl bg-white border border-slate-200 rounded-lg p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Building2 className="w-5 h-5 text-[#86BC25]" />
          <h1 className="text-lg font-bold text-slate-900">Set up your company profile</h1>
        </div>
        <p className="text-sm text-slate-600">
          Complete this once to enable proposal generation tailored to your organization.
        </p>

        {error && (
          <div className="px-3 py-2 rounded-md border border-red-300 bg-red-50 text-red-800 text-xs font-semibold">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Company Name</label>
            <input
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full p-2 border border-slate-300 rounded"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Primary Sector</label>
            <input
              value={formData.primarySector}
              onChange={(e) => setFormData({ ...formData, primarySector: e.target.value })}
              className="w-full p-2 border border-slate-300 rounded"
            />
          </div>
        </div>

        <div className="text-sm">
          <label className="block font-semibold text-slate-700 mb-1">Company Description</label>
          <textarea
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full p-2 border border-slate-300 rounded"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Core Services (comma separated)</label>
            <input
              value={formData.coreServices.join(', ')}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  coreServices: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                })
              }
              className="w-full p-2 border border-slate-300 rounded"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Target Countries (comma separated)</label>
            <input
              value={formData.targetCountries.join(', ')}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  targetCountries: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                })
              }
              className="w-full p-2 border border-slate-300 rounded"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSaving}
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#111827] text-white rounded disabled:opacity-60"
        >
          <Save className="w-4 h-4 text-[#86BC25]" />
          <span>{isSaving ? 'Saving...' : 'Save profile and continue'}</span>
        </button>
      </form>
    </div>
  );
};

