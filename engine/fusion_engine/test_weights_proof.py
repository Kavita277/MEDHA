import sys
import os

# Add parent directory to path to allow imports
engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from fusion_engine.fusion import compute_fusion, FUSION_WEIGHTS
import fusion_engine.fusion as fusion_mod
from fusion_engine.evaluate_fusion import BASELINE_WEIGHTS
from fusion_engine.schemas import FusionInput, ModalitySignal

def prove_multimodal_weights():
    print("=====================================================")
    print("PROOF OF MULTI-MODAL WEIGHTING")
    print("=====================================================")
    
    # 1. Enforce the baseline weights just like the real script does
    fusion_mod.FUSION_WEIGHTS = BASELINE_WEIGHTS
    print(f"1. Current active global weights:\n   {fusion_mod.FUSION_WEIGHTS}")
    
    # 2. Create a mock victim with different risk scores across modalities
    # We set Structured to 0.10 (low risk) but Text to 0.90 (high distress)
    mock_input = FusionInput(
        patient_id="Victim_X",
        timestamp="2023-10-01",
        text=ModalitySignal(available=True, risk=0.90),
        voice=ModalitySignal(available=True, risk=0.20),
        behaviour=ModalitySignal(available=True, risk=0.10),
        structured=ModalitySignal(available=True, risk=0.10),
        temporal=ModalitySignal(available=True, risk=0.30)
    )
    
    print("\n2. Simulating a victim observation...")
    print(f"   - Structured Risk: {mock_input.structured.risk:.2f}")
    print(f"   - Text Distress Risk: {mock_input.text.risk:.2f}")
    print(f"   - Voice Risk: {mock_input.voice.risk:.2f}")
    print(f"   - Behaviour Risk: {mock_input.behaviour.risk:.2f}")
    print(f"   - Temporal Risk: {mock_input.temporal.risk:.2f}")
    
    # 3. Compute Fusion
    output = compute_fusion(mock_input)
    
    print("\n3. Final Fusion Computation Results:")
    print("   Effective Weights Applied by the Engine:")
    for modality, weight in output.effective_weights.items():
        print(f"     - {modality.capitalize()}: {weight * 100:.1f}%")
        
    print(f"\n   Final Fused Risk: {output.fused_risk:.4f}")
    print(f"   Dynamic Distress Score (DDS): {output.dds}")
    
    # 4. Prove that it didn't collapse
    structured_only_result = mock_input.structured.risk
    if output.fused_risk == structured_only_result:
        print("\n[FAILED] The engine collapsed to 100% structured data.")
    else:
        print(f"\n[PASSED] The engine successfully blended all modalities! ")
        print(f"         If it was 100% structured, the risk would be {structured_only_result:.4f}.")
        print(f"         Instead, because Text Risk was high, it pushed the final risk up to {output.fused_risk:.4f}.")
    print("=====================================================")

if __name__ == "__main__":
    prove_multimodal_weights()
