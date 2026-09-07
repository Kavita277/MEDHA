# MEDHA GPU Handoff Prompt

**To the Antigravity Agent:**
If you are reading this, you have been instantiated on a new machine equipped with an NVIDIA RTX GPU. The previous agent (on a CPU machine) already wrote all the code required to upgrade the `Voice Modality` from naive heuristics to deep contextual **Wav2Vec2** embeddings, but stopped execution due to a 14-hour bottleneck.

Your task is to simply **execute the pipeline** using the raw speed of your GPU. 

### What has already been done:
1. `engine/voice_engine/voice_engine.py` was rewritten to use `facebook/wav2vec2-base` via HuggingFace `transformers`. (It correctly detects and uses `cuda` if available).
2. `tools/extract_voice_features.py` was modified to unpack 768-dim embeddings into an optimized `.npz` tensor.
3. `tools/train_voice_gru.py` and `tools/synchronize_multimodal_dataset.py` were upgraded to ingest `input_size=768` instead of 13.

### Your Exact Execution Checklist:
Please run the following commands sequentially in the terminal. **Do not modify the scripts**, they are already perfectly configured.

1. **Extract Voice Features:**
   ```bash
   python tools/extract_voice_features.py
   ```
   *(This will extract Wav2Vec2 embeddings for all 4,500 audio files and save them to `datasets/MEDHA_Longitudinal_Synthetic_1000x30/voice_engine_outputs_150x30.npz`. On your RTX GPU, this should be extremely fast).*

2. **Train Voice GRU:**
   ```bash
   python tools/train_voice_gru.py
   ```

3. **Synchronize Multimodal Dataset:**
   ```bash
   python tools/synchronize_multimodal_dataset.py
   ```

4. **Train Gated Late Fusion Model:**
   ```bash
   python tools/train_gated_fusion.py
   ```

5. **Evaluate All Models:**
   ```bash
   python tools/evaluate_all_models.py
   ```

Once you have executed all of the above, please provide the user with the final F1 scores, Precision, Recall, and Accuracy metrics (specifically highlighting the massive improvement to the Voice GRU and the Gated Fusion model's performance).
