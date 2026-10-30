const API_BASE_URL = import.meta.env.VITE_API_BASE_URL !== undefined
  ? import.meta.env.VITE_API_BASE_URL
  : '';
const API_PREFIX = API_BASE_URL ? `${API_BASE_URL}/api` : '/api';

async function getApiError(response, fallbackMessage) {
  const body = await response.json().catch(() => null);
  const detail = body?.detail;
  const message = Array.isArray(detail)
    ? detail.map((item) => item.msg || item.message).filter(Boolean).join('; ')
    : detail;
  return message || `${fallbackMessage} (HTTP ${response.status})`;
}

export async function fetchIntent(query) {
  const res = await fetch(`${API_PREFIX}/search/intent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to analyze search intent'));
  }
  return res.json();
}

export async function fetchQuestions(query, category) {
  const res = await fetch(`${API_PREFIX}/search/questions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, category })
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to generate requirement questions'));
  }
  return res.json();
}

export async function generateRecommendations(query, category, answers) {
  const res = await fetch(`${API_PREFIX}/recommendations/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, category, answers })
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to generate recommendations'));
  }
  const result = await res.json();
  if (
    !result ||
    !Array.isArray(result.recommendations) ||
    !result.recommendations.every((recommendation) => recommendation?.product)
  ) {
    throw new Error('TrustRank returned an invalid recommendation response. Please try again.');
  }

  return result;
}

export async function fetchProvidersStatus() {
  const res = await fetch(`${API_PREFIX}/providers/status`);
  if (!res.ok) {
    throw new Error('Failed to fetch provider statuses');
  }
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_PREFIX}/health`);
  return res.json();
}

export async function searchAmazonProducts(query) {
  // This router is intentionally not under /api; preserve the existing backend URL.
  const url = API_BASE_URL ? `${API_BASE_URL}/products/scrape` : '/products/scrape';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to search Amazon products'));
  }
  const result = await res.json();
  if (!result || !Array.isArray(result.products)) {
    throw new Error('TrustRank returned an invalid Amazon search response. Please try again.');
  }
  // Keep the response object intact: the backend owns the product count and
  // callers must not replace a non-empty Bright Data result with another
  // provider's empty result.
  return result;
}

export async function generateImage(prompt, size = '1024x1024') {
  const res = await fetch(`${API_PREFIX}/images/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt, size }) });
  if (!res.ok) throw new Error(await getApiError(res, 'Failed to generate image'));
  return res.json();
}

export async function analyzeImage(imageUrl) {
  const res = await fetch(`${API_PREFIX}/images/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ image_url: imageUrl }) });
  if (!res.ok) throw new Error(await getApiError(res, 'Failed to analyze image'));
  return res.json();
}

// ==============================================================================
// User Authentication & Session APIs
// ==============================================================================

export async function apiSignUp(email, password, name = null) {
  const res = await fetch(`${API_PREFIX}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name })
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Registration failed'));
  }
  return res.json();
}

export async function apiLogin(email, password) {
  const res = await fetch(`${API_PREFIX}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Login failed'));
  }
  return res.json();
}

export async function apiGetMe(token) {
  if (!token) return null;
  const res = await fetch(`${API_PREFIX}/auth/me`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  });
  if (!res.ok) {
    return null;
  }
  return res.json();
}

