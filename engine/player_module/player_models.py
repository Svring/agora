from pydantic import BaseModel, Field
from typing import Tuple, Dict, Any, Optional
import uuid


class PlayerId(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class PlayerStatusEffect(BaseModel):
    name: str
    description: str
    duration_turns: Optional[int] = None  # None for permanent

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class PlayerState(BaseModel):
    player_id: PlayerId
    name: str
    archetype_card_id: str
    inventory_card_ids: Tuple[str, ...] = Field(default_factory=tuple)
    active_quest_ids: Tuple[str, ...] = Field(default_factory=tuple)
    status_effects: Tuple[PlayerStatusEffect, ...] = Field(default_factory=tuple)
    player_stats: Dict[str, Any] = Field(default_factory=dict)
    known_lore_card_ids: Tuple[str, ...] = Field(default_factory=tuple)

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class PlayerAction(BaseModel):
    player_id: PlayerId
    action_type: str

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class SpeakAction(PlayerAction):
    action_type: str = "SPEAK"
    message: str
    target_npc_id: Optional[str] = None


class MoveAction(PlayerAction):
    action_type: str = "MOVE"
    target_location_id: str


class UseItemAction(PlayerAction):
    action_type: str = "USE_ITEM"
    item_card_id: str
    target_id: Optional[str] = None


class GeneralAction(PlayerAction):
    action_type: str = "GENERAL"
    description: str


class PlayerModuleError(BaseModel):
    message: str

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class PlayerActionParseError(PlayerModuleError):
    raw_input: str
    reason: str
