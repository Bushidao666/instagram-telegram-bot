import axios from 'axios';

// Use relative URL for API calls - Next.js will proxy them
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Profile types
export interface Profile {
  id: number;
  username: string;
  webhook_url: string;
  check_interval: number;
  download_posts: boolean;
  download_stories: boolean;
  is_active: boolean;
  last_post_timestamp?: string;
  last_story_timestamp?: string;
  created_at: string;
  updated_at: string;
}

export interface ProfileCreate {
  username: string;
  webhook_url: string;
  check_interval: number;
  download_posts: boolean;
  download_stories: boolean;
}

export interface ProfileUpdate {
  webhook_url?: string;
  check_interval?: number;
  download_posts?: boolean;
  download_stories?: boolean;
  is_active?: boolean;
}

// Log types
export interface SystemLog {
  id: number;
  level: 'info' | 'warning' | 'error';
  message: string;
  details?: string;
  profile_id?: number;
  created_at: string;
}

// Stats types
export interface Stats {
  total_profiles: number;
  active_profiles: number;
  total_posts: number;
  total_stories: number;
  total_errors: number;
  last_check?: string;
}

// API functions
export interface TestResult {
  profile: string;
  steps: Array<{
    step: string;
    status: string;
    timestamp: string;
    details?: string;
  }>;
  success: boolean;
  media_found: {
    type: string;
    media_type?: string;
    caption: string;
    timestamp: string;
    file_path?: string;
    file_size?: number;
    shortcode?: string;
    is_video?: boolean;
    download_skipped?: boolean;
    reason?: string;
  } | null;
  webhook_result: {
    success?: boolean;
    configured?: boolean;
    url: string;
    timestamp?: string;
    test_skipped?: boolean;
    reason?: string;
  } | null;
  error: string | null;
  warning?: string;
}

export const profilesApi = {
  list: () => api.get<Profile[]>('/api/profiles'),
  create: (data: ProfileCreate) => api.post<Profile>('/api/profiles', data),
  get: (id: number) => api.get<Profile>(`/api/profiles/${id}`),
  update: (id: number, data: ProfileUpdate) => api.put<Profile>(`/api/profiles/${id}`, data),
  delete: (id: number) => api.delete(`/api/profiles/${id}`),
  forceCheck: (id: number) => api.post(`/api/check/${id}`),
  testScraping: (id: number) => {
    console.log(`🧪 [TEST] Iniciando teste de scraping para perfil ID: ${id}`);
    return api.post<TestResult>(`/api/test/${id}`).then(response => {
      console.log('✅ [TEST] Resposta recebida:', response.data);
      return response;
    }).catch(error => {
      console.error('❌ [TEST] Erro no teste:', error);
      throw error;
    });
  },
};

export const logsApi = {
  list: (params?: { level?: string; profile_id?: number; limit?: number; offset?: number }) =>
    api.get<SystemLog[]>('/api/logs', { params }),
};

export const statsApi = {
  get: () => api.get<Stats>('/api/stats'),
};

// WebSocket connection for real-time logs
export const createWebSocket = (onMessage: (log: SystemLog) => void) => {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 
    (typeof window !== 'undefined' 
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws/logs`
      : 'ws://localhost:8000/ws/logs');
  
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'log') {
      onMessage(JSON.parse(data.data));
    }
  };
  
  return ws;
};

// Default export for convenience
export default api;