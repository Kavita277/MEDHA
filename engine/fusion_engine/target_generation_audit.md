# Target Generation Audit

## Findings
1. **Target**: `Future_Escalation_Label`
2. **Missing Data**: The dataset contains 7000 rows where the target is NaN. These represent the final 7 days of the 30-day window for each victim, as the target looks 7 days into the future.
3. **Correlations**: 
Future_Escalation_Label        1.000000
DDS                            0.309887
Recent_Max_DDS                 0.304095
DDS_Deviation_From_Baseline    0.302068
Speech_Rate_Deviation          0.299094
Rolling_DDS_Mean               0.299085
Previous_DDS                   0.291486
Urgency                        0.290392
Energy_Deviation               0.290139
Recent_Min_DDS                 0.280779
4. **Leakage**: There is no 1.0 perfect correlation. The target is derived by looking forward 7 days, meaning rows at T=24-30 naturally have NaN targets. The highest correlations are structural threat variables.
5. **DDS Involvement**: DDS is NOT involved in the target construction.
