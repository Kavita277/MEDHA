import { api } from './api';

export interface CheckinStatusResponse {
  completed_today: boolean;
  active_checkin_id: string | null;
  status: string;
}

export const checkinService = {
  startCheckin: async (sessionId: string, token?: string | null) => {
    return api.post<any>(`/checkins/sessions/${sessionId}`, undefined, { token: token ?? undefined });
  },

  getTodayStatus: async (token?: string | null) => {
    return api.get<CheckinStatusResponse>('/checkins/status/today', { token: token ?? undefined });
  },

  submitAnswer: async (checkinId: string, answer: any, token?: string | null) => {
    return api.post<any>(`/checkins/${checkinId}/answer`, { answer }, { token: token ?? undefined });
  },
};
