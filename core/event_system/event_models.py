# Event definitions and dispatcher
# from typing import Callable, Dict, List, Any

from pydantic import BaseModel, Field
from typing import Callable, Dict, List, Any, TypeVar, Generic, Mapping, Tuple, Type
from datetime import datetime, timezone
import uuid
from enum import Enum


# Define available system event types
class SystemEventType(str, Enum):
    """Enumeration for different types of system events."""

    # --- General & Meta Event ---
    GENERAL_EVENT = "GENERAL_EVENT"  # For events not fitting specific module categories

    # --- Module-Specific Event Types ---
    PLAYER_MODULE_EVENT = (
        "PLAYER_MODULE_EVENT"  # Events originating from the Player Module
    )
    DM_MODULE_EVENT = "DM_MODULE_EVENT"  # Events originating from the DM Module/AI
    WORLD_MODULE_EVENT = (
        "WORLD_MODULE_EVENT"  # Events related to world state, NPCs, locations etc.
    )
    GAME_FLOW_EVENT = (
        "GAME_FLOW_EVENT"  # Events related to game turns, start/end, saving/loading
    )
    CARD_SYSTEM_EVENT = (
        "CARD_SYSTEM_EVENT"  # Events from the Card System (CRUD, loading)
    )
    NARRATIVE_SYSTEM_EVENT = (
        "NARRATIVE_SYSTEM_EVENT"  # Events from the Narrative System
    )
    CORE_SYSTEM_EVENT = (
        "CORE_SYSTEM_EVENT"  # Events from core backbone/system infrastructure
    )
    # Add other high-level module types as needed, e.g., UI_EVENT, AUDIO_EVENT etc.

    # --- Test Events (Kept from previous versions) ---
    TEST_EVENT = "TEST_EVENT"
    SPECIFIC_ERROR_TEST_EVENT = "SPECIFIC_ERROR_TEST_EVENT"

    # Specific actions like 'PLAYER_CREATED', 'CARD_UPDATED' will now be part of the event's payload, e.g.:
    # payload = {"action": "PLAYER_CREATED", "player_id": "..."}
    # payload = {"action": "CARD_UPDATED", "card_id": "...", "changes": {...}}


# Base Event Definition
class GameEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_name: SystemEventType = Field(
        ..., description="The specific type of the event."
    )
    source_module: str = Field(
        ..., description="The module or system that generated this event."
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Flexible field for event-specific data."
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Optional flexible metadata

    class Config:
        frozen = True
        arbitrary_types_allowed = True
        use_enum_values = True


# Example specific event (can be moved or expanded later)
# class PlayerActionSystemEvent(GameEvent):
#     player_id: str # Or PlayerId model
#     action_type: str # e.g., from PlayerAction.action_type
#     action_details: Dict[str, Any]


# Event Dispatcher (relevant for a fully event-driven system)
EventType = TypeVar(
    "EventType", bound=GameEvent
)  # This might be less relevant now, or needs re-evaluation.


# Pydantic Model for Listener Registry
class ListenerRegistry(
    BaseModel, Generic[EventType]
):  # Generic[EventType] might need to be Generic[GameEvent] or just removed if EventType becomes non-generic
    # Changed from _listeners to listeners, and types updated as per user example
    listeners: Dict[SystemEventType, Tuple[Callable[[GameEvent], None], ...]] = Field(
        default_factory=dict
    )

    class Config:
        frozen = True
        arbitrary_types_allowed = True  # Needed for Type[EventType]


# Removed the old subscribe and dispatch methods from this class.
# Those functionalities will be handled by pure functions in event_provider.py.
