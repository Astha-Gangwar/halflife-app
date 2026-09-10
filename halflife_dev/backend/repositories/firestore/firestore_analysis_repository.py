from typing import Optional
from datetime import datetime
from backend.utils.clock import utcnow, normalize_firestore_datetimes
from backend.repositories.interfaces.analysis_repository import AnalysisRepository
from backend.domain.schemas.analysis import Analysis, AnalysisResult, ValidationError
from backend.domain.enums import AnalysisStatus, ConfirmationStatus

COLLECTION = "analyses"


class FirestoreAnalysisRepository(AnalysisRepository):
    def __init__(self, db):
        self.db = db

    def create(self, record: Analysis) -> Analysis:
        doc = {
            "analysis_id": record.analysis_id,
            "user_id": record.user_id,
            "item_draft_id": record.item_draft_id,
            "original_content_snapshot": record.original_content_snapshot,
            "model_name": record.model_name,
            "model_version": record.model_version,
            "prompt_version": record.prompt_version,
            "model_result": record.model_result.model_dump(mode="json") if record.model_result else None,
            "validation_status": record.validation_status,
            "validation_errors": [e.model_dump(mode="json") for e in record.validation_errors],
            "status": record.status.value,
            "confirmation_status": record.confirmation_status.value,
            "approved_result": record.approved_result.model_dump(mode="json") if record.approved_result else None,
            "item_id": record.item_id,
            "created_at": record.created_at,
            "completed_at": record.completed_at,
            "confirmed_at": record.confirmed_at,
        }
        self.db.collection(COLLECTION).document(record.analysis_id).set(doc)
        return self._to_domain(doc)

    def get_by_id(self, analysis_id: str, user_id: str) -> Optional[Analysis]:
        snap = self.db.collection(COLLECTION).document(analysis_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict()
        if data.get("user_id") != user_id:
            return None
        return self._to_domain(data)

    def update_approved_result(self, analysis_id: str, user_id: str, approved_result: dict) -> Analysis:
        doc_ref = self.db.collection(COLLECTION).document(analysis_id)
        snap = doc_ref.get()
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("ANALYSIS_NOT_FOUND_OR_NOT_ACCESSIBLE: analysis not found or unauthorized")
        data = snap.to_dict()

        result_model = AnalysisResult.model_validate(approved_result)
        updates = {
            "approved_result": result_model.model_dump(mode="json"),
            "confirmation_status": ConfirmationStatus.ACCEPTED.value,
            "confirmed_at": utcnow(),
        }
        doc_ref.update(updates)
        data.update(updates)
        return self._to_domain(data)

    def _to_domain(self, data: dict) -> Analysis:
        data = normalize_firestore_datetimes(data)
        return Analysis(
            analysis_id=data["analysis_id"],
            user_id=data["user_id"],
            item_draft_id=data.get("item_draft_id"),
            original_content_snapshot=data["original_content_snapshot"],
            model_name=data["model_name"],
            model_version=data["model_version"],
            prompt_version=data["prompt_version"],
            model_result=AnalysisResult.model_validate(data["model_result"]) if data.get("model_result") else None,
            validation_status=data["validation_status"],
            validation_errors=[ValidationError.model_validate(e) for e in data.get("validation_errors") or []],
            status=AnalysisStatus(data["status"]),
            confirmation_status=ConfirmationStatus(data["confirmation_status"]),
            approved_result=AnalysisResult.model_validate(data["approved_result"]) if data.get("approved_result") else None,
            item_id=data.get("item_id"),
            created_at=data["created_at"],
            completed_at=data.get("completed_at"),
            confirmed_at=data.get("confirmed_at"),
        )
