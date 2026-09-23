export interface JournalEntryCreate {
  content: string;
}

export interface JournalEntryUpdate {
  content: string;
}

export interface JournalEntryResponse {
  id: string;
  case_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface JournalEntryListResponse {
  entries: JournalEntryResponse[];
}
