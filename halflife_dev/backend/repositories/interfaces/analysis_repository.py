from abc import ABC, abstractmethod
from typing import Optional
from backend.domain.schemas.analysis import AnalysisRecord

class AnalysisRepository(ABC):
    @abstractmethod
    def create(self, record: AnalysisRecord) -> AnalysisRecord:
        pass

    @abstractmethod
    def get_by_id(self, analysis_id: str, user_id: str) -> Optional[AnalysisRecord]:
        pass
    
    @abstractmethod
    def update_approved_result(self, analysis_id: str, user_id: str, approved_result: dict) -> AnalysisRecord:
        pass
