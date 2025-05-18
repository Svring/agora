from typing import Optional, Dict, Any
from pydantic import NonNegativeInt

from .narrative_models import (
    NarrativeEvent,
    NarrativeSourceType,
    NarrativeType,
)

# from engine.player_module.player_models import PlayerId # If strong typing for IDs is enforced later


# Private helper function to reduce boilerplate
def _create_narrative_event(
    source_type: NarrativeSourceType,
    narrative_type: NarrativeType,
    content: str,
    source_id: Optional[str] = None,
    target_entity_id: Optional[str] = None,
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    visibility_scope: Optional[str] = None,
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Internal helper to construct NarrativeEvent instances."""
    return NarrativeEvent(
        source_type=source_type,
        source_id=source_id,
        narrative_type=narrative_type,
        content=content,
        target_entity_id=target_entity_id,
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=narrative_payload,
        metadata=metadata if metadata is not None else {},
    )


# --- Public API Functions ---


def create_scene_description_event(
    content: str,
    source_id: str = "DM",  # Default to DM, can be SYSTEM
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    visibility_scope: Optional[str] = "ALL",
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Creates a SCENE_DESCRIPTION narrative event."""
    return _create_narrative_event(
        source_type=NarrativeSourceType.DM,  # Or SYSTEM based on actual source
        narrative_type=NarrativeType.SCENE_DESCRIPTION,
        content=content,
        source_id=source_id,
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=narrative_payload,
        metadata=metadata,
    )


def create_npc_dialogue_event(
    npc_id: str,  # ID of the NPC speaking
    content: str,
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    target_player_id: Optional[
        str
    ] = None,  # If dialogue is directed to a specific player
    visibility_scope: Optional[str] = "ALL",
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Creates an NPC_DIALOGUE narrative event."""
    return _create_narrative_event(
        source_type=NarrativeSourceType.DM,  # Assuming DM orchestrates NPC dialogue
        source_id=npc_id,  # The NPC is the conceptual source
        narrative_type=NarrativeType.NPC_DIALOGUE,
        content=content,
        target_entity_id=target_player_id,  # Could also be the npc_id if it's a general statement
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=narrative_payload,
        metadata=metadata,
    )


def create_player_action_result_event(
    player_id: str,
    result_content: str,
    attempted_action_description: Optional[str] = None,
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    visibility_scope: Optional[str] = "PLAYER_ONLY",  # Default for direct feedback
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Creates a PLAYER_ACTION_RESULT narrative event."""
    final_payload = narrative_payload.copy() if narrative_payload else {}
    if attempted_action_description:
        final_payload.update({"attempted_action": attempted_action_description})

    return _create_narrative_event(
        source_type=NarrativeSourceType.SYSTEM,  # System narrates the outcome of player's action
        narrative_type=NarrativeType.PLAYER_ACTION_RESULT,
        content=result_content,
        source_id="SYSTEM",  # Or player_id if system is acting on their direct command prompt
        target_entity_id=player_id,  # The result is pertinent to this player
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=final_payload,
        metadata=metadata,
    )


def create_world_event(
    content: str,
    source_id: str = "SYSTEM",  # Or DM if DM directly causes it
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    visibility_scope: Optional[str] = "ALL",
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Creates a WORLD_EVENT narrative event."""
    return _create_narrative_event(
        source_type=NarrativeSourceType.SYSTEM,  # Or DM
        narrative_type=NarrativeType.WORLD_EVENT,
        content=content,
        source_id=source_id,
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=narrative_payload,
        metadata=metadata,
    )


def create_quest_update_event(
    content: str,
    quest_id: str,
    player_id: Optional[
        str
    ] = None,  # If the update is for a specific player's quest log
    source_id: str = "SYSTEM",  # Or DM
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    visibility_scope: Optional[str] = "ALL",  # Or PLAYER_ONLY if personal
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Creates a QUEST_UPDATE narrative event."""
    final_payload = narrative_payload.copy() if narrative_payload else {}
    final_payload["quest_id"] = quest_id
    if player_id:
        final_payload["player_id"] = player_id  # For context in payload

    return _create_narrative_event(
        source_type=NarrativeSourceType.SYSTEM,  # Or DM
        narrative_type=NarrativeType.QUEST_UPDATE,
        content=content,
        source_id=source_id,
        target_entity_id=player_id,  # Event is primarily relevant to this player if specified
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=final_payload,
        metadata=metadata,
    )


def create_lore_discovery_event(
    player_id: str,
    lore_content: str,
    lore_card_id: Optional[str] = None,
    source_id: str = "SYSTEM",  # System reveals lore
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    visibility_scope: Optional[str] = "PLAYER_ONLY",  # Usually personal discovery
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Creates a LORE_DISCOVERY narrative event."""
    final_payload = narrative_payload.copy() if narrative_payload else {}
    if lore_card_id:
        final_payload["lore_card_id"] = lore_card_id

    return _create_narrative_event(
        source_type=NarrativeSourceType.SYSTEM,
        narrative_type=NarrativeType.LORE_DISCOVERY,
        content=lore_content,
        source_id=source_id,
        target_entity_id=player_id,
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=final_payload,
        metadata=metadata,
    )


def create_system_message_event(
    content: str,
    target_player_id: Optional[str] = None,
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    visibility_scope: Optional[str] = "ALL",
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Creates a SYSTEM_MESSAGE narrative event."""
    return _create_narrative_event(
        source_type=NarrativeSourceType.SYSTEM,
        narrative_type=NarrativeType.SYSTEM_MESSAGE,
        content=content,
        source_id="SYSTEM",
        target_entity_id=target_player_id,
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=narrative_payload,
        metadata=metadata,
    )


def create_error_narration_event(
    player_id: str,
    error_message_content: str,
    attempted_action_description: Optional[str] = None,
    location_id: Optional[str] = None,
    turn_number: Optional[NonNegativeInt] = None,
    visibility_scope: Optional[str] = "PLAYER_ONLY",
    narrative_payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NarrativeEvent:
    """Creates an ERROR_NARRATION narrative event (e.g. action failure)."""
    final_payload = narrative_payload.copy() if narrative_payload else {}
    if attempted_action_description:
        final_payload["attempted_action"] = attempted_action_description

    return _create_narrative_event(
        source_type=NarrativeSourceType.SYSTEM,
        narrative_type=NarrativeType.ERROR_NARRATION,
        content=error_message_content,
        source_id="SYSTEM",
        target_entity_id=player_id,
        location_id=location_id,
        turn_number=turn_number,
        visibility_scope=visibility_scope,
        narrative_payload=final_payload,
        metadata=metadata,
    )


__all__ = [
    "create_scene_description_event",
    "create_npc_dialogue_event",
    "create_player_action_result_event",
    "create_world_event",
    "create_quest_update_event",
    "create_lore_discovery_event",
    "create_system_message_event",
    "create_error_narration_event",
]

if __name__ == "__main__":
    import uuid
    from datetime import datetime

    def test_create_scene_description_event():
        print("Test: create_scene_description_event")
        event = create_scene_description_event(
            content="The sun sets over the misty mountains.",
            location_id="loc_mountain_peak",
            turn_number=10,
            metadata={"weather": "clear"},
        )
        assert isinstance(event, NarrativeEvent)
        assert event.narrative_type == NarrativeType.SCENE_DESCRIPTION
        assert event.source_type == NarrativeSourceType.DM
        assert event.content == "The sun sets over the misty mountains."
        assert event.location_id == "loc_mountain_peak"
        assert event.turn_number == 10
        assert event.visibility_scope == "ALL"
        assert event.metadata == {"weather": "clear"}
        print("PASS: create_scene_description_event")

    def test_create_npc_dialogue_event():
        print("Test: create_npc_dialogue_event")
        event = create_npc_dialogue_event(
            npc_id="npc_bartender_bob",
            content="Welcome to the Prancing Pony!",
            target_player_id="player_frodo",
            turn_number=5,
        )
        assert isinstance(event, NarrativeEvent)
        assert event.narrative_type == NarrativeType.NPC_DIALOGUE
        assert event.source_type == NarrativeSourceType.DM
        assert event.source_id == "npc_bartender_bob"
        assert event.content == "Welcome to the Prancing Pony!"
        assert event.target_entity_id == "player_frodo"
        assert event.turn_number == 5
        print("PASS: create_npc_dialogue_event")

    def test_create_player_action_result_event():
        print("Test: create_player_action_result_event")
        event = create_player_action_result_event(
            player_id="player_aragorn",
            result_content="You successfully pick the lock.",
            attempted_action_description="Tried to pick the chest lock",
            location_id="loc_dungeon_cell_3",
            turn_number=12,
        )
        assert isinstance(event, NarrativeEvent)
        assert event.narrative_type == NarrativeType.PLAYER_ACTION_RESULT
        assert event.source_type == NarrativeSourceType.SYSTEM
        assert event.target_entity_id == "player_aragorn"
        assert event.content == "You successfully pick the lock."
        assert event.narrative_payload == {
            "attempted_action": "Tried to pick the chest lock"
        }
        assert event.visibility_scope == "PLAYER_ONLY"
        print("PASS: create_player_action_result_event")

    def test_create_world_event():
        print("Test: create_world_event")
        event = create_world_event(
            content="A distant dragon roars, echoing through the valley.",
            source_id="SYSTEM_WEATHER_ENGINE",  # Example custom source
            turn_number=15,
        )
        assert isinstance(event, NarrativeEvent)
        assert event.narrative_type == NarrativeType.WORLD_EVENT
        assert event.source_type == NarrativeSourceType.SYSTEM
        assert event.source_id == "SYSTEM_WEATHER_ENGINE"
        assert event.content == "A distant dragon roars, echoing through the valley."
        print("PASS: create_world_event")

    def test_create_quest_update_event():
        print("Test: create_quest_update_event")
        event = create_quest_update_event(
            content="Quest 'Find the Lost Sword' updated: Speak to the Elder.",
            quest_id="quest_lost_sword_001",
            player_id="player_legolas",
            turn_number=20,
            visibility_scope="PLAYER_ONLY",
        )
        assert isinstance(event, NarrativeEvent)
        assert event.narrative_type == NarrativeType.QUEST_UPDATE
        assert event.target_entity_id == "player_legolas"
        assert event.narrative_payload == {
            "quest_id": "quest_lost_sword_001",
            "player_id": "player_legolas",
        }
        assert event.visibility_scope == "PLAYER_ONLY"
        print("PASS: create_quest_update_event")

    def test_create_lore_discovery_event():
        print("Test: create_lore_discovery_event")
        event = create_lore_discovery_event(
            player_id="player_gandalf",
            lore_content="You decipher the ancient runes. They speak of a hidden power.",
            lore_card_id="lore_ancient_runes_001",
            turn_number=22,
        )
        assert isinstance(event, NarrativeEvent)
        assert event.narrative_type == NarrativeType.LORE_DISCOVERY
        assert event.target_entity_id == "player_gandalf"
        assert event.narrative_payload == {"lore_card_id": "lore_ancient_runes_001"}
        print("PASS: create_lore_discovery_event")

    def test_create_system_message_event():
        print("Test: create_system_message_event")
        event = create_system_message_event(
            content="It is now Player Gimli's turn.",
            target_player_id="player_gimli",
            turn_number=25,
        )
        assert isinstance(event, NarrativeEvent)
        assert event.narrative_type == NarrativeType.SYSTEM_MESSAGE
        assert event.target_entity_id == "player_gimli"
        assert event.content == "It is now Player Gimli's turn."
        print("PASS: create_system_message_event")

    def test_create_error_narration_event():
        print("Test: create_error_narration_event")
        event = create_error_narration_event(
            player_id="player_samwise",
            error_message_content="You try to lift the heavy boulder, but it doesn't budge.",
            attempted_action_description="Lift boulder",
            turn_number=30,
        )
        assert isinstance(event, NarrativeEvent)
        assert event.narrative_type == NarrativeType.ERROR_NARRATION
        assert event.target_entity_id == "player_samwise"
        assert (
            event.content == "You try to lift the heavy boulder, but it doesn't budge."
        )
        assert event.narrative_payload == {"attempted_action": "Lift boulder"}
        print("PASS: create_error_narration_event")

    print("\n--- Running Narrative Provider Tests ---")
    test_create_scene_description_event()
    test_create_npc_dialogue_event()
    test_create_player_action_result_event()
    test_create_world_event()
    test_create_quest_update_event()
    test_create_lore_discovery_event()
    test_create_system_message_event()
    test_create_error_narration_event()
    print("--- Narrative Provider Tests Complete ---\n")
