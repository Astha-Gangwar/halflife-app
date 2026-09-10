from backend.repositories.firestore.firestore_analysis_repository import FirestoreAnalysisRepository
from backend.services.analysis_service import AnalysisService
from backend.domain.schemas.analysis import AnalysisResult
from backend.domain.enums import IntentType, ConfidenceLevel, AnalysisStatus, ConfirmationStatus


def test_uncertain_result_requires_confirmation(db_session):
    service = AnalysisService(FirestoreAnalysisRepository(db_session))
    result = AnalysisResult(intent_type=None, confidence=ConfidenceLevel.LOW, requires_confirmation=True, uncertainty_reason="ambiguous")

    record = service.record_analysis("user-1", "Running, five kilometres", result, "gemini", "v1", "v1")

    assert record.status == AnalysisStatus.CONFIRMATION_REQUIRED
    assert record.confirmation_status == ConfirmationStatus.PENDING


def test_confident_result_does_not_require_confirmation(db_session):
    service = AnalysisService(FirestoreAnalysisRepository(db_session))
    result = AnalysisResult(intent_type=IntentType.GENERAL_NOTE, confidence=ConfidenceLevel.HIGH, requires_confirmation=False)

    record = service.record_analysis("user-1", "Just a note", result, "gemini", "v1", "v1")

    assert record.status == AnalysisStatus.COMPLETED
    assert record.confirmation_status == ConfirmationStatus.NOT_REQUIRED
