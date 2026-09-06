class ExplanationValidator:
    @staticmethod
    def validate(explanation_text, obj):
        """
        Validates the generated explanation against the deterministic Explanation Object.
        """
        text = explanation_text.lower()
        
        # 1. Modality availability consistency
        if not obj["voice_available"]:
            if "voice was normal" in text or "voice signals were normal" in text or "voice is normal" in text:
                return False, "Failed: Described missing voice as normal"
        
        if not obj["text_available"]:
            if "text was normal" in text or "text signals were normal" in text:
                return False, "Failed: Described missing text as normal"
                
        # 2. Causality and Case Events
        # "caused", "because of", "due to" related to court hearing
        if obj["structured_context_available"]:
            causal_phrases = ["caused by the court", "due to the hearing", "because of the hearing", "caused severe distress"]
            for phrase in causal_phrases:
                if phrase in text:
                    return False, "Failed: Unsupported causal claim regarding case event"
                    
        # 3. Diagnosis and safety inference
        safety_phrases = ["suicide", "self-harm", "imminent danger", "emergency", "diagnosis", "diagnosed with"]
        for phrase in safety_phrases:
            if phrase in text:
                return False, "Failed: Generation contains safety/diagnostic language"
                
        # 4. Current vs Future distress
        if "currently highly distressed because" in text and "future" in text:
             return False, "Failed: Confusing future escalation with current distress"
             
        return True, "Valid"
