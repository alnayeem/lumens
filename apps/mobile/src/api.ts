import Constants from 'expo-constants';

// Prefer public env at build/run time, then Expo extra, then placeholder
const PUBLIC_BASE = (process.env as any)?.EXPO_PUBLIC_API_BASE as string | undefined;
const EXTRA_BASE = (Constants.expoConfig?.extra as any)?.apiBase as string | undefined;
export const API = PUBLIC_BASE || EXTRA_BASE || 'https://YOUR_CLOUD_RUN_URL';
// Debug: verify API base being used at runtime
// Note: logs appear in Expo CLI console
console.log('API_BASE in app:', API);

async function get<T>(path: string): Promise<T> {
  const url = `${API}${path}`;
  console.log('GET', url);
  const res = await fetch(url);
  console.log('RES', res.status, url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export type Category = { slug: string; label: string };
export type VideoItem = {
  title?: string;
  channel_title?: string;
  published_at?: string;
  thumbnails?: { medium?: { url?: string }; default?: { url?: string } };
  url?: string;
  embed?: string;
  video_id?: string;
};

export async function fetchCategories(): Promise<{ items: Category[] }> {
  return get('/v1/categories');
}

export async function fetchContent(opts: { topic?: string; language?: string; limit?: number; cursor?: string | null }): Promise<{ items: VideoItem[]; nextCursor?: string | null }> {
  const params = new URLSearchParams();
  if (opts.topic) params.set('topic', opts.topic);
  params.set('language', opts.language || 'en');
  params.set('limit', String(opts.limit ?? 24));
  if (opts.cursor) params.set('cursor', opts.cursor);
  return get(`/v1/content?${params.toString()}`);
}
