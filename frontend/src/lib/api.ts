const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAPI<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { next: { revalidate: 30 } });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  userops: (page = 1) => fetchAPI(`/api/userops?page=${page}`),
  stats: () => fetchAPI('/api/stats'),
  paymasters: () => fetchAPI('/api/paymasters'),
  smartAccounts: () => fetchAPI('/api/smart-accounts'),
  health: () => fetchAPI('/health'),
};
