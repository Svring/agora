# Represents the current state of the game world
# from typing import Dict, Any, List
# # from ...core.card_system.base_card import BaseCard # If game state holds card instances

from pydantic import BaseModel, Field
from typing import Dict, Tuple, Any, Optional

# from pathlib import Path # Not used in current snippet
# from ..player_module.player_models import PlayerId, PlayerState # Correct import path


class GameState(BaseModel):
    game_id: str
    story_background_card_id: str
    card_system_digest: str

    current_location_id: Optional[str] = None
    active_npcs_in_location: Tuple[str, ...] = Field(default_factory=tuple)
    world_facts: Dict[str, Any] = Field(default_factory=dict)

    # Using Any for PlayerState for now, to be replaced with actual import
    # Keyed by str(PlayerId.id)
    player_states: Dict[str, Any] = Field(default_factory=dict)

    turn_number: int = 0
    # Keyed by str(PlayerId.id)
    current_acting_player_id: Optional[str] = None

    event_log: Tuple[str, ...] = Field(default_factory=tuple)

    class Config:
        frozen = True
        arbitrary_types_allowed = True


# Example of how PlayerId might be used as a key (conceptual)
# def get_player_state(game_state: GameState, player_id: PlayerId) -> Optional[PlayerState]:
#     return game_state.player_states.get(str(player_id.id))

# def update_player_state(game_state: GameState, player_state: PlayerState) -> GameState:
#     new_player_states = game_state.player_states.copy()
#     new_player_states[str(player_state.player_id.id)] = player_state
#     return game_state.model_copy(update={"player_states": new_player_states})

#     defget_summary_for_dm(self) -> str:
#         # Creates a textual summary of the game state relevant for the DM AI
#         player_summaries = []
#         for pid, pdata in self.players.items():
#             # Assuming pdata has a 'get_summary' method or relevant attributes
#             # player_summaries.append(f"Player {pid}: {pdata.get_summary()}")
#             player_summaries.append(f"Player {pid}: Status - TBD") # Placeholder
#         players_str = "\n".join(player_summaries)
#         return f"""
#         Story Background: {self.current_story_background_id}
#         DM Profile: {self.current_dm_profile_id}
#         Players:\n{players_str}
#         World State: {self.world_state}
#         Turn: {self.turn_number}
#         Active Quests: {', '.join(self.active_quests) if self.active_quests else 'None'}
#         """

#     def update_player_state(self, player_id: str, new_state_data: Dict[str, Any]):
#         if player_id in self.players:
#             self.players[player_id].update(new_state_data) # Or more structured update
#         else:
#             # Handle new player or error
#             pass

#     def update_world_state(self, key: str, value: Any):
#         self.world_state[key] = value

#     def increment_turn(self):
#         self.turn_number += 1
