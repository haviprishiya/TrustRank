const API_BASE_URL = import.meta.env?.VITE_API_URL || '/api';

async function getApiError(response, fallbackMessage) {
  const body = await response.json().catch(() => null);
  const detail = body?.detail;
  const message = Array.isArray(detail)
    ? detail.map((item) => item.msg || item.message).filter(Boolean).join('; ')
    : detail;
  return message || `${fallbackMessage} (HTTP ${response.status})`;
}

export async function fetchIntent(query) {
  const res = await fetch(`${API_BASE_URL}/search/intent`, {
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
  const res = await fetch(`${API_BASE_URL}/search/questions`, {
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
  const res = await fetch(`${API_BASE_URL}/recommendations/generate`, {
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
  const res = await fetch(`${API_BASE_URL}/providers/status`);
  if (!res.ok) {
    throw new Error('Failed to fetch provider statuses');
  }
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE_URL}/health`);
  return res.json();
}
