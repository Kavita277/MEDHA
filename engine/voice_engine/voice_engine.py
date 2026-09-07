import os
import torch
import librosa
import numpy as np
from transformers import Wav2Vec2Model, Wav2Vec2Processor

class VoiceEngine:
    def __init__(self):
        print("Loading Wav2Vec2 Base Model (facebook/wav2vec2-base)...")
        # Load the model and processor from HuggingFace
        # facebook/wav2vec2-base outputs 768-dim embeddings
        self.processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
        self.model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base")
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        print(f"Wav2Vec2 loaded successfully on {self.device}.")

    def analyze(self, audio_path):
        """
        Extracts deep speech embeddings from the given 16kHz audio file.
        Returns a mean-pooled 768-dimensional numpy array.
        """
        # Load audio (Wav2Vec2 requires 16000Hz)
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        
        # Process input for the model
        inputs = self.processor(y, sampling_rate=sr, return_tensors="pt", padding=True)
        
        # Move inputs to device
        input_values = inputs.input_values.to(self.device)
        
        # Forward pass through Wav2Vec2
        with torch.no_grad():
            outputs = self.model(input_values)
        
        # outputs.last_hidden_state shape: (batch_size, sequence_length, hidden_size)
        # For facebook/wav2vec2-base, hidden_size is 768.
        # We mean-pool across the sequence_length dimension to get a single 768-dim vector per audio file.
        last_hidden_state = outputs.last_hidden_state # [1, seq_len, 768]
        pooled_embedding = torch.mean(last_hidden_state, dim=1).squeeze(0) # [768]
        
        # Move back to CPU and convert to numpy
        embedding_np = pooled_embedding.cpu().numpy()
        
        return {
            "wav2vec2_embedding": embedding_np
        }