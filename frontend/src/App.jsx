import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import SearchBar from './components/SearchBar';
import RequirementWizard from './components/RequirementWizard';
import ProductGrid from './components/ProductGrid';
import ComparisonTable from './components/ComparisonTable';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ProductDetailsModal from './components/ProductDetailsModal';
import ProviderStatusBanner from './components/ProviderStatusBanner';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';
import ErrorState from './components/ErrorState';
import { fetchIntent, fetchQuestions, generateRecommendations, fetchProvidersStatus } from './services/api';

export default function App() {
  const [step, setStep] = useState('home'); // 'home' | 'wizard' | 'results'
  const [activeView, setActiveView] = useState('recommendations'); // 'recommendations' | 'comparison' | 'analytics'
  const [query, setQuery] = useState('');
  const [intent, setIntent] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [userAnswers, setUserAnswers] = useState({});
  const [pipelineData, setPipelineData] = useState(null);
  const [providers, setProviders] = useState([]);
  const [isProviderModalOpen, setIsProviderModalOpen] = useState(false);
  const [selectedProductModal, setSelectedProductModal] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [error, setError] = useState(null);

  // Initial provider status fetch
  useEffect(() => {
    fetchProvidersStatus()
      .then((data) => setProviders(data))
      .catch((err) => console.error("Could not fetch provider status:", err));
  }, []);

  // Handler: User searches on Homepage
  const handleSearch = async (searchQuery) => {
    try {
      setError(null);
      setQuery(searchQuery);
      setIsLoading(true);
      setLoadingMessage(`Analyzing intent for "${searchQuery}"...`);

      const detectedIntent = await fetchIntent(searchQuery);
      setIntent(detectedIntent);

      const dynamicQuestions = await fetchQuestions(searchQuery, detectedIntent.detected_category);
      setQuestions(dynamicQuestions);

      setStep('wizard');
    } catch (err) {
      console.error(err);
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler: User submits personalized requirements
  const handleGenerateRecommendations = async (answers) => {
    try {
      setError(null);
      setUserAnswers(answers);
      setIsLoading(true);
      setLoadingMessage(`Querying live marketplace feeds & scoring products...`);

      const result = await generateRecommendations(query, intent?.detected_category, answers);
      setPipelineData(result);
      if (result.provider_statuses) {
        setProviders(result.provider_statuses);
      }

      setStep('results');
      setActiveView('recommendations');
    } catch (err) {
      console.error(err);
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setStep('home');
    setQuery('');
    setIntent(null);
    setQuestions([]);
    setPipelineData(null);
    setError(null);
  };

  const handleEditSearch = () => {
    setStep('home');
  };

  const providerDiagnostics = pipelineData?.provider_statuses
    ?.filter((provider) => provider.diagnostic_code !== 'skipped_for_category')
    .filter((provider) => provider.diagnostic_code !== 'provider_disabled')
    .filter((provider) => provider.diagnostic_code !== 'success')
    .map((provider) => `${provider.name}: ${provider.message}`)
    .join(' ');

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Navigation */}
      <Navbar
        onReset={handleReset}
        onViewProviders={() => setIsProviderModalOpen(true)}
        activeView={step === 'results' ? activeView : 'home'}
        setActiveView={setActiveView}
        providersCount={providers.length}
        liveItemCount={pipelineData?.total_products_found || 0}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error State */}
        {error && (
          <ErrorState
            error={error}
            onRetry={() => {
              if (step === 'wizard') handleGenerateRecommendations(userAnswers);
              else handleSearch(query);
            }}
          />
        )}

        {/* Loading State */}
        {isLoading && <LoadingState message={loadingMessage} />}

        {/* STEP 1: HOME (Search-first) */}
        {!isLoading && step === 'home' && (
          <div className="space-y-12 my-6">
            {/* Hero Section */}
            <div className="text-center max-w-3xl mx-auto space-y-4">
              <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-bold tracking-wide">
                <span>⚡ Real-Time Multi-Marketplace Intelligence</span>
              </div>
              <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
                Honest Shopping Research & Recommendations
              </h1>
              <p className="text-sm sm:text-base text-slate-600 font-normal max-w-2xl mx-auto">
                Search any product. Answer a few dynamic questions tailored to your search. TrustRank scans live marketplace listings, filters real ratings, and ranks the best options with full transparency.
              </p>

              {/* Prominent Search Bar */}
              <div className="pt-4">
                <SearchBar
                  onSearch={handleSearch}
                  isLoading={isLoading}
                  initialQuery={query}
                />
              </div>
            </div>

            {/* Core Workflow Pillars */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 max-w-5xl mx-auto pt-6 text-left">
              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                  1
                </div>
                <h3 className="font-bold text-sm text-slate-900">Intent-First Search</h3>
                <p className="text-xs text-slate-500">
                  Search anything naturally. TrustRank understands what you're looking for without forcing pre-defined categories.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                  2
                </div>
                <h3 className="font-bold text-sm text-slate-900">Dynamic Requirements</h3>
                <p className="text-xs text-slate-500">
                  Questions are generated specifically for your search—from RAM/GPU for laptops to skin concerns for skincare.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                  3
                </div>
                <h3 className="font-bold text-sm text-slate-900">Real Live Products</h3>
                <p className="text-xs text-slate-500">
                  No fake product catalogs. Live marketplace feeds with verified prices in INR and genuine buyer feedback.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-sm">
                  4
                </div>
                <h3 className="font-bold text-sm text-slate-900">Top 5 & Analytics</h3>
                <p className="text-xs text-slate-500">
                  Side-by-side Top 5 comparison matrix and real-time category analytics dashboard.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: REQUIREMENT WIZARD */}
        {!isLoading && step === 'wizard' && intent && (
          <RequirementWizard
            intent={intent}
            questions={questions}
            onGenerate={handleGenerateRecommendations}
            onEditSearch={handleEditSearch}
            isLoading={isLoading}
          />
        )}

        {/* STEP 3: RESULTS & DASHBOARDS */}
        {!isLoading && step === 'results' && pipelineData && (
          <div className="space-y-6">
            {/* Search Header Banner */}
            <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                    {pipelineData.intent?.category_display_name || 'Category'}
                  </span>
                  <span className="text-xs text-slate-500">
                    Query: <strong>"{pipelineData.query}"</strong>
                  </span>
                  <span className="text-xs text-emerald-600 font-semibold">
                    • {pipelineData.recommendations.length} live recommendations
                  </span>
                </div>
                <h2 className="text-xl font-bold text-slate-900 mt-1">
                  TrustRank Recommendations & Research
                </h2>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setStep('wizard')}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition"
                >
                  Adjust Requirements
                </button>
                <button
                  onClick={handleReset}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition"
                >
                  New Search
                </button>
              </div>
            </div>

            {/* View Sub-Navigation */}
            <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
              <button
                onClick={() => setActiveView('recommendations')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                  activeView === 'recommendations'
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/20'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                }`}
              >
                All Ranked Recommendations ({pipelineData.recommendations.length})
              </button>
              <button
                onClick={() => setActiveView('comparison')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                  activeView === 'comparison'
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/20'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                }`}
              >
                Top 5 Comparison Matrix
              </button>
              <button
                onClick={() => setActiveView('analytics')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                  activeView === 'analytics'
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/20'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                }`}
              >
                Analytical Dashboard
              </button>
            </div>

            {/* View Content */}
            {activeView === 'recommendations' && (
              <ProductGrid
                recommendations={pipelineData.recommendations}
                onSelectProduct={(p) => setSelectedProductModal(p)}
              />
            )}

            {activeView === 'comparison' && (
              <ComparisonTable
                comparisonProducts={pipelineData.top_5_comparison}
                onSelectProduct={(p) => setSelectedProductModal(p)}
              />
            )}

            {activeView === 'analytics' && (
              <AnalyticsDashboard analytics={pipelineData.analytics} />
            )}
          </div>
        )}

        {/* Empty state if results empty */}
        {!isLoading && step === 'results' && (!pipelineData || pipelineData.recommendations.length === 0) && (
          <EmptyState
            title="No live products retrieved"
            message={providerDiagnostics || "We were unable to retrieve live product listings matching this exact query from authorized providers. Check provider status or try another search."}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Product Details Modal */}
      {selectedProductModal && (
        <ProductDetailsModal
          product={selectedProductModal}
          onClose={() => setSelectedProductModal(null)}
        />
      )}

      {/* Provider Status Modal */}
      <ProviderStatusBanner
        providers={providers}
        isOpen={isProviderModalOpen}
        onClose={() => setIsProviderModalOpen(false)}
      />

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-xs py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-xs">
              TR
            </div>
            <span className="font-bold text-slate-200">TrustRank Shopping Intelligence</span>
            <span>—</span>
            <span>Zero fake products. Live marketplace verified.</span>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={() => setIsProviderModalOpen(true)}
              className="text-slate-300 hover:text-indigo-400 transition"
            >
              Provider Credentials Status
            </button>
            <span>•</span>
            <span>Prices displayed in Indian Rupees (₹ / INR)</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
