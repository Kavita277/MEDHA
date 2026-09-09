import sys
import os
import torch
import warnings

TEXT_ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../engine/text engine"))
if TEXT_ENGINE_DIR not in sys.path:
    sys.path.insert(0, TEXT_ENGINE_DIR)

_original_torch_load = torch.load

def robust_torch_load(*args, **kwargs):
    # Add weights_only=False to support legacy models/full models safely if needed,
    # though it might be insecure if it's untrusted, but we trust the repo.
    if 'weights_only' in kwargs:
        kwargs['weights_only'] = False
        
    checkpoint = _original_torch_load(*args, **kwargs)
    
    if isinstance(checkpoint, torch.nn.Module):
        return checkpoint.state_dict()
    
    if isinstance(checkpoint, dict):
        if 'state_dict' in checkpoint:
            return checkpoint['state_dict']
        if 'model_state_dict' in checkpoint:
            return checkpoint['model_state_dict']
            
    return checkpoint

class TextAdapter:
    def __init__(self):
        self.engine = None
        self.error = None
        
        torch.load = robust_torch_load
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import medha_text_engine
            self.engine = medha_text_engine
        except FileNotFoundError as e:
            self.error = f"Missing file: {e}"
        except RuntimeError as e:
            self.error = f"Runtime error (torch mismatch or invalid state): {e}"
        except Exception as e:
            self.error = f"Initialization error: {e}"
        finally:
            torch.load = _original_torch_load

    def predict(self, text: str):
        if not self.engine:
            raise RuntimeError(f"Text Engine is not available: {self.error}")
        
        # The wrapper expects metadata as well, though only text is strictly required.
        return self.engine.medha_text_engine({"text": text})