export async function apiLogout(token) {
  if (!token) return { message: 'Logged out' };
  try {
    const res = await fetch(`${API_PREFIX}/auth/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    return res.json();
  } catch (err) {
    console.warn('Logout request failed:', err);
    return { message: 'Logged out locally' };
  }
}

export async function fetchCouponOffers(query = '', category = '') {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  if (category) params.append('category', category);
  const url = `${API_PREFIX}/coupons/offers${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to fetch coupon offers'));
  }
  return res.json();
}

export async function fetchFeaturedDeals() {
  const res = await fetch(`${API_PREFIX}/coupons/featured`);
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to fetch featured deals'));
  }
  return res.json();
}

export async function extractProductOffers(product) {
  if (!product) return [];
  try {
    const res = await fetch(`${API_PREFIX}/coupons/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product })
    });
    if (!res.ok) return [];
    return res.json();
  } catch (err) {
    console.warn('Could not extract coupon offers:', err);
    return [];
  }
}

// ==========================================
// Customer Profile & Research History APIs
// ==========================================

function getAuthHeaders(token) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (typeof window !== 'undefined' && window.localStorage) {
    let guestId = localStorage.getItem('trustrank_guest_id');
    if (!guestId) {
      guestId = 'guest_' + Math.random().toString(36).substring(2, 12);
      localStorage.setItem('trustrank_guest_id', guestId);
    }
    headers['X-Guest-ID'] = guestId;
  }
  return headers;
}

export async function fetchProfileDashboard(token) {
  const res = await fetch(`${API_PREFIX}/history/dashboard`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to fetch customer profile dashboard'));
  }
  return res.json();
}

export async function fetchResearchHistory(token, category = 'all', limit = 50) {
  const params = new URLSearchParams();
  if (category && category !== 'all') params.append('category', category);
  if (limit) params.append('limit', limit);
  const url = `${API_PREFIX}/history${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to fetch research history'));
  }
  return res.json();
}

export async function recordResearchActivity(token, { category, title, query, metadata }) {
  try {
    const res = await fetch(`${API_PREFIX}/history/record`, {
      method: 'POST',
      headers: getAuthHeaders(token),
      body: JSON.stringify({
        category,
        title,
        query: query || null,
        metadata: metadata || {}
      })
    });
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.warn('Could not record research history:', err);
    return null;
  }
}

export async function clearResearchHistory(token, category = null) {
  const params = new URLSearchParams();
  if (category && category !== 'all') params.append('category', category);
  const url = `${API_PREFIX}/history/clear${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to clear research history'));
  }
  return res.json();
}

export async function fetchSavedProducts(token) {
  const res = await fetch(`${API_PREFIX}/history/saved`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to fetch saved products'));
  }
  return res.json();
}

export async function saveProduct(token, product) {
  const res = await fetch(`${API_PREFIX}/history/save`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      product_id: String(product.id || product.product_id),
      title: product.title,
      marketplace: product.marketplace || 'Amazon India',
      price: product.current_price ?? product.price ?? null,
      original_price: product.original_price ?? null,
      rating: product.rating ?? null,
      trust_score: product.trust_score ?? product.trustrank_score ?? null,
      image_url: product.image_url || (product.image_candidates ? product.image_candidates[0] : null),
      product_url: product.product_url || null,
      metadata: product.metadata || {}
    })
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to save product'));
  }
  return res.json();
}

export async function removeSavedProduct(token, productId) {
  const res = await fetch(`${API_PREFIX}/history/save/${encodeURIComponent(productId)}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to remove saved product'));
  }
  return res.json();
}

// ==========================================
// Price Drop Alerts APIs
// ==========================================

export async function fetchPriceAlerts(token) {
  const res = await fetch(`${API_PREFIX}/alerts`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to fetch price alerts'));
  }
  return res.json();
}

export async function createPriceAlert(token, payload) {
  const res = await fetch(`${API_PREFIX}/alerts`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to create price alert'));
  }
  return res.json();
}

export async function updateAlertStatus(token, alertId, status) {
  const res = await fetch(`${API_PREFIX}/alerts/${encodeURIComponent(alertId)}/status`, {
    method: 'PUT',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ status })
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to update alert status'));
  }
  return res.json();
}

export async function deletePriceAlert(token, alertId) {
  const res = await fetch(`${API_PREFIX}/alerts/${encodeURIComponent(alertId)}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to delete price alert'));
  }
  return res.json();
}

export async function checkPriceAlertsNow(token) {
  const res = await fetch(`${API_PREFIX}/alerts/check`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error(await getApiError(res, 'Failed to run price check'));
  }
  return res.json();
}
