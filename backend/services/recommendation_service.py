"""
Clinical Recommendation & Safety Protocol Service (Step 26)
============================================================

Aggregates persisted multi-modal predictions and contextual risk indicators for a Case,
and invokes the frozen MEDHA Recommendation Engine (`engine/recommendation_engine/`)
and Alert Engine (`engine/alert_engine/`) to produce clinician decision support
recommendations, tailored self-help resources, and evaluated safety protocols.

Key Principles:
  - Consumes existing stored prediction results (`PredictionResultModel`),
    safety events (`SafetyEventModel`), and session state snapshots.
  - Reuses the existing backend prediction/triage/fusion interpretation and trend
    determination from Step 25; does NOT create a new trend calculation or fabricate data.
  - Preserves the distinction between distress/risk and safety.
  - Preserves the conversational safety fast-path (`AlertEngine.evaluate_conversational_safety`).
  - Decision support only: never asserts clinical certainty or diagnoses.
  - Handles missing / null prediction results safely (results_available=False).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Union

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.persistence.models.case import Case
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.safety_event import SafetyEventModel
from backend.persistence.models.session import SessionModel
from backend.schemas.recommendations import (
    CaseRecommendationsResponse,
    RecommendationItem,
    SafetyProtocolResponse,
    SelfHelpResourceItem,
)
from engine.alert_engine import (
    AlertEngine,
    AlertInput,
    AlertOutput,
    ContextInput as AlertContextInput,
    RiskLevel as AlertRiskLevel,
    SignalsInput as AlertSignalsInput,
    Trend as AlertTrend,
    evaluate_conversational_safety,
)
from engine.recommendation_engine import (
    ContextInput as RecContextInput,
    Intent,
    RecommendationEngine,
    RecommendationEngineInput,
    RiskLevel as RecRiskLevel,
    SignalsInput as RecSignalsInput,
    Trend as RecTrend,
)


class RecommendationService:
    """
    Service layer providing clinical recommendations and dynamic safety protocol evaluation.
    """

    def __init__(
        self,
        rec_engine: Optional[RecommendationEngine] = None,
        alert_engine: Optional[AlertEngine] = None,
    ):
        self.rec_engine = rec_engine or RecommendationEngine()
        self.alert_engine = alert_engine or AlertEngine()

    def get_case_recommendations(
        self,
        db: Session,
        case: Case,
        session_id: Optional[uuid.UUID] = None,
    ) -> CaseRecommendationsResponse:
        """
        Aggregates stored case signals, runs the recommendation and alert engines,
        and constructs a validated CaseRecommendationsResponse.

        :param db: Active SQLAlchemy database session.
        :param case: Authorized Case entity.
        :param session_id: Optional session UUID for session-specific recommendation.
        :return: CaseRecommendationsResponse Pydantic model.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch relevant prediction result(s)
        if session_id is not None:
            prediction = (
                db.query(PredictionResultModel)
                .filter(
                    PredictionResultModel.case_id == case.id,
                    PredictionResultModel.session_id == session_id,
                )
                .order_by(desc(PredictionResultModel.created_at))
                .first()
            )
        else:
            prediction = (
                db.query(PredictionResultModel)
                .filter(PredictionResultModel.case_id == case.id)
                .order_by(
                    desc(PredictionResultModel.timepoint),
                    desc(PredictionResultModel.created_at),
                )
                .first()
            )

        # 2. Extract context flags from safety alerts & session state
        context_flags = self._aggregate_context(db, case.id)

        # 3. Handle missing / unavailable prediction results
        if prediction is None or prediction.fusion_dds_prediction is None:
            # If no prediction is available, evaluate safety protocol on contextual flags only
            safety_protocol = None
            if any(context_flags.values()):
                alert_ctx = AlertContextInput(**context_flags)
                alert_in = AlertInput(
                    case_id=str(case.id),
                    risk_level=AlertRiskLevel.LOW,
                    fused_risk_score=0.0,
                    trend=AlertTrend.STABLE,
                    signals=AlertSignalsInput(),
                    context=alert_ctx,
                )
                alert_out = self.alert_engine.get_alert(alert_in)
                safety_protocol = self._build_safety_protocol_response(case.id, session_id, alert_out)

            return CaseRecommendationsResponse(
                case_id=case.id,
                victim_id=case.victim_id,
                session_id=session_id,
                timepoint=case.current_timepoint if prediction is None else prediction.timepoint,
                results_available=False,
                risk_level=None,
                triage_level=prediction.triage_level if prediction else None,
                fused_risk_score=None,
                recommendations=[],
                self_help_resources=[],
                safety_protocol=safety_protocol,
                disclaimer="This is a support-oriented recommendation and is not a medical diagnosis.",
                generated_at=now,
            )

        # 4. Determine longitudinal trend from actual historical predictions
        # (Strict rule: do not fabricate historical data)
        historical_preds = (
            db.query(PredictionResultModel)
            .filter(
                PredictionResultModel.case_id == case.id,
                PredictionResultModel.fusion_dds_prediction.isnot(None),
            )
            .order_by(PredictionResultModel.timepoint.asc(), PredictionResultModel.created_at.asc())
            .all()
        )

        trend_rec = RecTrend.STABLE
        trend_alert = AlertTrend.STABLE

        if len(historical_preds) >= 2:
            latest_score = historical_preds[-1].fusion_dds_prediction
            prev_score = historical_preds[-2].fusion_dds_prediction
            if latest_score is not None and prev_score is not None:
                delta = latest_score - prev_score
                if delta >= 5.0:
                    trend_rec = RecTrend.INCREASING
                    trend_alert = AlertTrend.INCREASING
                elif delta <= -5.0:
                    trend_rec = RecTrend.DECREASING
                    trend_alert = AlertTrend.DECREASING

        # 5. Map risk level and normalized scores
        risk_level_str = self._resolve_risk_level_str(
            triage_level=prediction.triage_level,
            fusion_dds=prediction.fusion_dds_prediction,
        )
        rec_risk_level = RecRiskLevel.from_str(risk_level_str)
        alert_risk_level = AlertRiskLevel.from_str(risk_level_str)

        fused_score_norm = max(0.0, min(1.0, prediction.fusion_dds_prediction / 100.0))

        # Modality signals
        rec_signals = RecSignalsInput(
            text_distress=(prediction.text_pred / 100.0) if prediction.text_pred is not None else 0.0,
            voice_distress=(prediction.voice_pred / 100.0) if prediction.voice_pred is not None else 0.0,
            structured_risk=(prediction.struct_pred / 100.0) if prediction.struct_pred is not None else 0.0,
            behavioural_risk=(prediction.behav_pred / 100.0) if prediction.behav_pred is not None else 0.0,
            temporal_risk=prediction.temporal_risk_score if prediction.temporal_risk_score is not None else 0.0,
        )

        alert_signals = AlertSignalsInput(
            text_distress=(prediction.text_pred / 100.0) if prediction.text_pred is not None else None,
            voice_distress=(prediction.voice_pred / 100.0) if prediction.voice_pred is not None else None,
            structured_risk=(prediction.struct_pred / 100.0) if prediction.struct_pred is not None else None,
            behavioural_risk=(prediction.behav_pred / 100.0) if prediction.behav_pred is not None else None,
            temporal_risk=prediction.temporal_risk_score,
        )

        # Context inputs
        rec_context = RecContextInput(**context_flags)
        alert_context = AlertContextInput(**context_flags)

        # Active intent if present in session snapshot
        active_intent = self._extract_session_intent(db, case.id, session_id)

        # 6. Execute Recommendation Engine
        rec_engine_input = RecommendationEngineInput(
            case_id=str(case.id),
            fused_risk_score=fused_score_norm,
            risk_level=rec_risk_level,
            trend=trend_rec,
            signals=rec_signals,
            context=rec_context,
            intent=active_intent,
        )
        rec_output = self.rec_engine.get_recommendations(rec_engine_input)

        # 7. Execute Alert Engine (Safety Protocol)
        alert_engine_input = AlertInput(
            case_id=str(case.id),
            risk_level=alert_risk_level,
            fused_risk_score=fused_score_norm,
            trend=trend_alert,
            signals=alert_signals,
            context=alert_context,
        )
        alert_output = self.alert_engine.get_alert(alert_engine_input)
        safety_protocol = self._build_safety_protocol_response(case.id, session_id, alert_output)

        # 8. Assemble structured Pydantic response
        recs_list = [
            RecommendationItem(
                id=r.id,
                category=r.category,
                priority=r.priority,
                reason=r.reason,
                action=r.action,
            )
            for r in rec_output.recommendations
        ]

        self_help_list = [
            SelfHelpResourceItem(
                id=s.id,
                type=s.type,
                title=s.title,
                category=s.category,
                description=s.description,
            )
            for s in rec_output.self_help
        ]

        return CaseRecommendationsResponse(
            case_id=case.id,
            victim_id=case.victim_id,
            session_id=session_id or prediction.session_id,
            timepoint=prediction.timepoint,
            results_available=True,
            risk_level=risk_level_str,
            triage_level=prediction.triage_level or "UNKNOWN",
            fused_risk_score=prediction.fusion_dds_prediction,
            recommendations=recs_list,
            self_help_resources=self_help_list,
            safety_protocol=safety_protocol,
            disclaimer="This is a support-oriented recommendation and is not a medical diagnosis.",
            generated_at=now,
        )

    def get_safety_protocol(
        self,
        db: Session,
        case: Case,
        session_id: Optional[uuid.UUID] = None,
    ) -> SafetyProtocolResponse:
        """
        Evaluates and returns the current dynamic safety protocol and alert status for a case.
        """
        rec_resp = self.get_case_recommendations(db=db, case=case, session_id=session_id)
        if rec_resp.safety_protocol is not None:
            return rec_resp.safety_protocol

        # Fallback to routine monitoring protocol if no prediction or safety protocol
        alert_in = AlertInput(
            case_id=str(case.id),
            risk_level=AlertRiskLevel.LOW,
            fused_risk_score=0.0,
            trend=AlertTrend.STABLE,
            signals=AlertSignalsInput(),
            context=AlertContextInput(),
        )
        alert_out = self.alert_engine.get_alert(alert_in)
        return self._build_safety_protocol_response(case.id, session_id, alert_out)

    def check_conversational_safety(
        self,
        text: str,
        case_id: str = "UNKNOWN",
        safety_concern_mentioned: Optional[bool] = None,
    ) -> Optional[dict]:
        """
        Immediate conversational fast-path wrapper.
        """
        return evaluate_conversational_safety(
            text=text,
            case_id=case_id,
            safety_concern_mentioned=safety_concern_mentioned,
        )

    def _build_safety_protocol_response(
        self,
        case_id: uuid.UUID,
        session_id: Optional[uuid.UUID],
        alert_out: AlertOutput,
    ) -> SafetyProtocolResponse:
        return SafetyProtocolResponse(
            alert_id=alert_out.alert_id,
            case_id=case_id,
            session_id=session_id,
            alert_triggered=alert_out.alert_triggered,
            priority=alert_out.priority,
            alert_type=alert_out.alert_type,
            title=alert_out.title,
            message=alert_out.message,
            recommended_action=alert_out.recommended_action,
            cta=alert_out.cta,
            reason=alert_out.reason,
            source=alert_out.source,
            reason_codes=alert_out.reason_codes,
            status=alert_out.status,
            timestamp=alert_out.timestamp,
        )

    def _resolve_risk_level_str(
        self,
        triage_level: Optional[str],
        fusion_dds: Optional[float],
    ) -> str:
        """Maps triage or DDS score to canonical risk level string."""
        if triage_level:
            normalized = triage_level.strip().upper()
            if normalized == "CRITICAL":
                return "CRITICAL"
            elif normalized == "HIGH":
                return "HIGH"
            elif normalized in ("MEDIUM", "MODERATE"):
                return "MODERATE"
            elif normalized == "LOW":
                return "LOW"

        if fusion_dds is not None:
            if fusion_dds >= 80.0:
                return "CRITICAL"
            elif fusion_dds >= 60.0:
                return "HIGH"
            elif fusion_dds >= 40.0:
                return "MODERATE"
            else:
                return "LOW"

        return "LOW"

    def _aggregate_context(self, db: Session, case_id: uuid.UUID) -> dict:
        """Aggregates contextual risk and profile flags from safety events and session snapshots."""
        events = (
            db.query(SafetyEventModel)
            .filter(SafetyEventModel.case_id == case_id)
            .all()
        )

        threat_event = False
        protection_issue = False

        for ev in events:
            event_type = (ev.event_type or "").lower()
            severity = (ev.severity or "").upper()
            if severity in ("CRITICAL", "HIGH") or any(
                t in event_type for t in ["threat", "self_harm", "safety_escalation", "danger"]
            ):
                threat_event = True
            if "protection" in event_type or severity == "CRITICAL":
                protection_issue = True

        latest_session = (
            db.query(SessionModel)
            .filter(SessionModel.case_id == case_id)
            .order_by(desc(SessionModel.updated_at))
            .first()
        )

        financial_hardship = False
        rehabilitation_issue = False
        investigation_delay = False
        compensation_delay = False

        if latest_session and latest_session.state_snapshot:
            struct_feat = latest_session.state_snapshot.get("structured_features", {})
            intake_ctx = latest_session.state_snapshot.get("context", {})

            financial_hardship = bool(
                struct_feat.get("financial_hardship")
                or intake_ctx.get("financial_hardship")
            )
            rehabilitation_issue = bool(
                struct_feat.get("rehabilitation_issue")
                or intake_ctx.get("rehabilitation_issue")
            )
            investigation_delay = bool(
                struct_feat.get("investigation_delay")
                or intake_ctx.get("investigation_delay")
            )
            compensation_delay = bool(
                struct_feat.get("compensation_delay")
                or intake_ctx.get("compensation_delay")
            )
            if intake_ctx.get("threat_event"):
                threat_event = True
            if intake_ctx.get("protection_issue"):
                protection_issue = True

        return {
            "threat_event": threat_event,
            "protection_issue": protection_issue,
            "financial_hardship": financial_hardship,
            "rehabilitation_issue": rehabilitation_issue,
            "investigation_delay": investigation_delay,
            "compensation_delay": compensation_delay,
        }

    def _extract_session_intent(
        self,
        db: Session,
        case_id: uuid.UUID,
        session_id: Optional[uuid.UUID],
    ) -> Optional[Union[Intent, List[Intent]]]:
        """Extracts active intent from session state snapshot if present."""
        target_session = None
        if session_id:
            target_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        else:
            target_session = (
                db.query(SessionModel)
                .filter(SessionModel.case_id == case_id)
                .order_by(desc(SessionModel.updated_at))
                .first()
            )

        if target_session and target_session.state_snapshot:
            raw_intent = (
                target_session.state_snapshot.get("active_intent")
                or target_session.state_snapshot.get("intent")
            )
            if raw_intent:
                try:
                    if isinstance(raw_intent, list):
                        return [Intent.from_str(str(i)) for i in raw_intent]
                    return Intent.from_str(str(raw_intent))
                except Exception:
                    return None
        return None
