# Controls narrative flow, events, and game progression
# # from ..dm_ai.dm_agent import DMAgent
# # from .game_state import GameState
# # from ...core.event_system.events import EventDispatcher, PlayerActionEvent
# # from ...core.card_system.card_manager import CardManager

# class StoryManager:
#     def __init__(self, dm_agent: DMAgent, game_state: GameState, event_dispatcher: EventDispatcher, card_manager: CardManager):
#         self.dm_agent = dm_agent
#         self.game_state = game_state
#         self.event_dispatcher = event_dispatcher
#         self.card_manager = card_manager
#         # self._subscribe_to_events()

#     # def _subscribe_to_events(self):
#     #     self.event_dispatcher.subscribe(PlayerActionEvent, self.handle_player_action)

#     def start_game(self, story_background_card_id: str, dm_profile_card_id: str, player_archetype_ids: list[str]):
#         # Load initial cards (story, DM)
#         # Initialize game state
#         # Potentially generate an introductory narrative from the DM
#         story_bg = self.card_manager.get_card(story_background_card_id)
#         dm_profile = self.card_manager.get_card(dm_profile_card_id)
#         # ... setup game_state.current_story_background, game_state.current_dm_profile
#         # intro_narrative = self.dm_agent.generate_narrative(self.game_state)
#         # print(intro_narrative) # Or send to an interface
#         pass

#     def handle_player_action(self, event: PlayerActionEvent):
#         # Update game state based on player action
#         # self.game_state.update_based_on_action(event.player_id, event.action, event.details)
#         # Get DM response
#         # dm_response = self.dm_agent.process_player_action(event.action, self.game_state)
#         # print(f"DM: {dm_response}") # Or send to an interface
#         # Potentially trigger further narrative or game state changes
#         pass

#     def advance_story(self):
#         # Logic for story progression, could be event-driven or DM-initiated
#         # narrative_update = self.dm_agent.generate_narrative(self.game_state)
#         # print(narrative_update)
#         pass

# Conceptual outline for StoryManager / LangGraph Orchestrator

# from typing_extensions import TypedDict
# from typing import Annotated, Optional
# from langgraph.graph import StateGraph, START, END
# from langgraph.graph.message import add_messages # If using chat messages
# from returns.result import Result, Success, Failure

# from core.card_system.card_provider import CardSystemState
# from ..dm_ai.dm_agent import LangchainDMCore # Your DM agent
# from .game_state import GameState
# from .story_models import DMInput, DMDecision, StoryEngineError, DMProcessingError
# from ..player_module.player_models import PlayerAction


# # 1. Define Graph State (as discussed in the explanation)
# class GraphOrchestratorState(TypedDict):
#     game_state: GameState
#     current_player_action: Optional[PlayerAction]
#     dm_decision: Optional[DMDecision]
#     error_message: Optional[str]
#     # messages: Annotated[list, add_messages] # if using message-based graph state

# # 2. Initialize DM Agent and other services
# # dm_agent_instance = LangchainDMCore(...)
# # (This would likely be initialized with model, API keys etc. from config)

# # 3. Define Graph Nodes
# # def determine_player_input_node(state: GraphOrchestratorState) -> GraphOrchestratorState:
# #     # Logic to get next player action (could be from a queue, or wait for input)
# #     # Updates state.current_player_action
# #     # This might be an entry point to the graph run rather than a node if action is passed in.
# #     print("--- Determining Player Input ---")
# #     # ... placeholder ...
# #     return state

# def dm_ai_node(state: GraphOrchestratorState) -> GraphOrchestratorState:
#     print("--- DM AI Processing ---")
#     if not state.get('current_player_action') or not state.get('game_state'):
#         return {**state, "error_message": "Missing player action or game state for DM AI."}

#     dm_input = DMInput(
#         current_game_state=state['game_state'],
#         last_player_action=state['current_player_action']
#     )

