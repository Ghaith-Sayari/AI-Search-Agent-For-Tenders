import React, { useState, useEffect } from 'react';
import { NavRoute } from './components/layout/Sidebar';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { OpportunitiesPage } from './pages/OpportunitiesPage';
import { OpportunityDetailPage } from './pages/OpportunityDetailPage';
import { ProposalsPage } from './pages/ProposalsPage';
import { AnalysesPage } from './pages/AnalysesPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { PipelineRunsPage } from './pages/PipelineRunsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { CostUsagePage } from './pages/CostUsagePage';
import { SettingsPage } from './pages/SettingsPage';

import {
  Opportunity,
  ReviewItem,
  PipelineRun,
  SystemService,
  SystemIncident,
  CostMetrics,
  CompanyProfile,
} from './types';
import { apiService, FetchOpportunitiesParams } from './services/api';

export default function App() {
  const [currentRoute, setCurrentRoute] = useState<NavRoute>('dashboard');
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [proposalOppId, setProposalOppId] = useState<string | null>(null);

  // Data Stores
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [services, setServices] = useState<SystemService[]>([]);
  const [incidents, setIncidents] = useState<SystemIncident[]>([]);
  const [costMetrics, setCostMetrics] = useState<CostMetrics | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isRunExecuting, setIsRunExecuting] = useState(false);
  const [isAnalyzingId, setIsAnalyzingId] = useState<string | null>(null);

  // Initial Data Fetch
  const loadAllData = async (params?: FetchOpportunitiesParams) => {
    try {
      const [oppsData, reviewsData, runsData, healthData, metricsData, profileData] =
        await Promise.all([
          apiService.getOpportunities(params),
          apiService.getReviews(),
          apiService.getPipelineRuns(),
          apiService.getSystemHealth(),
          apiService.getCostMetrics(),
          apiService.getCompanyProfile(),
        ]);

      setOpportunities(oppsData);
      setReviews(reviewsData);
      setRuns(runsData);
      setServices(healthData.services);
      setIncidents(healthData.incidents);
      setCostMetrics(metricsData);
      setCompanyProfile(profileData);
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleFilterOpportunities = async (params: FetchOpportunitiesParams) => {
    const oppsData = await apiService.getOpportunities(params);
    setOpportunities(oppsData);
  };

  const handleTriggerRun = async () => {
    setIsRunExecuting(true);
    try {
      const newRun = await apiService.triggerPipelineRun('Manual Header Execution');
      const updatedRuns = await apiService.getPipelineRuns();
      setRuns(updatedRuns);
      setSelectedRunId(newRun.id);

      // Simulate step progression
      setTimeout(async () => {
        setIsRunExecuting(false);
        const refreshedRuns = await apiService.getPipelineRuns();
        setRuns(refreshedRuns);
      }, 1500);
    } catch (err) {
      console.error('Error executing run:', err);
      setIsRunExecuting(false);
    }
  };

  const handleReAnalyzeOpportunity = async (id: string) => {
    setIsAnalyzingId(id);
    try {
      await apiService.runOpportunityAnalysis(id);
      const updatedOpps = await apiService.getOpportunities();
      setOpportunities(updatedOpps);
    } catch (err) {
      console.error('Error re-analyzing opportunity:', err);
    } finally {
      setIsAnalyzingId(null);
    }
  };

  const handleResolveReview = async (
    reviewId: string,
    action: 'APPROVE' | 'REJECT' | 'SEND_BACK',
    overrideReason: string
  ) => {
    try {
      await apiService.resolveReview(reviewId, action, overrideReason, 'Ghaith Sayari (Senior Partner)');
      const [updatedReviews, updatedOpps] = await Promise.all([
        apiService.getReviews(),
        apiService.getOpportunities(),
      ]);
      setReviews(updatedReviews);
      setOpportunities(updatedOpps);
    } catch (err) {
      console.error('Error resolving review:', err);
    }
  };

  const handleSaveProfile = async (updated: CompanyProfile) => {
    try {
      const saved = await apiService.updateCompanyProfile(updated);
      setCompanyProfile(saved);
    } catch (err) {
      console.error('Error saving company profile:', err);
    }
  };

  const activeOpportunity = opportunities.find((o) => o.id === selectedOpportunityId) || null;
  const openReviewsCount = reviews.filter((r) => r.status === 'OPEN').length;

  if (isLoading || !costMetrics || !companyProfile) {
    return (
      <div className="min-h-screen bg-[#111827] text-white flex flex-col items-center justify-center p-6 font-mono">
        <div className="w-10 h-10 border-4 border-slate-700 border-t-[#86BC25] rounded-full animate-spin mb-4" />
        <p className="text-sm font-bold tracking-tight">Initializing TenderIntel Engine...</p>
        <p className="text-xs text-slate-400 mt-1">Loading AI Gatekeeper & Opportunity Intelligence Store</p>
      </div>
    );
  }

  return (
    <AppShell
      currentRoute={currentRoute}
      selectedOpportunityId={selectedOpportunityId}
      onNavigate={(route) => {
        setCurrentRoute(route);
        if (route !== 'opportunities') {
          setSelectedOpportunityId(null);
        }
      }}
      onTriggerRun={handleTriggerRun}
      isRunExecuting={isRunExecuting}
      reviewCount={openReviewsCount}
    >
      {/* Route Views Switching */}
      {currentRoute === 'dashboard' && (
        <DashboardPage
          opportunities={opportunities}
          pipelineRuns={runs}
          costMetrics={costMetrics}
          onNavigate={(route) => setCurrentRoute(route)}
          onSelectOpportunity={(id) => {
            setSelectedOpportunityId(id);
            setCurrentRoute('opportunities');
          }}
          onSelectRun={(id) => {
            setSelectedRunId(id);
            setCurrentRoute('runs');
          }}
        />
      )}

      {currentRoute === 'opportunities' &&
        (selectedOpportunityId && activeOpportunity ? (
          <OpportunityDetailPage
            opportunity={activeOpportunity}
            onBack={() => setSelectedOpportunityId(null)}
            onNavigateToReviews={() => setCurrentRoute('reviews')}
            onGenerateProposal={(id) => {
              setProposalOppId(id);
              setCurrentRoute('proposals');
            }}
          />
        ) : (
          <OpportunitiesPage
            opportunities={opportunities}
            onFilterChange={handleFilterOpportunities}
            onSelectOpportunity={(id) => setSelectedOpportunityId(id)}
            onReAnalyze={handleReAnalyzeOpportunity}
            onRefresh={() => loadAllData()}
            isAnalyzingId={isAnalyzingId}
          />
        ))}

      {currentRoute === 'proposals' && (
        <ProposalsPage
          opportunities={opportunities}
          companyProfile={companyProfile}
          initialOpportunityId={proposalOppId}
          onNavigateToOpportunity={(id) => {
            setSelectedOpportunityId(id);
            setCurrentRoute('opportunities');
          }}
        />
      )}

      {currentRoute === 'analyses' && (
        <AnalysesPage
          opportunities={opportunities}
          onSelectOpportunity={(id) => {
            setSelectedOpportunityId(id);
            setCurrentRoute('opportunities');
          }}
        />
      )}

      {currentRoute === 'reviews' && (
        <ReviewQueuePage
          reviews={reviews}
          opportunities={opportunities}
          onResolveReview={handleResolveReview}
          onSelectOpportunity={(id) => {
            setSelectedOpportunityId(id);
            setCurrentRoute('opportunities');
          }}
        />
      )}

      {currentRoute === 'runs' && (
        <PipelineRunsPage
          runs={runs}
          selectedRunId={selectedRunId}
          onSelectRun={(id) => setSelectedRunId(id)}
          onTriggerRun={handleTriggerRun}
          isRunExecuting={isRunExecuting}
        />
      )}

      {currentRoute === 'system' && (
        <SystemHealthPage
          services={services}
          incidents={incidents}
          onRefresh={() => loadAllData()}
        />
      )}

      {currentRoute === 'cost' && <CostUsagePage metrics={costMetrics} />}

      {currentRoute === 'settings' && (
        <SettingsPage profile={companyProfile} onSaveProfile={handleSaveProfile} />
      )}
    </AppShell>
  );
}
