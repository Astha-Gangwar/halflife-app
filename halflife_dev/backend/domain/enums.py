from enum import Enum

class IntentType(str, Enum):
    RECIPE = "recipe"
    LEARNING_CONTENT = "learning_content"
    IDEA = "idea"
    TASK = "task"
    ACTIVITY_LOG = "activity_log"
    GENERAL_NOTE = "general_note"
    UNKNOWN = "unknown"

class ContentFormat(str, Enum):
    TEXT = "text"
    LINK = "link"
    IMAGE = "image"
    FILE = "file"

class ItemStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class LifecycleState(str, Enum):
    SAVED = "saved"
    CLASSIFIED = "classified"
    GROUPED = "grouped"
    SCHEDULED_FOR_REVIEW = "scheduled_for_review"
    RESURFACED = "resurfaced"
    TRIED = "tried"
    MODIFIED = "modified"
    COMPLETED = "completed"
    DISMISSED = "dismissed"
    NOT_RELEVANT = "not_relevant"
    ARCHIVED = "archived"

class AnalysisStatus(str, Enum):
    REQUESTED = "requested"
    PROCESSING = "processing"
    COMPLETED = "completed"
    VALIDATION_FAILED = "validation_failed"
    CONFIRMATION_REQUIRED = "confirmation_required"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ConfirmationStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    ACCEPTED = "accepted"
    USER_CORRECTED = "user_corrected"
    KEPT_GENERAL = "kept_general"
    CANCELLED = "cancelled"

class RelationshipStatus(str, Enum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    REMOVED = "removed"

class RelationshipType(str, Enum):
    NEAR_DUPLICATE = "near_duplicate"
    SIMILAR = "similar"
    VARIANT = "variant"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTINUATION = "continuation"
    SAME_TOPIC = "same_topic"
    SAME_COLLECTION = "same_collection"

class FeedbackValue(str, Enum):
    YES = "yes"
    NO = "no"
    PARTIAL = "partial"
    COMPLETED = "completed"
    POSTPONED = "postponed"
    TRIED = "tried"
    DISMISSED = "dismissed"
    NOT_RELEVANT = "not_relevant"
    MODIFIED = "modified"
    SKIPPED = "skipped"

class ActorType(str, Enum):
    USER = "user"
    AGENT = "agent"
    APPLICATION = "application"
    SCHEDULED_PROCESS = "scheduled_process"
    ADMINISTRATOR = "administrator"

class SourceType(str, Enum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    USER_CONFIRMED = "user_confirmed"
    SYSTEM_CALCULATED = "system_calculated"
    IMPORTED = "imported"

class EventStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"

class ResurfacingStatus(str, Enum):
    CANDIDATE = "candidate"
    ELIGIBLE = "eligible"
    SELECTED = "selected"
    PRESENTED = "presented"
    ACTED_ON = "acted_on"
    DISMISSED = "dismissed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class OutcomeType(str, Enum):
    TRIED = "tried"
    COMPLETED = "completed"
    MODIFIED = "modified"
    REMIND_LATER = "remind_later"
    DISMISSED = "dismissed"
    NOT_RELEVANT = "not_relevant"
    ARCHIVED = "archived"
    RESTORED = "restored"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
