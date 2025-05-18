from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union
import uuid
from enum import Enum
from datetime import datetime

from core.event_system.event_models import (
    GameEvent,
)  # Assuming GameEvent is in this path


class NarrativeSourceType(str, Enum):
    DM = "DM"
    PLAYER = "PLAYER"
    SYSTEM = "SYSTEM"  # For automated game events or rules engine outputs


class NarrativeType(str, Enum):
    SCENE_DESCRIPTION = "SCENE_DESCRIPTION"
    NPC_DIALOGUE = "NPC_DIALOGUE"
    PLAYER_ACTION_RESULT = (
        "PLAYER_ACTION_RESULT"  # Describes the outcome of a player's action
    )
    WORLD_EVENT = "WORLD_EVENT"  # E.g., a distant explosion, change in weather
    QUEST_UPDATE = "QUEST_UPDATE"
    LORE_DISCOVERY = "LORE_DISCOVERY"
    SYSTEM_MESSAGE = "SYSTEM_MESSAGE"  # E.g., "It's now Player X's turn"
    ERROR_NARRATION = (
        "ERROR_NARRATION"  # e.g. "You try to open the door, but it's locked."
    )


class NarrativeEvent(GameEvent):
    source_type: NarrativeSourceType
    source_id: Optional[str] = None  # PlayerId, NpcId, "SYSTEM"

    narrative_type: NarrativeType
    content: str  # The textual description or dialogue

    # Optional fields for more context
    target_entity_id: Optional[str] = (
        None  # Who this event is primarily about or directed to (e.g., an NPC ID if it's their dialogue)
    )
    location_id: Optional[str] = None  # Where the event takes place
    turn_number: Optional[int] = None  # Game turn when this event occurred

    # Visibility: Who can perceive this event.
    # If None, assumed to be visible to all relevant parties (e.g., all players in the current location).
    # Could be a list of PlayerIds or specific roles. For now, keeping it simple.
    visibility_scope: Optional[str] = (
        None  # E.g., "ALL", "PLAYER_ONLY", "DM_ONLY", or specific PlayerId/GroupId
    )

    # Specific narrative payload, if simple content is not enough.
    # For example, for a QUEST_UPDATE, this could contain structured quest data.
    narrative_payload: Optional[Dict[str, Any]] = None

    class Config:
        frozen = True
        arbitrary_types_allowed = True
