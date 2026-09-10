import numpy as np


def build_sliding_windows(
	data,
	feature_columns,
	target_column="Future_Escalation_Label",
	window_size=7,
):
	sequences = []
	labels = []
	victim_ids = []

	for victim_id, victim_data in data.groupby("Victim_ID", sort=True):
		victim_data = victim_data.sort_values("Timepoint")
		features = victim_data[feature_columns].to_numpy(dtype=np.float32)
		targets = victim_data[target_column].to_numpy()

		for end_index in range(window_size, len(victim_data)):
			if np.isnan(targets[end_index]):
				continue
			sequences.append(features[end_index - window_size:end_index])
			labels.append(targets[end_index])
			victim_ids.append(victim_id)



	if not sequences:
		raise ValueError("No valid sliding-window sequences were found.")

	return (
		np.stack(sequences),
		np.asarray(labels, dtype=np.float32),
		np.asarray(victim_ids),
	)


def build_sequences(data, feature_columns, target_column="Future_Escalation_Label", sequence_length=None):
	"""Backward-compatible wrapper for the old one-sequence-per-victim API."""
	if sequence_length is None:
		raise ValueError("Use build_sliding_windows for leakage-free temporal sequences.")
	return build_sliding_windows(
		data,
		feature_columns,
		target_column=target_column,
		window_size=sequence_length,
	)[:2]
