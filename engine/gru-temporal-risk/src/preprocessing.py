from pathlib import Path

import numpy as np
import pandas as pd


IDENTIFIER_COLUMNS = {"Victim_ID", "Timepoint", "Future_Escalation_Label"}


def load_data(file_path, sheet_name="Longitudinal_Data"):
	data = pd.read_excel(file_path, sheet_name=sheet_name)
	required_columns = {"Victim_ID", "Timepoint", "Future_Escalation_Label"}
	missing_columns = required_columns - set(data.columns)
	if missing_columns:
		raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
	return data.sort_values(["Victim_ID", "Timepoint"]).reset_index(drop=True)


def get_feature_columns(data):
	excluded_columns = IDENTIFIER_COLUMNS | {"Date_Time"}
	return [
		column
		for column in data.columns
		if column not in excluded_columns
		and pd.api.types.is_numeric_dtype(data[column])
	]


def prepare_features(data, feature_columns=None):
	feature_columns = feature_columns or get_feature_columns(data)
	features = data[feature_columns].replace([np.inf, -np.inf], np.nan)
	return features.fillna(0.0).astype(np.float32), feature_columns


def fit_scaler(features):
	from sklearn.preprocessing import StandardScaler
	scaler = StandardScaler()
	if features.ndim == 3:
		samples, timesteps, num_features = features.shape
		features_2d = features.reshape(samples * timesteps, num_features)
		scaler.fit(features_2d)
	else:
		scaler.fit(features)
	return scaler


def apply_scaler(scaler, features):
	if features.ndim == 3:
		samples, timesteps, num_features = features.shape
		features_2d = features.reshape(samples * timesteps, num_features)
		scaled_2d = scaler.transform(features_2d)
		return scaled_2d.reshape(samples, timesteps, num_features)
	else:
		return scaler.transform(features)

