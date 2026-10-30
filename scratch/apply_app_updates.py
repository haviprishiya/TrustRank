import os

app_path = r"c:\Users\haviprishiya\Downloads\update new\update\update\frontend\src\App.jsx"
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
old_import = "import CouponsOffersDashboard from './components/CouponsOffersDashboard';"
new_import = """import CouponsOffersDashboard from './components/CouponsOffersDashboard';
import UserProfileDashboard from './components/UserProfileDashboard';"""
assert old_import in content, "old_import not found"
content = content.replace(old_import, new_import, 1)

old_api_import = "import { fetchIntent, fetchQuestions, generateRecommendations, fetchProvidersStatus, generateImage, analyzeImage, apiGetMe, apiLogout } from './services/api';"
new_api_import = "import { fetchIntent, fetchQuestions, generateRecommendations, fetchProvidersStatus, generateImage, analyzeImage, apiGetMe, apiLogout, recordResearchActivity } from './services/api';"
assert old_api_import in content, "old_api_import not found"
content = content.replace(old_api_import, new_api_import, 1)

# 2. activeView profile check
old_active_view = """      if (params.get('view') === 'coupons' || window.location.hash === '#coupons') {"""
new_active_view = """      if (params.get('view') === 'profile' || window.location.hash === '#profile') {
        return 'profile';
      }
      if (params.get('view') === 'coupons' || window.location.hash === '#coupons') {"""
assert old_active_view in content, "old_active_view not found"
content = content.replace(old_active_view, new_active_view, 1)

# 3. activeView === 'profile' block
old_coupons_block = "  if (activeView === 'coupons') {"
new_profile_block = """  if (activeView === 'profile') {
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
        />
        {selectedProductModal && (
          <ProductDetailsModal
            product={selectedProductModal}
            onClose={() => setSelectedProductModal(null)}
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

  if (activeView === 'coupons') {"""
assert old_coupons_block in content, "old_coupons_block not found"
content = content.replace(old_coupons_block, new_profile_block, 1)

# 4. ReviewAnalysisDashboard profile navigation
old_review_profile = "onNavigateProfile={() => setIsAuthModalOpen(true)}"
new_review_profile = "onNavigateProfile={() => setActiveView('profile')}"
assert old_review_profile in content, "old_review_profile not found"
content = content.replace(old_review_profile, new_review_profile, 1)

# 5. Record search activity in handleSearch
old_search_fn = """      const detectedIntent = await fetchIntent(searchQuery);
      setIntent(detectedIntent);"""
new_search_fn = """      const detectedIntent = await fetchIntent(searchQuery);
      setIntent(detectedIntent);
      recordResearchActivity(authToken, {
        category: 'search',
        title: `Searched for "${searchQuery}"`,
        query: searchQuery,
        metadata: { category: detectedIntent.detected_category }
      });"""
assert old_search_fn in content, "old_search_fn not found"
content = content.replace(old_search_fn, new_search_fn, 1)

# 6. Record recommendation & comparison in handleGenerateRecommendations
old_recs_fn = """      const result = await generateRecommendations(query, intent?.detected_category, answers);
      setPipelineData(result);"""
new_recs_fn = """      const result = await generateRecommendations(query, intent?.detected_category, answers);
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
      }"""
assert old_recs_fn in content, "old_recs_fn not found"
content = content.replace(old_recs_fn, new_recs_fn, 1)

# 7. Sub-navigation tabs in results view
old_tabs = """              <button
                onClick={() => setActiveView('coupons')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                  activeView === 'coupons'
                    ? 'bg-amber-600 text-white shadow-sm shadow-amber-600/20'
                    : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
                }`}
              >
                Coupons & Offers
              </button>"""
new_tabs = """              <button
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
              </button>"""
assert old_tabs in content, "old_tabs not found"
content = content.replace(old_tabs, new_tabs, 1)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("App.jsx successfully updated!")
