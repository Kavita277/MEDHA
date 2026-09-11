
CREATE TABLE users (
	id UUID NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	mobile VARCHAR(32), 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	must_change_password BOOLEAN NOT NULL, 
	last_login_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)




CREATE TABLE audit_logs (
	id UUID NOT NULL, 
	actor_user_id UUID, 
	actor_role VARCHAR(32), 
	action VARCHAR(100) NOT NULL, 
	resource_type VARCHAR(100), 
	resource_id VARCHAR(100), 
	status VARCHAR(32) NOT NULL, 
	ip_address VARCHAR(64), 
	user_agent VARCHAR(255), 
	metadata_payload JSON, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_user_id) REFERENCES users (id) ON DELETE SET NULL
)




CREATE TABLE therapists (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	display_name VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)




CREATE TABLE cases (
	id UUID NOT NULL, 
	victim_id VARCHAR(100) NOT NULL, 
	user_id UUID NOT NULL, 
	therapist_id UUID NOT NULL, 
	current_timepoint INTEGER NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	closed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(therapist_id) REFERENCES therapists (id) ON DELETE RESTRICT
)




CREATE TABLE behaviour_feature_snapshots (
	id UUID NOT NULL, 
	case_id UUID NOT NULL, 
	timepoint INTEGER NOT NULL, 
	app_interaction_duration FLOAT, 
	app_interaction_duration_deviation FLOAT, 
	checkin_response_delay FLOAT, 
	checkin_response_delay_deviation FLOAT, 
	checkin_completion_rate FLOAT, 
	missed_checkin_count FLOAT, 
	journal_entry_count FLOAT, 
	chat_message_count FLOAT, 
	late_night_usage_ratio FLOAT, 
	support_resource_access_count FLOAT, 
	aggregated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uix_case_timepoint_behaviour UNIQUE (case_id, timepoint), 
	FOREIGN KEY(case_id) REFERENCES cases (id) ON DELETE CASCADE
)




CREATE TABLE chat_sessions (
	id UUID NOT NULL, 
	case_id UUID NOT NULL, 
	session_identifier VARCHAR(100) NOT NULL, 
	timepoint INTEGER NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	state_snapshot JSON, 
	closed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES cases (id) ON DELETE RESTRICT
)




CREATE TABLE journal_entries (
	id UUID NOT NULL, 
	case_id UUID NOT NULL, 
	content TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES cases (id)
)




CREATE TABLE chat_messages (
	id UUID NOT NULL, 
	chat_session_id UUID NOT NULL, 
	role VARCHAR(32) NOT NULL, 
	content TEXT NOT NULL, 
	metadata_payload JSON, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chat_session_id) REFERENCES chat_sessions (id) ON DELETE RESTRICT
)




CREATE TABLE checkins (
	id UUID NOT NULL, 
	session_id UUID NOT NULL, 
	victim_id VARCHAR(64) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	current_question_id VARCHAR(64), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES chat_sessions (id) ON DELETE RESTRICT
)




CREATE TABLE prediction_results (
	id UUID NOT NULL, 
	case_id UUID NOT NULL, 
	session_id UUID, 
	timepoint INTEGER NOT NULL, 
	structured_score FLOAT, 
	text_score FLOAT, 
	voice_score FLOAT, 
	behaviour_score FLOAT, 
	fusion_score FLOAT, 
	temporal_risk FLOAT, 
	future_escalation_flag INTEGER, 
	triage_level VARCHAR(16), 
	explanation TEXT, 
	recommendation TEXT, 
	struct_available BOOLEAN NOT NULL, 
	text_available BOOLEAN NOT NULL, 
	voice_available BOOLEAN NOT NULL, 
	behav_available BOOLEAN NOT NULL, 
	predicted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES cases (id) ON DELETE CASCADE, 
	FOREIGN KEY(session_id) REFERENCES chat_sessions (id) ON DELETE SET NULL
)




CREATE TABLE raw_events (
	id UUID NOT NULL, 
	event_id VARCHAR(100) NOT NULL, 
	case_id UUID NOT NULL, 
	session_id UUID, 
	event_type VARCHAR(100) NOT NULL, 
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	metadata_payload JSON, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES cases (id) ON DELETE RESTRICT, 
	FOREIGN KEY(session_id) REFERENCES chat_sessions (id) ON DELETE SET NULL
)




CREATE TABLE safety_events (
	id UUID NOT NULL, 
	case_id UUID NOT NULL, 
	session_id UUID, 
	event_type VARCHAR NOT NULL, 
	severity VARCHAR NOT NULL, 
	detected_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR NOT NULL, 
	payload JSON, 
	handled_at TIMESTAMP WITH TIME ZONE, 
	handled_by UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES cases (id), 
	FOREIGN KEY(session_id) REFERENCES chat_sessions (id), 
	FOREIGN KEY(handled_by) REFERENCES users (id)
)




CREATE TABLE voice_records (
	id UUID NOT NULL, 
	case_id UUID NOT NULL, 
	session_id UUID, 
	timepoint VARCHAR NOT NULL, 
	audio_filename VARCHAR(255), 
	duration_seconds FLOAT, 
	extracted_features JSON, 
	transcript TEXT, 
	voice_score FLOAT, 
	processed_at TIMESTAMP WITH TIME ZONE, 
	available FLOAT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES cases (id), 
	FOREIGN KEY(session_id) REFERENCES chat_sessions (id)
)




CREATE TABLE checkin_questions (
	id UUID NOT NULL, 
	checkin_id UUID NOT NULL, 
	question_id VARCHAR(64) NOT NULL, 
	question_text TEXT NOT NULL, 
	question_order INTEGER NOT NULL, 
	answered_at TIMESTAMP WITH TIME ZONE, 
	answer JSON, 
	answer_status VARCHAR(32) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(checkin_id) REFERENCES checkins (id) ON DELETE CASCADE
)

