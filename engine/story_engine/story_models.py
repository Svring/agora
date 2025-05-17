from pydantic import BaseModel, Field
from typing import Any, Optional, Tuple, Dict

# Assuming GameState and PlayerAction will be imported from their respective modules
# from .game_state import GameState
# from ..player_module.player_models import PlayerAction, PlayerId


class GameEffect(BaseModel):
    effect_type: str

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class UpdatePlayerStateEffect(GameEffect):
    effect_type: str = "UPDATE_PLAYER_STATE"
    player_id: Any  # Should be PlayerId from player_models
    updates: Dict[str, Any]


class AddItemToPlayerEffect(GameEffect):
    effect_type: str = "ADD_ITEM_TO_PLAYER"
    player_id: Any  # Should be PlayerId
    item_card_id: str
    quantity: int = 1


class NpcDialogueEffect(GameEffect):
    effect_type: str = "NPC_DIALOGUE"
    npc_id: str
    dialogue: str


class NarrativeUpdateEffect(GameEffect):
    effect_type: str = "NARRATIVE_UPDATE"
    description: str


class DMInput(BaseModel):
    current_game_state: Any  # Should be GameState from game_state.py
    last_player_action: Optional[Any] = (
        None  # Should be PlayerAction from player_models
    )

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class DMDecision(BaseModel):
    narrative_text_for_players: str
    internal_dm_thoughts: Optional[str] = None
    game_effects: Tuple[GameEffect, ...] = Field(default_factory=tuple)

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class StoryEngineError(BaseModel):
    message: str

    class Config:
        frozen = True
        arbitrary_types_allowed = True


class DMProcessingError(StoryEngineError):
    reason: str
