# DDS Target Audit

## Finding
**Classification: B. Derived synthetic reference with overlapping inputs**

## Detailed Audit
The `DDS` (Dynamic Distress Score) column in the dataset is generated using a deterministic mathematical formula rather than being an independent clinical ground truth.

A linear regression on the dataset features achieves an $R^2$ of 1.0, proving that `DDS` is perfectly predictable from other features. Further investigation using Lasso regression identified the exact non-zero coefficients that construct the `DDS` score:

- **Rolling_DDS_Mean**: 0.936175
- **DDS_Slope**: 0.732336
- **Recent_Change_Rate**: 0.363775
- **Response_Delay_Deviation**: 0.036528
- **Diary_Length**: -0.021330
- **Interaction_Frequency_7d**: -0.169627

### Feature Contributions
- **Structured Variables**: Yes. They heavily dictate the score (e.g., `Interaction_Frequency_7d`, `Response_Delay_Deviation`).
- **Text Variables**: No direct contribution.
- **Voice Variables**: No direct contribution.
- **Behaviour Variables**: Yes, via interaction frequency and response delay deviations.
- **Baseline/Deviation Variables**: Yes, heavily (e.g., `Rolling_DDS_Mean`, `DDS_Slope`).
- **Future Information**: No. Future escalation data does not enter the current DDS.
- **Latent Distress / Independent Reference**: No. `DDS` is completely derived from observable input variables without random noise that would reflect a truly independent latent state.

### Conclusion
Because `DDS` is derived from overlapping inputs (especially structured historical variables), evaluating the fusion engine against it strictly measures how well the fusion system reconstructs the synthetic generation formula, **not independent clinical validity.** 
Therefore, if structured inputs heavily dominate the fusion weights, it is an expected artifact of the dataset generation methodology, as structured variables mathematically define the target.
