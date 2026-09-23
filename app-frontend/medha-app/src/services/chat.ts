/**
 * Chat Service
 * ============
 *
 * Client functions for interacting with the MEDHA chatbot backend.
 */

import { api } from './api';

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

export interface ChatMessageResponse {
  id: string;
  chat_session_id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM' | string;
  content: string;
  timestamp: string;
}

export interface ChatTurnResult {
  session_id: string;
  turn_index: number;
  user_message: string;
  assistant_response: string;
  timestamp: string;
  safety_triggered: boolean;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: ChatMessageResponse[];
}

// ---------------------------------------------------------------------------
// API Methods
// ---------------------------------------------------------------------------

/**
 * Sends a message to the MEDHA chatbot.
 */
export async function sendMessage(
  sessionId: string,
  message: string,
  token: string,
): Promise<ChatTurnResult> {
  return api.post<ChatTurnResult>(
    `/chat/sessions/${sessionId}/message`,
    { message },
    { token },
  );
}

/**
 * Retrieves the full chat history for a session.
 */
export async function getChatHistory(
  sessionId: string,
  token: string,
): Promise<ChatHistoryResponse> {
  return api.get<ChatHistoryResponse>(`/chat/sessions/${sessionId}/history`, {
    token,
  });
}