#     # dm_response_text = dm_agent_instance.generate_response(
#     #     game_state_summary=f"Turn: {dm_input.current_game_state.turn_number}, Loc: {dm_input.current_game_state.current_location_id}",
#     #     player_action_description=str(dm_input.last_player_action)
#     # )
#     # This is simplified. The actual call to dm_agent should be more structured,
#     # and the response needs to be parsed into DMDecision (narrative + GameEffects).
#     # For now, creating a placeholder DMDecision:
#     placeholder_decision = DMDecision(
#         narrative_text_for_players=f"DM responds to {state['current_player_action'].action_type}: Placeholder narrative.",
#         game_effects=tuple()
#     )
#     return {**state, "dm_decision": placeholder_decision, "error_message": None}

# def game_state_update_node(state: GraphOrchestratorState) -> GraphOrchestratorState:
#     print("--- Updating Game State ---")
#     current_gs = state.get('game_state')
#     dm_decision = state.get('dm_decision')

#     if not current_gs or not dm_decision:
#         return {**state, "error_message": "Missing game state or DM decision for update."}

#     new_gs = current_gs # Start with the old state

#     # Apply GameEffects from DMDecision to new_gs (immutable updates)
#     # For example:
#     # for effect in dm_decision.game_effects:
#     #     if isinstance(effect, AddItemToPlayerEffect):
#     #         player_id_str = str(effect.player_id.id) # Assuming PlayerId has .id
#     #         if player_id_str in new_gs.player_states:
#     #             player_state_to_update = new_gs.player_states[player_id_str]
#     #             new_inventory = player_state_to_update.inventory_card_ids + (effect.item_card_id,)
#     #             updated_player = player_state_to_update.model_copy(update={"inventory_card_ids": new_inventory})
#     #
#     #             new_player_states_map = new_gs.player_states.copy()
#     #             new_player_states_map[player_id_str] = updated_player
#     #             new_gs = new_gs.model_copy(update={"player_states": new_player_states_map})
#     #     # ... handle other effects

#     # Increment turn number if applicable
#     new_gs = new_gs.model_copy(update={"turn_number": new_gs.turn_number + 1})
#     # Log event
#     new_event_log = new_gs.event_log + (f"Turn {new_gs.turn_number}: DMDecision processed.",)
#     new_gs = new_gs.model_copy(update={"event_log": new_event_log})

#     return {**state, "game_state": new_gs, "error_message": None, "current_player_action": None, "dm_decision": None}

# def narrative_output_node(state: GraphOrchestratorState) -> GraphOrchestratorState:
#     print("--- Narrative Output ---")
#     if state.get('dm_decision'):
#         print(f"DM Says: {state['dm_decision'].narrative_text_for_players}")
#     if state.get('error_message'):
#         print(f"Error in graph: {state['error_message']}")
#     return state

# # 4. Build the Graph
# # workflow = StateGraph(GraphOrchestratorState)
# # workflow.add_node("dm_ai", dm_ai_node)
# # workflow.add_node("update_state", game_state_update_node)
# # workflow.add_node("output_narrative", narrative_output_node)

# # workflow.add_edge(START, "dm_ai") # Or from a player input node
# # workflow.add_edge("dm_ai", "update_state")
# # workflow.add_edge("update_state", "output_narrative")
# # workflow.add_edge("output_narrative", END) # Or loop back for next turn

# # # Conditional edges for error handling or different paths
# # def should_continue(state: GraphOrchestratorState):
# #     if state.get("error_message"):
# #         return "output_narrative" # Go to output to show error, then END or an error_handler_node
# #     return "update_state"
# # workflow.add_conditional_edges("dm_ai", should_continue, {
# #     "update_state": "update_state",
# #     "output_narrative": "output_narrative"
# # })


# # graph = workflow.compile()

# # 5. StoryManager Class (Interface to the Graph)
# # class StoryManager(BaseModel):
# #     card_system_state: CardSystemState
# #     # current_game_state: GameState # GameState will be managed by the graph state
# #     # dm_agent: LangchainDMCore # DM Agent integrated into graph node
# #     graph_instance: Any # Compiled LangGraph

# #     class Config:
# #         arbitrary_types_allowed = True

