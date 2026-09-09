import sys
import os
import pandas as pd

STRUCTURED_ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../engine/Structured_risk_enigne"))
if STRUCTURED_ENGINE_DIR not in sys.path:
    sys.path.insert(0, STRUCTURED_ENGINE_DIR)

class StructuredAdapter:
    def __init__(self):
        self.engine = None
        self.error = None
        try:
            from inference import structured_engine_api
            self.engine = structured_engine_api
        except Exception as e:
            self.error = str(e)
            print(f"StructuredAdapter failed to load: {e}")

    def predict(self, data_dict: dict):
        if not self.engine:
            raise RuntimeError(f"Structured Engine is not available due to initialization error: {self.error}")
            
        # Ensure required features exist with defaults
        required_numerical = ['Mood', 'Stress', 'Sleep', 'Functioning', 'Safety', 
                              'Social_Support_Checkin', 'Self_Reported_Wellbeing', 
                              'Upcoming_Hearing', 'Hearing_Completed', 'Compensation_Delay', 
                              'Relocation_Stress', 'Rehabilitation_Issue', 'Protection_Event', 
                              'Social_Support', 'Therapist_Engagement', 'Access_To_Services', 
                              'Stable_Housing', 'Other_Protective_Factors', 'Recent_Episode', 
                              'Family_Reported_Episode', 'DDS', 'Previous_DDS', 'Baseline_DDS',
                              'DDS_Deviation_From_Baseline', 'Engagement_Score', 'Engagement_Deviation',
                              'Response_Delay_Hours', 'Response_Delay_Deviation', 'Missed_Checkin',
                              'Interaction_Frequency_7d', 'Session_Duration_Minutes', 'Threat_Event',
                              'Investigation_Delay', 'Family_Support', 'Baseline_Response_Delay',
                              'Baseline_Engagement', 'Delta_DDS']
                              
        for num_feat in required_numerical:
            if num_feat not in data_dict:
                # Map old names from the UI to new names if needed
                mapping = {
                    "Mood": "Mood_Score",
                    "Stress": "Stress_Level",
                    "Sleep": "Sleep_Quality",
                    "Functioning": "Functioning_Score",
                    "Safety": "Safety_Score",
                    "Self_Reported_Wellbeing": "Wellbeing_Index"
                }
                if num_feat in mapping and mapping[num_feat] in data_dict:
                    data_dict[num_feat] = data_dict[mapping[num_feat]]
                else:
                    data_dict[num_feat] = 0.0

        if 'Episode_Severity' not in data_dict:
            data_dict['Episode_Severity'] = 'None' # Or whatever episode_mapping expects
        if 'Case_Type' not in data_dict:
            data_dict['Case_Type'] = 'murder_grievous_hurt'
        if 'Case_Stage' not in data_dict:
            data_dict['Case_Stage'] = 'Investigation'
            
        df = pd.DataFrame([data_dict])
        res = self.engine(df)
        return res[0]
