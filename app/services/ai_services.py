import random

class BaseAIService:
    def predict(self, data: dict):
        # Mock logic
        return {
            "risk_score": round(random.uniform(0.1, 0.9), 2),
            "confidence": round(random.uniform(0.7, 0.99), 2),
            "embedding": [round(random.random(), 4) for _ in range(5)]
        }

class TextService(BaseAIService):
    pass

class VoiceService(BaseAIService):
    pass

class BehaviourService(BaseAIService):
    pass

class StructuredService(BaseAIService):
    pass

class TemporalService(BaseAIService):
    pass
