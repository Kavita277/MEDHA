import numpy as np

class ExplanationBuilder:
    @staticmethod
    def build(
        current_score, previous_score,
        z_text, z_voice, z_beh,
        w_text, w_voice, w_beh,
        trajectory_info,
        case_event_info,
        future_prob,
        masks
    ):
        """
        Builds the deterministic Explanation JSON object from model outputs.
        """
        
        recent_change = current_score - previous_score
        
        text_avail = bool(masks.get('text', 1))
        voice_avail = bool(masks.get('voice', 1))
        beh_avail = bool(masks.get('behaviour', 1))
        
        obj = {
            "current_distress_score": round(float(current_score), 4),
            "previous_distress_score": round(float(previous_score), 4),
            "recent_change": round(float(recent_change), 4),
            
            "text_logit": round(float(z_text), 4) if text_avail else 0.0,
            "voice_logit": round(float(z_voice), 4) if voice_avail else 0.0,
            "behaviour_logit": round(float(z_beh), 4) if beh_avail else 0.0,
            
            "text_gate_weight": round(float(w_text), 4),
            "voice_gate_weight": round(float(w_voice), 4),
            "behaviour_gate_weight": round(float(w_beh), 4),
            
            "text_contribution": round(float(w_text * z_text), 4) if text_avail else 0.0,
            "voice_contribution": round(float(w_voice * z_voice), 4) if voice_avail else 0.0,
            "behaviour_contribution": round(float(w_beh * z_beh), 4) if beh_avail else 0.0,
            
            "trajectory": trajectory_info.get("direction", "stable"),
            "trajectory_slope": round(float(trajectory_info.get("slope", 0.0)), 4),
            "trajectory_persistence": round(float(trajectory_info.get("persistence", 0.0)), 4),
            "trajectory_volatility": round(float(trajectory_info.get("volatility", 0.0)), 4),
            
            "recent_case_event": case_event_info.get("event", "None"),
            "days_since_case_event": case_event_info.get("days_since", -1),
            
            "future_escalation_probability": round(float(future_prob), 4),
            
            "text_available": text_avail,
            "voice_available": voice_avail,
            "behaviour_available": beh_avail,
            "structured_context_available": case_event_info.get("event", "None") != "None"
        }
        
        return obj