# #     @classmethod
# #     def initialize_story_engine(cls, card_system: CardSystemState) -> 'StoryManager':
# #         # Compile and return graph instance with necessary initializations
# #         compiled_graph = graph # from above
# #         return cls(card_system_state=card_system, graph_instance=compiled_graph)

# #     def initialize_new_game(self, story_background_card_id: str, player_archetype_card_ids: Dict[str, str]) -> Result[GameState, StoryEngineError]:
# #         # Create initial PlayerStates using player_module.player_manager.create_player_state
# #         # Construct the very first GameState object
# #         # initial_gs = GameState(...)
# #         # This initial_gs would be the input for the first run of the graph, or to set its initial state.
# #         # return Success(initial_gs)
# #         pass

# #     def process_player_action(self, current_gs: GameState, action: PlayerAction) -> Result[GameState, StoryEngineError]:
# #         initial_graph_state: GraphOrchestratorState = {
# #             "game_state": current_gs,
# #             "current_player_action": action,
# #             "dm_decision": None,
# #             "error_message": None
# #         }
# #         # config = {"configurable": {"thread_id": "game_session_123"}} # For checkpointers
# #         # final_graph_state_stream = self.graph_instance.stream(initial_graph_state, config=config)
# #         # final_state = None
# #         # for Gs_event in final_graph_state_stream:
# #         #    final_state = Gs_event # get the last state

# #         # if final_state and final_state.get("game_state") and not final_state.get("error_message"):
# #         #     return Success(final_state["game_state"])
# #         # else:
# #         #     error_msg = final_state.get("error_message", "Unknown graph execution error") if final_state else "Graph did not run"
# #         #     return Failure(StoryEngineError(message=error_msg))
# #         pass


# # The existing StoryManagerError and StoryManagerResult from your file could be adapted or merged.
# # from pydantic import BaseModel
# # from typing import Union
# # from .game_state import GameState
# # from ...core.card_system.card_provider import CardSystemState
# # from ..dm_ai.dm_agent import LangchainDMCore # Placeholder

# # class StoryManagerError(BaseModel):
# #     message: str

# #     class Config:
# #         frozen = True

# # StoryManagerResult = Result[GameState, StoryManagerError]

# # class StoryManager(BaseModel):
# #     card_system_state: CardSystemState
# #     current_game_state: GameState # This would be the output of the graph, or the input to the next step
# #     dm_agent: LangchainDMCore # This agent will be part of a graph node

# #     class Config:
# #         frozen = True
# #         arbitrary_types_allowed = True

# #     def initialize_story(self, story_background_id: str, dm_profile_id: str, player_ids: list[str]) -> StoryManagerResult:
# #         # ... logic to load initial cards, set up initial GameState ...
# #         # This would now involve preparing the initial GraphOrchestratorState
# #         initial_game_state = GameState(...) # Simplified
# #         # Create a new StoryManager instance with this initial state, or rather, the graph would manage this state.
# #         return Success(self.model_copy(update={"current_game_state": initial_game_state}))

# #     def process_player_action(self, player_id: str, action_description: str) -> StoryManagerResult:
# #         # 1. Parse action_description into PlayerAction (using player_module)
# #         # player_action_result = parse_player_text_input(PlayerId(id=player_id), action_description)
# #         # if player_action_result.is_failure:
# #         #     return Failure(StoryManagerError(message=str(player_action_result.failure())))
# #         # parsed_action = player_action_result.unwrap()

# #         # 2. Run the graph with current_game_state and parsed_action
# #         # graph_result_gs = self._run_graph_step(self.current_game_state, parsed_action)
# #         # if graph_result_gs.is_failure:
# #         #     return Failure(graph_result_gs.failure())
# #         # new_game_state = graph_result_gs.unwrap()
# #         # return Success(self.model_copy(update={"current_game_state": new_game_state}))
# #         pass

# #     # _run_graph_step would encapsulate the graph.invoke() or graph.stream() call.

# # Your existing file has a good start for StoryManager, which can be adapted to be the
# # primary interface that prepares input for the LangGraph and processes its output.
