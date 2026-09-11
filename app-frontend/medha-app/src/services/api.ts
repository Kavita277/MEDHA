/**
 * MEDHA Mobile API Client Service
 * ================================
 * Provides access to the MEDHA enterprise backend endpoints for mobile app.
 */

import { Platform } from 'react-native';

// Machine LAN IP for physical device / Expo Go access over Wi-Fi
export const API_BASE_URL = 'http://192.168.0.2:8000/api/v1';

let authToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  authToken = token;
};

export const ensureAuthenticated = async () => {
  if (!authToken) {
    try {
      const data = await authService.login('ananya.sharma@medha.org', 'PatientPass123!');
      if (data.access_token) {
        setAuthToken(data.access_token);
      }
    } catch (e) {
      console.warn('Auto-authentication fallback failed', e);
    }
  }
  return authToken;
};

const request = async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // not json
    }
    throw new Error(errorDetail);
  }

  return response.json();
};

export const authService = {
  login: async (email: string, password: string) => {
    const data = await request<{ access_token: string; token_type: string; user: any }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (data.access_token) {
      setAuthToken(data.access_token);
    }
    return data;
  },
  logout: () => {
    setAuthToken(null);
  },
  getMe: async () => {
    return request<any>('/auth/me');
  }
};

export const sessionService = {
  createSession: async () => {
    await ensureAuthenticated();
    return request<{ id: string; session_identifier: string; timepoint: number; status: string }>('/sessions', {
      method: 'POST',
    });
  },
  getSession: async (sessionId: string) => {
    await ensureAuthenticated();
    return request<any>(`/sessions/${sessionId}`);
  }
};

export const chatService = {
  sendMessage: async (sessionId: string, message: string, language?: string) => {
    await ensureAuthenticated();
    return request<{
      session_id: string;
      turn_index: number;
      user_message: string;
      assistant_response: string;
      safety_triggered: boolean;
    }>(`/chat/sessions/${sessionId}/message`, {
      method: 'POST',
      body: JSON.stringify({ message, language: language || null }),
    });
  },
  getChatHistory: async (sessionId: string) => {
    await ensureAuthenticated();
    return request<{ session_id: string; messages: Array<{ role: string; content: string }> }>(
      `/chat/sessions/${sessionId}/history`
    );
  }
};

export const checkinService = {
  startCheckin: async (sessionId?: string) => {
    await ensureAuthenticated();
    let sid = sessionId;
    if (!sid) {
      const sess = await sessionService.createSession();
      sid = sess.id;
    }
    return request<any>(`/checkins/sessions/${sid}`, { method: 'POST' });
  },
  getCheckin: async (checkinId: string) => {
    await ensureAuthenticated();
    return request<any>(`/checkins/${checkinId}`);
  },
  submitAnswer: async (checkinId: string, answer: Record<string, any>) => {
    await ensureAuthenticated();
    return request<any>(`/checkins/${checkinId}/answer`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    });
  },
  completeCheckin: async (checkinId: string) => {
    await ensureAuthenticated();
    return request<any>(`/checkins/${checkinId}/complete`, { method: 'POST' });
  },
  getTodayStatus: async () => {
    await ensureAuthenticated();
    return request<{ completed_today: boolean; active_checkin_id: string | null; status: string }>('/checkins/status/today');
  },
};

export const journalService = {
  createEntry: async (content: string) => {
    await ensureAuthenticated();
    return request<any>('/journal', {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  },
  listEntries: async () => {
    await ensureAuthenticated();
    return request<{ entries: any[] }>('/journal');
  },
};

export const voiceService = {
  uploadCheckin: async (
    audioData?: string | Blob,
    timepoint: string = 'current',
    sessionId?: string,
    customFilename?: string
  ) => {
    await ensureAuthenticated();
    const formData = new FormData();
    formData.append('timepoint', timepoint);
    if (sessionId) formData.append('session_id', sessionId);

    let blob: Blob;
    let fileName = customFilename || 'voice_checkin.wav';

    if (audioData instanceof Blob) {
      blob = audioData;
      if (!customFilename && (audioData as any).name) {
        fileName = (audioData as any).name;
      }
    } else if (typeof audioData === 'string' && audioData.length > 0 && !audioData.includes('dummy')) {
      try {
        if (!customFilename) {
          const parts = audioData.split('/');
          const lastPart = parts[parts.length - 1];
          if (lastPart && (lastPart.endsWith('.m4a') || lastPart.endsWith('.wav') || lastPart.endsWith('.mp3') || lastPart.endsWith('.aac'))) {
            fileName = lastPart;
          }
        }
        const fileRes = await fetch(audioData);
        blob = await fileRes.blob();
      } catch (err) {
        console.warn('Could not read audio uri to blob, using fallback:', err);
        blob = createSilenceWav();
      }
    } else {
      blob = createSilenceWav();
    }

    formData.append('audio_file', blob, fileName);

    const headers: Record<string, string> = {};
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(`${API_BASE_URL}/voice/checkin`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      let err = 'Voice upload failed';
      try {
        const j = await response.json();
        err = j.detail || err;
      } catch {}
      throw new Error(err);
    }
    return response.json();
  },
};

function createSilenceWav(): Blob {
  const sampleRate = 8000;
  const numSamples = 8000; // 1 second
  const buffer = new ArrayBuffer(44 + numSamples * 2);
  const view = new DataView(buffer);
  
  // RIFF identifier
  view.setUint32(0, 0x52494646, false);
  view.setUint32(4, 36 + numSamples * 2, true);
  view.setUint32(8, 0x57415645, false); // WAVE
  view.setUint32(12, 0x666d7420, false); // fmt 
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  view.setUint32(36, 0x64617461, false); // data
  view.setUint32(40, numSamples * 2, true);
  
  return new Blob([buffer], { type: 'audio/wav' });
}

export const therapistService = {
  getCases: async () => {
    return request<any[]>('/therapist/cases');
  },
  createPatient: async (data: { name: string; email: string; password: string; mobile?: string; victim_id?: string }) => {
    return request<any>('/therapist/users', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  getCaseResults: async (caseId: string) => {
    return request<any>(`/therapist/cases/${caseId}/results`);
  },
  getCaseSessions: async (caseId: string) => {
    return request<any[]>(`/therapist/cases/${caseId}/sessions`);
  },
  getCaseCheckins: async (caseId: string) => {
    return request<any[]>(`/therapist/cases/${caseId}/checkins`);
  },
  getCaseVoiceRecords: async (caseId: string) => {
    return request<any[]>(`/therapist/cases/${caseId}/voice-records`);
  },
  getCaseAlerts: async (caseId: string) => {
    return request<any[]>(`/therapist/cases/${caseId}/alerts`);
  },
  getCaseInsights: async (caseId: string) => {
    return request<any>(`/therapist/cases/${caseId}/insights`);
  },
  getCaseRecommendations: async (caseId: string) => {
    return request<any>(`/therapist/cases/${caseId}/recommendations`);
  },
  getCaseSafetyProtocol: async (caseId: string) => {
    return request<any>(`/therapist/cases/${caseId}/safety-protocol`);
  },
};

export const apiService = {
  auth: authService,
  session: sessionService,
  chat: chatService,
  checkin: checkinService,
  journal: journalService,
  voice: voiceService,
  therapist: therapistService,
};

export default apiService;
