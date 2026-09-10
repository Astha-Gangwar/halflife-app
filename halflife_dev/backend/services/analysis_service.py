import uuid
from datetime import datetime
from backend.utils.clock import utcnow
from typing import Optional
from backend.domain.schemas.analysis import Analysis, AnalysisResult
from backend.domain.enums import AnalysisStatus, ConfirmationStatus
from backend.repositories.interfaces.analysis_repository import AnalysisRepository

class AnalysisService:
    def __init__(self, analysis_repo: AnalysisRepository):
        self.analysis_repo = analysis_repo

    def record_analysis(
        self,
        user_id: str,
        original_content: str,
        model_result: AnalysisResult,
        model_name: str,
        model_version: str,
        prompt_version: str,
    ) -> Analysis:
        """
        Persist a model's analysis result. VAL-003/VAL-004: an unknown intent
        or a result flagged requires_confirmation must not become an approved
        item without explicit user confirmation.
        """
        now = utcnow()
        requires_confirmation = model_result.requires_confirmation or model_result.intent_type is None

        record = Analysis(
            analysis_id=str(uuid.uuid4()),
            user_id=user_id,
            original_content_snapshot=original_content,
            model_name=model_name,
            model_version=model_version,
            prompt_version=prompt_version,
            model_result=model_result,
            validation_status="passed",
            status=AnalysisStatus.CONFIRMATION_REQUIRED if requires_confirmation else AnalysisStatus.COMPLETED,
            confirmation_status=ConfirmationStatus.PENDING if requires_confirmation else ConfirmationStatus.NOT_REQUIRED,
            created_at=now,
            completed_at=now,
        )
        return self.analysis_repo.create(record)

    def get_analysis(self, analysis_id: str, user_id: str) -> Optional[Analysis]:
        return self.analysis_repo.get_by_id(analysis_id, user_id)

    def confirm_analysis(self, analysis_id: str, user_id: str, approved_result: dict) -> Analysis:
        return self.analysis_repo.update_approved_result(analysis_id, user_id, approved_result)
