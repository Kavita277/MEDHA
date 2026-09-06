Write-Host "Extracting Voice Features..."
python tools\extract_voice_features.py

Write-Host "Training Voice GRU..."
python tools\train_voice_gru.py

Write-Host "Synchronizing Datasets..."
python tools\synchronize_multimodal_dataset.py

Write-Host "Training Gated Late Fusion..."
python tools\train_gated_fusion.py

Write-Host "All processes complete!"
