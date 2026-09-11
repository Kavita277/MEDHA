"""
Clinical Insights Service (Step 25)
===================================

Aggregates persisted multi-modal and clinical signals for a Case and generates
deterministic, support-oriented clinical insights using the frozen MEDHA
Explainability Engine (`engine/explainability_engine/`).

Key Principles:
  - Consumes existing stored prediction results (`PredictionResultModel`),
    safety events (`SafetyEventModel`), and patient activity telemetry.
  - Does NOT create new ML models or modify the frozen Explainability Engine.
  - Strict human-in-the-loop clinical decision support: never makes medical
    or psychiatric diagnostic assertions.
  - Handles missing / null prediction results gracefully (results_available=False).
  - Does NOT fabricate historical predictions. When historical prediction data
    is insufficient (< 2 timepoints), explicitly indicates limited/unavailable trend.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.persistence.models.behaviour_snapshot import BehaviourFeatureSnapshotModel
from backend.persistence.models.case import Case
from backend.persistence.models.chat_message import ChatMessageModel
from backend.persistence.models.checkin import CheckInModel
from backend.persistence.models.journal_entry import JournalEntryModel
from backend.persistence.models.prediction_result import PredictionResultModel
from backend.persistence.models.safety_event import SafetyEventModel
from backend.persistence.models.session import SessionModel
from backend.persistence.models.voice_record import VoiceRecordModel
from backend.schemas.insights import (
    CaseInsightsResponse,
    InsightActivitySummary,
    InsightContextSummary,
    InsightFactorItem,
    InsightSignalsSummary,
)
from engine.explainability_engine import (
    ContextInput,
    ExplainabilityEngine,
    ExplainabilityInput,
    RecentActivityInput,
    RiskLevel,
    SignalsInput,
    Trend,
)


class InsightService:
    """
    Service layer providing clinical explainability and insight aggregation.
    """

    def __init__(self, engine: Optional[ExplainabilityEngine] = None):
        self.engine = engine or ExplainabilityEngine()

    def get_case_insights(
        self,
        db: Session,
        case: Case,
        session_id: Optional[uuid.UUID] = None,
    ) -> CaseInsightsResponse:
        """
        Aggregates stored case signals, runs the explainability engine,
        and constructs a validated CaseInsightsResponse.

        :param db: Active SQLAlchemy database session.
        :param case: Authorized Case entity.
        :param session_id: Optional session UUID for session-specific insight.
        :return: CaseInsightsResponse Pydantic model.
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

        # Fetch case activity counts
        activity_summary = self._aggregate_activity(db, case.id)

        # Fetch context flags from safety alerts & session state
        context_summary = self._aggregate_context(db, case.id)

        # 2. Handle missing / unavailable prediction results gracefully
        if prediction is None or prediction.fusion_dds_prediction is None:
            return CaseInsightsResponse(
                case_id=case.id,
                victim_id=case.victim_id,
                session_id=session_id,
                timepoint=case.current_timepoint if prediction is None else prediction.timepoint,
                results_available=False,
                trend_available=False,
                risk_level=None,
                triage_level=prediction.triage_level if prediction else None,
                fused_risk_score=None,
                summary="No prediction or assessment data is currently available for this case. Clinical insights will be generated once initial assessments are completed.",
                factors=[],
                trend_explanation="Longitudinal trend data is not available because no prior assessments have been recorded.",
                disclaimer="This is a support-oriented explanation and is not a medical diagnosis.",
                signals=InsightSignalsSummary(
                    text_distress=prediction.text_pred if prediction else None,
                    voice_distress=prediction.voice_pred if prediction else None,
                    behavioural_risk=prediction.behav_pred if prediction else None,
                    structured_risk=prediction.struct_pred if prediction else None,
                    temporal_risk=prediction.temporal_risk_score if prediction else None,
                ),
                context=context_summary,
                recent_activity=activity_summary,
                generated_at=now,
            )

        # 3. Determine longitudinal trend from actual historical predictions
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

        trend_available = False
        trend_enum = Trend.STABLE
        trend_explanation_override: Optional[str] = None

        if len(historical_preds) >= 2:
            trend_available = True
            latest_score = historical_preds[-1].fusion_dds_prediction
            prev_score = historical_preds[-2].fusion_dds_prediction
            if latest_score is not None and prev_score is not None:
                delta = latest_score - prev_score
                if delta >= 5.0:
                    trend_enum = Trend.INCREASING
                elif delta <= -5.0:
                    trend_enum = Trend.DECREASING
                else:
                    trend_enum = Trend.STABLE
        else:
            # Insufficient longitudinal data for historical trend
            trend_available = False
            trend_enum = Trend.STABLE
            trend_explanation_override = "Longitudinal trend data is limited; single assessment recorded."

        # 4. Map risk level and normalized scores for Explainability Engine
        risk_level_enum = self._resolve_risk_level(
            triage_level=prediction.triage_level,
            fusion_dds=prediction.fusion_dds_prediction,
        )

        fused_score_norm = max(0.0, min(1.0, prediction.fusion_dds_prediction / 100.0))

        signals_input = SignalsInput(
            text_distress=(prediction.text_pred / 100.0) if prediction.text_pred is not None else None,
            voice_distress=(prediction.voice_pred / 100.0) if prediction.voice_pred is not None else None,
            structured_risk=(prediction.struct_pred / 100.0) if prediction.struct_pred is not None else None,
            behavioural_risk=(prediction.behav_pred / 100.0) if prediction.behav_pred is not None else None,
            temporal_risk=prediction.temporal_risk_score,
        )

        context_input = ContextInput(
            threat_event=context_summary.threat_event,
            protection_issue=context_summary.protection_issue,
            financial_hardship=context_summary.financial_hardship,
            rehabilitation_issue=context_summary.rehabilitation_issue,
            investigation_delay=context_summary.investigation_delay,
            compensation_delay=context_summary.compensation_delay,
        )

        recent_activity_input = RecentActivityInput(
            checkins=activity_summary.checkins,
            journal_entries=activity_summary.journal_entries,
            voice_interactions=activity_summary.voice_interactions,
            text_interactions=activity_summary.text_interactions,
        )

        explainability_input = ExplainabilityInput(
            case_id=str(case.id),
            fused_risk_score=fused_score_norm,
            risk_level=risk_level_enum,
            trend=trend_enum,
            signals=signals_input,
            context=context_input,
            recent_activity=recent_activity_input,
        )

        # 5. Run explainability engine
        explanation_output = self.engine.get_explanation(explainability_input)

        # 6. Filter factors if trend history is insufficient
        factors: List[InsightFactorItem] = []
        for factor in explanation_output.factors:
            if factor.type == "trend" and not trend_available:
                # Do not claim a historical trend if history is insufficient
                continue
            factors.append(
                InsightFactorItem(
                    factor=factor.factor,
                    description=factor.description,
                    type=factor.type,
                )
            )

        final_trend_explanation = (
            trend_explanation_override
            if trend_explanation_override is not None
            else explanation_output.trend_explanation
        )

        return CaseInsightsResponse(
            case_id=case.id,
            victim_id=case.victim_id,
            session_id=session_id or prediction.session_id,
            timepoint=prediction.timepoint,
            results_available=True,
            trend_available=trend_available,
            risk_level=risk_level_enum.value,
            triage_level=prediction.triage_level or "UNKNOWN",
            fused_risk_score=prediction.fusion_dds_prediction,
            summary=explanation_output.summary,
            factors=factors,
            trend_explanation=final_trend_explanation,
            disclaimer=explanation_output.disclaimer,
            signals=InsightSignalsSummary(
                text_distress=prediction.text_pred,
                voice_distress=prediction.voice_pred,
                behavioural_risk=prediction.behav_pred,
                structured_risk=prediction.struct_pred,
                temporal_risk=prediction.temporal_risk_score,
            ),
            context=context_summary,
            recent_activity=activity_summary,
            generated_at=now,
        )

    def _resolve_risk_level(
        self,
        triage_level: Optional[str],
        fusion_dds: Optional[float],
    ) -> RiskLevel:
        """Maps triage or DDS score to engine RiskLevel enum."""
        if triage_level:
            normalized = triage_level.strip().upper()
            if normalized == "CRITICAL":
                return RiskLevel.CRITICAL
            elif normalized == "HIGH":
                return RiskLevel.HIGH
            elif normalized in ("MEDIUM", "MODERATE"):
                return RiskLevel.MODERATE
            elif normalized == "LOW":
                return RiskLevel.LOW

        if fusion_dds is not None:
            if fusion_dds >= 80.0:
                return RiskLevel.CRITICAL
            elif fusion_dds >= 60.0:
                return RiskLevel.HIGH
            elif fusion_dds >= 40.0:
                return RiskLevel.MODERATE
            else:
                return RiskLevel.LOW

        return RiskLevel.LOW

    def _aggregate_activity(self, db: Session, case_id: uuid.UUID) -> InsightActivitySummary:
        """Aggregates patient interaction counts for the case."""
        checkin_count = (
            db.query(CheckInModel)
            .join(SessionModel, CheckInModel.session_id == SessionModel.id)
            .filter(SessionModel.case_id == case_id)
            .count()
        )
        journal_count = (
            db.query(JournalEntryModel)
            .filter(JournalEntryModel.case_id == case_id)
            .count()
        )
        voice_count = (
            db.query(VoiceRecordModel)
            .filter(VoiceRecordModel.case_id == case_id)
            .count()
        )
        chat_count = (
            db.query(ChatMessageModel)
            .join(SessionModel, ChatMessageModel.chat_session_id == SessionModel.id)
            .filter(SessionModel.case_id == case_id)
            .count()
        )

        return InsightActivitySummary(
            checkins=checkin_count,
            journal_entries=journal_count,
            voice_interactions=voice_count,
            text_interactions=chat_count,
        )

    def _aggregate_context(self, db: Session, case_id: uuid.UUID) -> InsightContextSummary:
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

        # Check latest session snapshot for intake context flags
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

        return InsightContextSummary(
            threat_event=threat_event,
            protection_issue=protection_issue,
            financial_hardship=financial_hardship,
            rehabilitation_issue=rehabilitation_issue,
            investigation_delay=investigation_delay,
            compensation_delay=compensation_delay,
        )
