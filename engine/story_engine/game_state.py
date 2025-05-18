from pydantic import BaseModel, Field, NonNegativeInt
from typing import Dict, Tuple, Any, Optional

# Assuming PlayerState will eventually be imported properly
from ..player_module.player_models import PlayerState, PlayerId


class GameState(BaseModel):
    game_id: str
    story_background_card_id: str

    current_location_id: Optional[str] = None

    player_states: Dict[PlayerId, PlayerState] = Field(default_factory=dict)

    turn_number: NonNegativeInt = 0
    # Keyed by str(PlayerId.id) - similar to player_states keying
    current_acting_player_id: Optional[PlayerId] = None

    event_log: Tuple[str, ...] = Field(default_factory=tuple)

    class Config:
        frozen = True
        arbitrary_types_allowed = True


# Comments related to removed fields or specific PlayerId/PlayerState usage can be cleaned up further
# if those types are finalized.

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
