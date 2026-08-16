import React from 'react';
import {
  ProposalLanguage,
  ProposalType,
  ProposalTone,
  CreateProposalPayload,
} from '../../types/proposal';
import { CompanyProfile } from '../../types';
import { Sparkles, Info, RotateCw } from 'lucide-react';

interface ProposalConfigurationProps {
  initialTitle: string;
  companyProfile: CompanyProfile;
  onSubmit: (payload: CreateProposalPayload) => void;
  isGenerating: boolean;
  disabled?: boolean;
}

export const ProposalConfiguration: React.FC<ProposalConfigurationProps> = ({
  initialTitle,
  companyProfile,
  onSubmit,
  isGenerating,
  disabled = false,
}) => {
  const [title, setTitle] = React.useState(initialTitle || 'Proposal Draft');
  const [profileId, setProfileId] = React.useState('prof-01');
  const [language, setLanguage] = React.useState<ProposalLanguage>('English');
  const [type, setType] = React.useState<ProposalType>('Technical Proposal');
  const [tone, setTone] = React.useState<ProposalTone>('Professional');
  const [instructions, setInstructions] = React.useState('');

  React.useEffect(() => {
    if (initialTitle) {
      setTitle(initialTitle);
    }
  }, [initialTitle]);

  const presetInstructions = [
    'Emphasize our cloud modernization experience.',
    'Focus on cybersecurity capabilities.',
    'Highlight relevant government projects.',
    'Emphasize EU data sovereignty & GDPR compliance.',
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled || isGenerating) return;

    onSubmit({
      opportunityId: '',
      proposalTitle: title,
      companyProfileId: profileId,
      companyProfileName: companyProfile.name,
      language,
      proposalType: type,
      tone,
      additionalInstructions: instructions,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
        <span className="w-6 h-6 rounded-full bg-[#111827] text-[#86BC25] font-mono text-xs font-bold flex items-center justify-center shrink-0">
          ⚙
        </span>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900">
          Proposal Configuration
        </h3>
      </div>

      {/* Proposal Title */}
      <div className="space-y-1">
        <label className="text-xs font-bold text-slate-800">Proposal Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={disabled || isGenerating}
          className="w-full px-3 py-1.5 text-xs bg-[#F5F6F7] border border-slate-200 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
          required
        />
      </div>

      {/* Company Profile */}
      <div className="space-y-1">
        <label className="text-xs font-bold text-slate-800">Company Profile</label>
        <select
          value={profileId}
          onChange={(e) => setProfileId(e.target.value)}
          disabled={disabled || isGenerating}
          className="w-full px-3 py-1.5 text-xs bg-[#F5F6F7] border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
        >
          <option value="prof-01">{companyProfile.name} (Default Company Profile)</option>
          <option value="prof-02">Deloitte Cybersecurity & Defense Practice</option>
          <option value="prof-03">Deloitte Public Sector Cloud Advisory</option>
        </select>
      </div>

      {/* Language & Proposal Type */}
      <div className="grid grid-cols-2 gap-2.5">
        <div className="space-y-1">
          <label className="text-xs font-bold text-slate-800">Proposal Language</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as ProposalLanguage)}
            disabled={disabled || isGenerating}
            className="w-full px-3 py-1.5 text-xs bg-[#F5F6F7] border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
          >
            <option value="English">English</option>
            <option value="French">French</option>
            <option value="Arabic">Arabic</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-xs font-bold text-slate-800">Proposal Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as ProposalType)}
            disabled={disabled || isGenerating}
            className="w-full px-3 py-1.5 text-xs bg-[#F5F6F7] border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
          >
            <option value="Technical Proposal">Technical Proposal</option>
            <option value="Commercial Proposal">Commercial Proposal</option>
            <option value="Full Proposal">Full Proposal</option>
          </select>
        </div>
      </div>

      {/* Tone */}
      <div className="space-y-1">
        <label className="text-xs font-bold text-slate-800">Tone</label>
        <select
          value={tone}
          onChange={(e) => setTone(e.target.value as ProposalTone)}
          disabled={disabled || isGenerating}
          className="w-full px-3 py-1.5 text-xs bg-[#F5F6F7] border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-[#86BC25]"
        >
          <option value="Professional">Professional</option>
          <option value="Formal">Formal</option>
          <option value="Executive">Executive</option>
          <option value="Technical">Technical</option>
        </select>
      </div>

      {/* Additional Instructions */}
      <div className="space-y-1.5">
        <label className="text-xs font-bold text-slate-800">Additional Instructions</label>
        <textarea
          rows={3}
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          disabled={disabled || isGenerating}
          placeholder="Add specific instructions for the proposal..."
          className="w-full p-2.5 text-xs bg-[#F5F6F7] border border-slate-200 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#86BC25] leading-relaxed resize-y"
        />

        {/* Example Prompt Preset Chips */}
        <div className="flex flex-wrap gap-1 pt-1">
          {presetInstructions.map((chip) => (
            <button
              key={chip}
              type="button"
              disabled={disabled || isGenerating}
              onClick={() =>
                setInstructions((prev) => (prev ? `${prev} ${chip}` : chip))
              }
              className="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded font-mono border border-slate-200 transition-colors"
            >
              + {chip}
            </button>
          ))}
        </div>
      </div>

      {/* Quality Notice & Action Area */}
      <div className="pt-3 border-t border-slate-100 space-y-3">
        <div className="p-2.5 bg-amber-50/80 border border-amber-200 rounded text-[11px] text-amber-900 flex items-start gap-2">
          <Info className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
          <span>
            <strong>Human Review Required:</strong> AI-generated content requires human review before submission.
          </span>
        </div>

        <button
          type="submit"
          disabled={disabled || isGenerating}
          className={`w-full py-2.5 px-4 text-xs font-bold text-white rounded transition-all flex items-center justify-center gap-2 shadow-xs ${
            disabled
              ? 'bg-slate-300 cursor-not-allowed text-slate-500'
              : isGenerating
              ? 'bg-slate-800 cursor-not-allowed'
              : 'bg-[#007629] hover:bg-[#005f20] active:scale-98'
          }`}
        >
          {isGenerating ? (
            <>
              <RotateCw className="w-4 h-4 animate-spin text-[#86BC25]" />
              <span>Generating Proposal Draft...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 text-[#86BC25]" />
              <span>Generate Proposal Draft</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
