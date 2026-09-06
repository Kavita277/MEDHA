import json

class ExplanationSchema:
    def __init__(self):
        self.fields = [
            "current_distress_score",
            "previous_distress_score",
            "recent_change",
            "text_logit",
            "voice_logit",
            "behaviour_logit",
            "text_gate_weight",
            "voice_gate_weight",
            "behaviour_gate_weight",
            "text_contribution",
            "voice_contribution",
            "behaviour_contribution",
            "trajectory",
            "trajectory_slope",
            "trajectory_persistence",
            "trajectory_volatility",
            "recent_case_event",
            "days_since_case_event",
            "future_escalation_probability",
            "text_available",
            "voice_available",
            "behaviour_available",
            "structured_context_available"
        ]

    def validate(self, obj):
        for field in self.fields:
            if field not in obj:
                raise ValueError(f"Missing required field: {field}")
        
        # Validations for values
        assert obj["text_gate_weight"] >= 0
        assert obj["voice_gate_weight"] >= 0
        assert obj["behaviour_gate_weight"] >= 0
        
        total_weight = obj["text_gate_weight"] + obj["voice_gate_weight"] + obj["behaviour_gate_weight"]
        assert abs(total_weight - 1.0) < 1e-4, f"Gate weights sum to {total_weight}, must be 1.0"
        
        return True
