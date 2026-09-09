"""
Conversation Summary Engine
===========================

Implements deterministic summary updates based on LLM proposals.
Separates conversational memory from predictive ML boundaries.
"""

import logging
import json
from typing import Any, Dict

from chatbot.interfaces import SummaryEngineProtocol, LLMProviderProtocol
from chatbot.state.medha_state import MedhaState
from chatbot.summary.summary_schema import SummaryItem

logger = logging.getLogger(__name__)


class ConversationSummaryEngine(SummaryEngineProtocol):
    """
    Manages conversational memory. Asks LLM for a structured JSON summary 
    of the new turn, then deterministically validates and merges it.
    """

    MAX_ITEMS_PER_CATEGORY = 10

    def update_summary(
        self, 
        state: MedhaState, 
        llm_provider: LLMProviderProtocol,
        **kwargs: Any
    ) -> None:
        """
        Updates the summary with information from the latest turn.
        """
        if not state.current_user_message:
            return

        # 1. Ask LLM for a proposed update
        # We only pass the latest turn and the current summary to keep context bounded
        # We also pass recent candidate observations if any were extracted this turn
        recent_obs = [
            obs.to_dict() for obs in state.candidate_observations 
            if obs.turn_index == len(state.conversation_history) // 2
        ]

        prompt = self._build_summary_prompt(state, recent_obs)
        
        response = llm_provider.generate_response(prompt, state)
        if not response.text:
            logger.warning("Summary generation failed or was empty.")
            return

        # 2. Parse LLM JSON
        try:
            update_data = self._parse_json_from_llm(response.text)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse summary update JSON: {e}")
            return

        # 3. Deterministically merge updates
        self._merge_updates(state, update_data, len(state.conversation_history))

    def _build_summary_prompt(self, state: MedhaState, recent_obs: list) -> str:
        summary_json = state.conversation_summary.to_json() if hasattr(state.conversation_summary, "to_json") else json.dumps(state.conversation_summary.to_dict())
        
        return (
            "You are a summarization engine for MEDHA.\n"
            "Your task is to identify NEW important facts, concerns, or events from the latest user message.\n\n"
            f"Latest User Message: \"{state.current_user_message}\"\n"
            f"Recent Qualitative Observations: {json.dumps(recent_obs)}\n\n"
            f"Current Summary State: {summary_json}\n\n"
            "Return ONLY a JSON object containing the updates. Use the exact keys: important_facts, current_concerns, recent_events, support_context, preferences, ongoing_topics, unresolved_topics, important_observations.\n"
            "Each key should map to a list of OBJECTS representing the new content.\n"
            "Object format: {\"content\": \"the new information\", \"supersedes_content\": \"the EXACT content string of the old item being updated, or null if this is entirely new\"}\n"
            "ONLY use 'supersedes_content' if there is clear, explicit evidence of an update (e.g., 'actually', 'but now', 'no longer'). Do NOT infer contradictions merely because statements are different.\n"
            "Do NOT include items that are already in the summary without meaningful changes.\n"
            "Do NOT make up clinical diagnoses.\n"
            "Ensure valid JSON."
        )

    def _parse_json_from_llm(self, content: str) -> Dict[str, list]:
        # Strip markdown fences if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        data = json.loads(content.strip())
        if not isinstance(data, dict):
            raise ValueError("Parsed JSON is not a dictionary.")
        return data

    def _merge_updates(self, state: MedhaState, update_data: Dict[str, list], turn_index: int) -> None:
        summary = state.conversation_summary
        
        categories = [
            "important_facts", "current_concerns", "recent_events", 
            "support_context", "preferences", "ongoing_topics", 
            "unresolved_topics", "important_observations"
        ]

        for category in categories:
            new_items = update_data.get(category, [])
            if not isinstance(new_items, list):
                continue
                
            current_list = getattr(summary, category)
            
            for item_obj in new_items:
                # Handle old string format if LLM ignores instructions
                if isinstance(item_obj, str):
                    item_obj = {"content": item_obj, "supersedes_content": None}
                    
                if not isinstance(item_obj, dict) or not item_obj.get("content"):
                    continue
                    
                content = str(item_obj["content"]).strip()
                if not content:
                    continue
                    
                supersedes_content = item_obj.get("supersedes_content")
                if isinstance(supersedes_content, str):
                    supersedes_content = supersedes_content.strip()

                status = "active"
                
                # Deduplication: Exact match
                if any(item.content == content for item in current_list):
                    continue
                    
                # Handle explicit supersession
                if supersedes_content:
                    matched_old_item = next((item for item in current_list if item.content == supersedes_content), None)
                    if matched_old_item:
                        matched_old_item.status = "superseded"
                    else:
                        # If supersedes_content is provided but not found, this is an ambiguous update
                        status = "unresolved"
                
                new_item = SummaryItem(
                    content=content,
                    source="user_statement",
                    extracted_by="llm_extraction",
                    turn_index=turn_index,
                    evidence=state.current_user_message,
                    status=status
                )
                
                current_list.append(new_item)
                
            # Truncate to MAX_ITEMS_PER_CATEGORY to prevent unbounded growth
            if len(current_list) > self.MAX_ITEMS_PER_CATEGORY:
                # Keep the newest N items
                setattr(summary, category, current_list[-self.MAX_ITEMS_PER_CATEGORY:])
                
        summary.updated_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
