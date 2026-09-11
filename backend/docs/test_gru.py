import sys, os
sys.path.insert(0, os.path.abspath("."))
import pandas as pd
import numpy as np
from backend.integrations.medha_v2 import get_v2_pipeline

pipeline = get_v2_pipeline()

rows = []
for t in range(1, 11):
    row = {'Victim_ID': 'V-LONG-01', 'Timepoint': t}
    for f in pipeline.structured_features:
        row[f] = 1.0
    for f in pipeline.text_features:
        row[f] = 0.5
    for f in pipeline.voice_features:
        row[f] = 0.5
    for f in pipeline.behaviour_features_all:
        row[f] = 2.0
    for f in pipeline.gru_features:
        row[f] = 0.1
    for f in pipeline.fusion_features:
        row[f] = 0.0
    row['Struct_Available'] = 1.0
    row['Text_Available'] = 1.0
    row['Voice_Available'] = 1.0
    row['Behav_Available'] = 1.0
    rows.append(row)

df = pd.DataFrame(rows)
res = pipeline.predict_v2(df)

for idx, r in res.iterrows():
    print(f"T{int(r['Timepoint'])}: Avail={int(r['Temporal_Available'])}, Score={r['Temporal_Risk_Score']}, Flag={r['Future_Escalation_Flag']}")
