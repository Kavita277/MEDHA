import { api } from './api';
import {
  JournalEntryCreate,
  JournalEntryUpdate,
  JournalEntryResponse,
  JournalEntryListResponse,
} from '../types/journal';

export const journalService = {
  listEntries: async (token: string): Promise<JournalEntryListResponse> => {
    return api.get<JournalEntryListResponse>('/journal', { token });
  },

  getEntry: async (token: string, id: string): Promise<JournalEntryResponse> => {
    return api.get<JournalEntryResponse>(`/journal/${id}`, { token });
  },

  createEntry: async (
    token: string,
    data: JournalEntryCreate
  ): Promise<JournalEntryResponse> => {
    return api.post<JournalEntryResponse>('/journal', data, { token });
  },

  updateEntry: async (
    token: string,
    id: string,
    data: JournalEntryUpdate
  ): Promise<JournalEntryResponse> => {
    return api.patch<JournalEntryResponse>(`/journal/${id}`, data, { token });
  },
};
