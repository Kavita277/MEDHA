class FallbackExplainer:
    @staticmethod
    def generate(obj):
        """
        Generates a deterministic safe fallback explanation.
        """
        curr = obj["current_distress_score"]
        prev = obj["previous_distress_score"]
        
        # Distress assessment
        if curr > 0.7:
            assessment = "Current distress is highly elevated"
        elif curr > 0.4:
            assessment = "Current distress is moderately elevated"
        else:
            assessment = "Current distress remains low/stable"
            
        if curr > prev + 0.1:
            assessment += " compared with the previous observation."
        elif curr < prev - 0.1:
            assessment += " and has decreased since the previous observation."
        else:
            assessment += " and remains stable."
            
        # Trajectory
        traj = f"The recent trajectory shows a {obj['trajectory']} pattern."
        
        # Missing modalities
        missing = []
        if not obj["text_available"]: missing.append("Text")
        if not obj["voice_available"]: missing.append("Voice")
        if not obj["behaviour_available"]: missing.append("Behaviour")
        
        if missing:
            mod_text = f"Some data ({', '.join(missing)}) was unavailable for this observation, so the assessment relies on the available modalities."
        else:
            mod_text = "All modality data was available."
            
        # Context
        if obj["structured_context_available"]:
            ctx_text = f"A recent case event ({obj['recent_case_event']}) is recorded as contextual information."
        else:
            ctx_text = "No recent case events are recorded in the context window."
            
        # Future
        fut = obj["future_escalation_probability"]
        if fut > 0.5:
            fut_text = "The model estimates an increased likelihood of distress escalation over the next 7 days."
        else:
            fut_text = "The model estimates a low likelihood of distress escalation over the next 7 days."
            
        parts = [
            f"Current assessment: {assessment}",
            f"Trajectory: {traj}",
            f"Case context: {ctx_text}",
            f"Future outlook: {fut_text}",
            f"Limitations: {mod_text}"
        ]
        
        return "\n".join(parts)
