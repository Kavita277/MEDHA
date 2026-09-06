import os
import json
from .explanation_builder import ExplanationBuilder
from .explanation_validator import ExplanationValidator
from .fallback_explainer import FallbackExplainer

class LLMExplainer:
    def __init__(self, model_path="Models/qwen2.5-0.5b-instruct"):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.load_error = None
        
        self._try_load()
        
    def _try_load(self):
        if not os.path.exists(self.model_path):
            self.load_error = f"Model weights not found at {self.model_path}. Please download Qwen2.5-0.5B-Instruct to this directory."
            return
            
        try:
            # We attempt to import transformers and bitsandbytes/awq for 4-bit
            import transformers
            import torch
            
            try:
                import bitsandbytes
                has_bnb = True
            except ImportError:
                has_bnb = False
                
            if not has_bnb:
                self.load_error = "bitsandbytes is not installed. 4-bit quantization on CPU/Windows requires a compatible runtime (e.g., llama.cpp or GGUF). Please install the necessary quantization libraries."
                return
                
            # Note: actual loading code would go here
            self.is_loaded = True
        except ImportError as e:
            self.load_error = f"Missing dependencies: {e}"
            
    def generate_explanation(self, explanation_obj):
        """
        Attempts to generate an explanation using Qwen2.5-0.5B-Instruct.
        Falls back to deterministic template if model is unavailable or validation fails.
        """
        if not self.is_loaded:
            print(f"LLM Explainer blocked: {self.load_error}")
            return FallbackExplainer.generate(explanation_obj)
            
        # The prompt string
        prompt = (
            "You are an explanation generator for the MEDHA system.\n"
            "Use ONLY the supplied evidence. Do not calculate new scores. Do not change any supplied score. "
            "Do not invent observations. Do not infer causality. Do not diagnose. "
            "Do not infer suicidality or immediate danger. Do not treat missing data as normal.\n"
            "Clearly distinguish current distress from future escalation.\n"
            "Describe structured case events as context, not proof of causation.\n"
            f"Evidence: {json.dumps(explanation_obj, indent=2)}\n"
            "Provide a short explanation covering Current assessment, Main signals, Trajectory, Case context, and Future outlook."
        )
        
        # In a real environment, self.model.generate() goes here
        generated_text = "Mock generated text from Qwen"
        
        # Validation
        is_valid, reason = ExplanationValidator.validate(generated_text, explanation_obj)
        
        if not is_valid:
            print(f"LLM Explanation rejected by Validator: {reason}")
            return FallbackExplainer.generate(explanation_obj)
            
        return generated_text
