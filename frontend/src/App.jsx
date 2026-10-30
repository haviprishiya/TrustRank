import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import SearchBar from './components/SearchBar';
import RequirementWizard from './components/RequirementWizard';
import ProductGrid from './components/ProductGrid';
import ComparisonTable from './components/ComparisonTable';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ProductDetailsModal from './components/ProductDetailsModal';
import ProviderStatusBanner from './components/ProviderStatusBanner';
import AuthModal from './components/AuthModal';
import LoadingState from './components/LoadingState';
import EmptyState from './components/EmptyState';
import ErrorState from './components/ErrorState';
import ReviewAnalysisDashboard from './components/ReviewAnalysisDashboard';
import CouponsOffersDashboard from './components/CouponsOffersDashboard';
import UserProfileDashboard from './components/UserProfileDashboard';
import PriceAlertModal from './components/PriceAlertModal';
import { fetchIntent, fetchQuestions, generateRecommendations, fetchProvidersStatus, generateImage, analyzeImage, apiGetMe, apiLogout, recordResearchActivity } from './services/api';

export default function App() {
  const [step, setStep] = useState('home'); // 'home' | 'wizard' | 'results'
  const [activeView, setActiveView] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('guest_id')) {
        try { localStorage.setItem('trustrank_guest_id', params.get('guest_id')); } catch (e) {}
      }
      if (params.get('view') === 'profile' || window.location.hash === '#profile') {
        return 'profile';
      }
      if (params.get('view') === 'coupons' || window.location.hash === '#coupons') {
        return 'coupons';
      }
      if (params.get('view') === 'review_analysis' || window.location.hash === '#review_analysis') {
        return 'review_analysis';
      }
    }
    return 'recommendations';
  }); // 'recommendations' | 'comparison' | 'analytics' | 'review_analysis'
  const [query, setQuery] = useState('');
  const [intent, setIntent] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [userAnswers, setUserAnswers] = useState({});
  const [pipelineData, setPipelineData] = useState(null);
  const [providers, setProviders] = useState([]);
  const [isProviderModalOpen, setIsProviderModalOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authToken, setAuthToken] = useState(localStorage.getItem('trustrank_auth_token') || null);
  const [welcomeToast, setWelcomeToast] = useState(null);
  const [selectedProductModal, setSelectedProductModal] = useState(null);
  const [alertProductModal, setAlertProductModal] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [error, setError] = useState(null);
  const [imagePrompt, setImagePrompt] = useState('');
  const [generatedImage, setGeneratedImage] = useState(null);
  const [imageUrl, setImageUrl] = useState('');
  const [imageAnalysis, setImageAnalysis] = useState(null);

  // Restore authenticated session
  useEffect(() => {
    if (authToken) {
      apiGetMe(authToken)
        .then((userData) => {
          if (userData) {
            setCurrentUser(userData);
          } else {
            localStorage.removeItem('trustrank_auth_token');
            setAuthToken(null);
          }
        })
        .catch(() => {
          localStorage.removeItem('trustrank_auth_token');
          setAuthToken(null);
        });
    }
  }, [authToken]);

  // Initial provider status fetch
  useEffect(() => {
    fetchProvidersStatus()
      .then((data) => setProviders(data.providers || []))
      .catch((err) => console.error("Could not fetch provider status:", err));
  }, []);

  const handleAuthSuccess = (authData) => {
    if (authData?.token && authData?.user) {
      localStorage.setItem('trustrank_auth_token', authData.token);
      setAuthToken(authData.token);
      setCurrentUser(authData.user);
      setWelcomeToast({
        title: authData.user.name ? `Welcome, ${authData.user.name}!` : `Welcome to TrustRank!`,
        message: `A welcome email has been sent to ${authData.user.email}. Check your inbox for your personalized shopping guide.`
      });
      setTimeout(() => setWelcomeToast(null), 8000);
    }
  };

  const handleLogout = async () => {
    if (authToken) {
      await apiLogout(authToken);
    }
    localStorage.removeItem('trustrank_auth_token');
    setAuthToken(null);
    setCurrentUser(null);
    setWelcomeToast({
      title: 'Signed Out',
      message: 'You have been safely signed out from your account.'
    });
    setTimeout(() => setWelcomeToast(null), 4000);
  };

  // Handler: User searches on Homepage
  const handleSearch = async (searchQuery) => {
    try {
      setError(null);
      setQuery(searchQuery);
      setIsLoading(true);
      setLoadingMessage(`Analyzing intent for "${searchQuery}"...`);

      const detectedIntent = await fetchIntent(searchQuery);
      setIntent(detectedIntent);
      recordResearchActivity(authToken, {
        category: 'search',
        title: `Searched for "${searchQuery}"`,
        query: searchQuery,
        metadata: { category: detectedIntent.detected_category }
      });

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

  const handleGenerateImage = async (event) => {
    event.preventDefault();
    if (!imagePrompt.trim()) return;
    try {
      setError(null);
      setIsLoading(true);
      setLoadingMessage('Generating image...');
      setGeneratedImage(await generateImage(imagePrompt.trim()));
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeImage = async (event) => {
    event.preventDefault();
    if (!imageUrl.trim()) return;
    try {
      setError(null);
      setIsLoading(true);
      setLoadingMessage('Analyzing image...');
      setImageAnalysis(await analyzeImage(imageUrl.trim()));
    } catch (err) {
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
      if (result.recommendations && result.recommendations.length > 0) {
        recordResearchActivity(authToken, {
          category: 'recommendation',
          title: `${result.recommendations.length} recommendations for "${query}"`,
          query: query,
          metadata: {
            total_ranked: result.recommendations.length,
            product: result.recommendations[0]?.product
          }
        });
      }
      if (result.top_5_comparison && result.top_5_comparison.length > 0) {
        recordResearchActivity(authToken, {
          category: 'comparison',
          title: `Compared Top 5 products for "${query}"`,
          query: query,
          metadata: {
            compared_products: result.top_5_comparison.map(p => ({
              id: p.id,
              title: p.title,
              price: p.current_price ?? p.price,
              marketplace: p.marketplace
            }))
          }
        });
      }
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
  if (activeView === 'profile') {
    return (
      <>
        <Navbar
          onReset={handleReset}
          onViewProviders={() => setIsProviderModalOpen(true)}
          activeView="profile"
          setActiveView={setActiveView}
          providersCount={providers.length}
          liveItemCount={pipelineData?.total_products_found || 0}
          currentUser={currentUser}
          onOpenAuthModal={() => setIsAuthModalOpen(true)}
          onLogout={handleLogout}
        />
        <UserProfileDashboard
          currentUser={currentUser}
          authToken={authToken}
          onOpenAuthModal={() => setIsAuthModalOpen(true)}
          onNavigateHome={() => { setStep('home'); setActiveView('home'); }}
          onNavigateRecommendations={() => { setStep('results'); setActiveView('recommendations'); }}
          onNavigateComparison={() => { setStep('results'); setActiveView('comparison'); }}
          onNavigateReviewAnalysis={(prod) => {
            if (prod) setSelectedProductModal(prod);
            setActiveView('review_analysis');
          }}
          onNavigateCoupons={() => setActiveView('coupons')}
          onReopenSearch={(pastQuery) => {
            handleSearch(pastQuery);
          }}
          onSelectProduct={(prod) => setSelectedProductModal(prod)}
          onOpenPriceAlert={(prod) => setAlertProductModal(prod)}
        />
        {selectedProductModal && (
          <ProductDetailsModal
            product={selectedProductModal}
            onClose={() => setSelectedProductModal(null)}
            onOpenPriceAlert={(p) => setAlertProductModal(p)}
          />
        )}
        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          onAuthSuccess={handleAuthSuccess}
        />
        <ProviderStatusBanner
          providers={providers}
          isOpen={isProviderModalOpen}
          onClose={() => setIsProviderModalOpen(false)}
        />
      </>
    );
  }

  if (activeView === 'coupons') {
    return (
      <>
        <CouponsOffersDashboard
          initialQuery={query}
          recommendations={pipelineData?.recommendations || []}
          onNavigateHome={() => { setStep('home'); setActiveView('home'); }}
          onNavigateRecommendations={() => { setStep('results'); setActiveView('recommendations'); }}
        />
        {selectedProductModal && (
          <ProductDetailsModal
            product={selectedProductModal}
            onClose={() => setSelectedProductModal(null)}
            onOpenPriceAlert={(p) => setAlertProductModal(p)}
          />
        )}
      </>
    );
  }

  if (activeView === 'review_analysis') {
    return (
      <>
        <ReviewAnalysisDashboard
          product={selectedProductModal || pipelineData?.recommendations?.[0]?.product || null}
          recommendations={pipelineData?.recommendations || []}
          onSelectProduct={(p, rec) => setSelectedProductModal(rec ? { ...p, _recommendation: rec } : p)}
          onNavigateHome={() => { setStep('home'); setActiveView('home'); }}
          onNavigateSearch={() => { setStep('home'); setActiveView('home'); }}
          onNavigateRecommendations={() => { setStep('results'); setActiveView('recommendations'); }}
          onNavigateComparison={() => { setStep('results'); setActiveView('comparison'); }}
          onNavigateProfile={() => setActiveView('profile')}
          onNavigateSettings={() => setIsProviderModalOpen(true)}
          currentUser={currentUser}
          onSearch={handleSearch}
        />
        {selectedProductModal && (
          <ProductDetailsModal
            product={selectedProductModal}
            onClose={() => setSelectedProductModal(null)}
            onOpenPriceAlert={(p) => setAlertProductModal(p)}
          />
        )}
        <ProviderStatusBanner
          providers={providers}
          isOpen={isProviderModalOpen}
          onClose={() => setIsProviderModalOpen(false)}
        />
        <AuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
          onAuthSuccess={handleAuthSuccess}
        />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans selection:bg-indigo-500 selection:text-white relative">
      {/* Welcome Email & Login Toast Notification */}
      {welcomeToast && (
        <div className="fixed top-20 right-4 sm:right-8 z-50 max-w-md w-full bg-slate-900 text-white p-4 rounded-2xl shadow-2xl border border-indigo-500/30 flex items-start space-x-3 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-emerald-500 flex items-center justify-center flex-shrink-0 text-white shadow-md">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-bold text-white tracking-tight">{welcomeToast.title}</h4>
            <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{welcomeToast.message}</p>
          </div>
          <button
            onClick={() => setWelcomeToast(null)}
            className="text-slate-400 hover:text-white transition p-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Navigation */}
      <Navbar
        onReset={handleReset}
        onViewProviders={() => setIsProviderModalOpen(true)}
        activeView={step === 'results' ? activeView : 'home'}
        setActiveView={setActiveView}
        providersCount={providers.length}
        liveItemCount={pipelineData?.total_products_found || 0}
        currentUser={currentUser}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl mx-auto">
              <section className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                <h2 className="font-bold text-slate-900">Image Generation</h2>
                <p className="text-xs text-slate-500 mt-1">Uses only a configured server-side provider.</p>
                <form onSubmit={handleGenerateImage} className="mt-3 flex gap-2">
                  <input value={imagePrompt} onChange={(event) => setImagePrompt(event.target.value)} className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="Describe an image" />
                  <button type="submit" className="rounded-lg bg-indigo-600 px-3 text-xs font-bold text-white">Generate</button>
                </form>
                {generatedImage?.image_url && <img className="mt-3 max-h-56 rounded-lg" src={generatedImage.image_url} alt={generatedImage.prompt || imagePrompt} />}
              </section>
              <section className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                <h2 className="font-bold text-slate-900">Image Analysis</h2>
                <p className="text-xs text-slate-500 mt-1">Analyze a publicly accessible product-image URL.</p>
                <form onSubmit={handleAnalyzeImage} className="mt-3 flex gap-2">
                  <input type="url" value={imageUrl} onChange={(event) => setImageUrl(event.target.value)} className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="https://…" />
                  <button type="submit" className="rounded-lg bg-indigo-600 px-3 text-xs font-bold text-white">Analyze</button>
                </form>
                {imageAnalysis && <pre className="mt-3 overflow-auto rounded bg-slate-50 p-2 text-xs">{JSON.stringify(imageAnalysis, null, 2)}</pre>}
              </section>
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
                  {pipelineData.intent?.extracted_requirements?.length > 0 && (
                    <span className="text-xs text-indigo-700 font-semibold">
                      Requirement: {pipelineData.intent.extracted_requirements.join(' + ')}
                    </span>
                  )}
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
              <button
                onClick={() => setActiveView('review_analysis')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                  activeView === 'review_analysis'
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-600/20'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                }`}
              >
                Review Analysis
              </button>
              <button
                onClick={() => setActiveView('coupons')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                  activeView === 'coupons'
                    ? 'bg-amber-600 text-white shadow-sm shadow-amber-600/20'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                }`}
              >
                Coupons & Offers
              </button>
              <button
                onClick={() => setActiveView('profile')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                  activeView === 'profile'
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/20'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                }`}
              >
                Profile & History
              </button>
            </div>

            {/* View Content */}
            {activeView === 'recommendations' && (
              <ProductGrid
                recommendations={pipelineData.recommendations}
                onSelectProduct={(p, rec) => setSelectedProductModal(rec ? { ...p, _recommendation: rec } : p)}
                onOpenPriceAlert={(p) => setAlertProductModal(p)}
              />
            )}

            {activeView === 'comparison' && (
              <ComparisonTable
                comparisonProducts={pipelineData.top_5_comparison}
                onSelectProduct={(p, rec) => setSelectedProductModal(rec ? { ...p, _recommendation: rec } : p)}
              />
            )}

            {activeView === 'analytics' && (
              <AnalyticsDashboard
                analytics={pipelineData.analytics}
                recommendations={pipelineData.recommendations}
                topComparison={pipelineData.top_5_comparison}
                bestForYou={pipelineData.best_for_you}
                bestValue={pipelineData.best_value}
                bestReviewed={pipelineData.best_reviewed}
                bestAlternative={pipelineData.best_alternative}
                onSelectProduct={(p, rec) => setSelectedProductModal(rec ? { ...p, _recommendation: rec } : p)}
              />
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

      {/* Price Drop Alert Modal */}
      {alertProductModal && (
        <PriceAlertModal
          product={alertProductModal}
          isOpen={Boolean(alertProductModal)}
          onClose={() => setAlertProductModal(null)}
          onAlertCreated={(res) => {
            setWelcomeToast({
              title: '🔔 Price Alert Activated!',
              message: `Tracking "${res.product_title.slice(0, 35)}..." for drops to ₹${res.target_price.toLocaleString('en-IN')}.`
            });
            setTimeout(() => setWelcomeToast(null), 5000);
          }}
        />
      )}

      {/* User Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
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
