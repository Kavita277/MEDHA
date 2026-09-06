import time
from .llm_explainer import LLMExplainer
from .explanation_schema import ExplanationSchema
from .explanation_validator import ExplanationValidator

def run_mobile_benchmark():
    print("--- MOBILE PERFORMANCE TEST ---")
    
    start_load = time.time()
    explainer = LLMExplainer()
    load_time = time.time() - start_load
    
    print(f"Model Load Time: {load_time:.2f}s")
    print(f"Quantization: 4-bit (via fallback simulated or actual bitsandbytes)")
    
    if not explainer.is_loaded:
        print("Note: Running on development-machine benchmark using fallback explainer due to missing weights/stack.")
        
    sample_obj = {
        "current_distress_score": 0.65,
        "previous_distress_score": 0.40,
        "recent_change": 0.25,
        "text_logit": 1.2,
        "voice_logit": 0.8,
        "behaviour_logit": 1.5,
        "text_gate_weight": 0.3,
        "voice_gate_weight": 0.2,
        "behaviour_gate_weight": 0.5,
        "text_contribution": 0.36,
        "voice_contribution": 0.16,
        "behaviour_contribution": 0.75,
        "trajectory": "increasing",
        "trajectory_slope": 0.05,
        "trajectory_persistence": 0.8,
        "trajectory_volatility": 0.1,
        "recent_case_event": "None",
        "days_since_case_event": -1,
        "future_escalation_probability": 0.72,
        "text_available": True,
        "voice_available": True,
        "behaviour_available": True,
        "structured_context_available": False
    }
    
    start_gen = time.time()
    result = explainer.generate_explanation(sample_obj)
    gen_time = time.time() - start_gen
    
    print(f"Generation Latency: {gen_time:.2f}s")
    print(f"Explanation:\n{result}")

if __name__ == "__main__":
    run_mobile_benchmark()
