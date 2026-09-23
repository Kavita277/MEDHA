/**
 * Voice Service
 * =============
 *
 * Client functions for interacting with the MEDHA voice backend.
 */

import { api } from './api';

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

export interface VoiceCheckInResponse {
  id: string;
  case_id: string;
  session_id?: string;
  timepoint: string;
  available: number;
  message: string;
}

// ---------------------------------------------------------------------------
// API Methods
// ---------------------------------------------------------------------------

/**
 * Uploads a recorded voice check-in to the backend.
 * Uses multipart/form-data.
 */
export async function uploadVoiceCheckin(
  audioUri: string,
  timepoint: string,
  token: string,
  sessionId?: string | null,
): Promise<VoiceCheckInResponse> {
  const formData = new FormData();

  // The backend endpoint requires 'timepoint'
  formData.append('timepoint', timepoint);

  // The backend endpoint accepts optional 'session_id'
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  // React Native fetch supports passing an object with uri, type, name in FormData
  const filename = audioUri.split('/').pop() || 'recording.m4a';
  const type = 'audio/m4a'; // Assuming m4a is the output from expo-audio high quality presets

  formData.append('audio_file', {
    uri: audioUri,
    name: filename,
    type,
  } as any);

  return api.upload<VoiceCheckInResponse>('/voice/checkin', formData, {
    token,
  });
}
