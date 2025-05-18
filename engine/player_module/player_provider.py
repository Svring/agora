from returns.result import Result, Success, Failure
from core.card_system.card_base_model import BaseCard

from .player_models import (
    PlayerId,
    PlayerState,
    PlayerAction,
    PlayerActionParseError,
    MoveAction,
    SpeakAction,
    UseItemAction,
    GeneralAction,
)


def create_player_state(
    player_id: PlayerId, archetype_card: BaseCard
) -> Result[PlayerState, str]:
    """Initializes a PlayerState from an archetype card."""
    if archetype_card.card_type != "PLAYER_ARCHETYPE":
        return Failure(f"Card '{archetype_card.name}' is not a PLAYER_ARCHETYPE card.")
    try:
        player_name = archetype_card.name
        initial_stats = archetype_card.metadata.get("initial_stats", {})
        return Success(
            PlayerState(
                player_id=player_id,
                name=player_name,
                archetype_card_id=archetype_card.card_id,
                player_stats=initial_stats,
            )
        )
    except Exception as e:
        return Failure(
            f"Error creating player state from card {archetype_card.card_id}: {str(e)}"
        )


def parse_player_text_input(
    player_id: PlayerId, text_input: str
) -> Result[PlayerAction, PlayerActionParseError]:
    """Parses raw text input into a structured PlayerAction.
    Expected format: "action_type: payload"
    e.g., "speak: Hello there to npc_bartender"
    """
    parts = text_input.split(":", 1)
    if len(parts) != 2:
        return Failure(
            PlayerActionParseError(
                message='Invalid input format. Expected "action_type: payload".',
                raw_input=text_input,
                reason="Missing or misplaced ':' separator",
            )
        )

    command = parts[0].lower().strip()
    payload_str = parts[1].strip()
    payload_parts = payload_str.lower().split()

    if not command:
        return Failure(
            PlayerActionParseError(
                message="Action type cannot be empty.",
                raw_input=text_input,
                reason="Empty action type",
            )
        )

    if not payload_str and command not in ["general"]:
        if command in ["move", "use"]:
            return Failure(
                PlayerActionParseError(
                    message=f"Payload for '{command}' action cannot be empty.",
                    raw_input=text_input,
                    reason="Empty payload for action",
                )
            )

    if command == "move":
        if not payload_parts:
            return Failure(
                PlayerActionParseError(
                    message="Move action requires a location ID.",
                    raw_input=text_input,
                    reason="Missing location ID in payload",
                )
            )
        return Success(
            MoveAction(player_id=player_id, target_location_id=payload_parts[0])
        )

    elif command == "speak":
        if not payload_str:
            return Failure(
                PlayerActionParseError(
                    message="Speak action requires a message.",
                    raw_input=text_input,
                    reason="Empty message payload for speak",
                )
            )

        message_parts_from_payload = payload_parts
        final_message_parts = message_parts_from_payload
        target_npc_id = None

        if (
            len(message_parts_from_payload) >= 2
            and message_parts_from_payload[-2] == "to"
        ):
            potential_message_parts = message_parts_from_payload[:-2]

            if not potential_message_parts:
                return Failure(
                    PlayerActionParseError(
                        message="Speak action requires message content before 'to <target_id>'.",
                        raw_input=text_input,
                        reason="Empty message when 'to <target_id>' is used",
                    )
                )
            else:
                final_message_parts = potential_message_parts
                target_npc_id = message_parts_from_payload[-1]

        message = " ".join(final_message_parts)

        if not message.strip():
            return Failure(
                PlayerActionParseError(
                    message="Speak action message cannot be empty.",
                    raw_input=text_input,
                    reason="Final message content is empty after parsing",
                )
            )

        return Success(
            SpeakAction(
                player_id=player_id, message=message, target_npc_id=target_npc_id
            )
        )

    elif command == "use":
        if not payload_parts:
            return Failure(
                PlayerActionParseError(
                    message="Use action requires an item ID.",
                    raw_input=text_input,
                    reason="Missing item ID in payload",
                )
            )

        item_card_id = payload_parts[0]
        target_id = None
        if len(payload_parts) >= 3 and payload_parts[1] == "on":
            item_card_id = payload_parts[0]
            target_id = payload_parts[2]
        elif len(payload_parts) == 1:
            item_card_id = payload_parts[0]
        elif "on" in payload_parts:
            item_card_id = payload_parts[0]

        return Success(
            UseItemAction(
                player_id=player_id, item_card_id=item_card_id, target_id=target_id
            )
        )

    elif command == "general":
        return Success(GeneralAction(player_id=player_id, description=payload_str))

    else:
        return Failure(
            PlayerActionParseError(
                message=f"Unknown action type: '{command}'.",
                raw_input=text_input,
                reason="Unknown action type prefix",
            )
        )


if __name__ == "__main__":
    import uuid

    class MockCardType:
        PLAYER_ARCHETYPE = "PLAYER_ARCHETYPE"
        ITEM = "ITEM"

    print("--- Running Player Provider Tests (New Format) ---")

    def get_test_player_id() -> PlayerId:
        return PlayerId(id=uuid.uuid4())

    # --- Tests for create_player_state (these remain structurally the same) ---
    def test_create_player_state_success():
        print("Test: create_player_state_success")
        player_id = get_test_player_id()
        archetype_card = BaseCard(
            card_id="arch_warrior_001",
            card_type=MockCardType.PLAYER_ARCHETYPE,
            name="Test Warrior",
            description="A brave warrior archetype.",
            metadata={"initial_stats": {"strength": 10, "health": 100}},
        )
        result = create_player_state(player_id, archetype_card)
        assert isinstance(result, Success)
        player_state = result.unwrap()
        assert isinstance(player_state, PlayerState)
        assert player_state.player_id == player_id
        assert player_state.name == "Test Warrior"
        assert player_state.archetype_card_id == archetype_card.card_id
        assert player_state.player_stats == {"strength": 10, "health": 100}
        print("PASS: create_player_state_success")

    def test_create_player_state_success_no_initial_stats():
        print("Test: create_player_state_success_no_initial_stats")
        player_id = get_test_player_id()
        archetype_card = BaseCard(
            card_id="arch_rogue_001",
            card_type=MockCardType.PLAYER_ARCHETYPE,
            name="Test Rogue",
            description="A stealthy rogue archetype.",
        )
        result = create_player_state(player_id, archetype_card)
        assert isinstance(result, Success)
        player_state = result.unwrap()
        assert isinstance(player_state, PlayerState)
        assert player_state.name == "Test Rogue"
        assert player_state.player_stats == {}
        print("PASS: create_player_state_success_no_initial_stats")

    def test_create_player_state_failure_wrong_card_type():
        print("Test: create_player_state_failure_wrong_card_type")
        player_id = get_test_player_id()
        item_card = BaseCard(
            card_id="item_sword_001",
            card_type=MockCardType.ITEM,
            name="Sword of Testing",
            description="A test item.",
        )
        result = create_player_state(player_id, item_card)
        assert isinstance(result, Failure)
        assert "not a PLAYER_ARCHETYPE card" in result.failure()
        print("PASS: create_player_state_failure_wrong_card_type")

    # --- Tests for parse_player_text_input (NEW FORMAT) ---
    def test_parse_move_action_success():
        print("Test: parse_move_action_success (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "move: location_castle_main_hall")
        assert isinstance(result, Success)
        action = result.unwrap()
        assert isinstance(action, MoveAction)
        assert action.player_id == player_id
        assert action.action_type == "MOVE"
        assert action.target_location_id == "location_castle_main_hall"
        print("PASS: parse_move_action_success (new format)")

    def test_parse_move_action_failure_empty_payload():
        print("Test: parse_move_action_failure_empty_payload (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "move: ")
        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PlayerActionParseError)
        assert error.reason == "Empty payload for action"
        print("PASS: parse_move_action_failure_empty_payload (new format)")

    def test_parse_speak_action_success_simple():
        print("Test: parse_speak_action_success_simple (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "speak: Hello there friend")
        assert isinstance(result, Success)
        action = result.unwrap()
        assert isinstance(action, SpeakAction)
        assert action.message == "hello there friend"
        assert action.target_npc_id is None
        print("PASS: parse_speak_action_success_simple (new format)")

    def test_parse_speak_action_success_with_target():
        print("Test: parse_speak_action_success_with_target (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(
            player_id, "speak: Greetings brave knight to npc_king_arthur"
        )
        assert isinstance(result, Success)
        action = result.unwrap()
        assert isinstance(action, SpeakAction)
        assert action.message == "greetings brave knight"
        assert action.target_npc_id == "npc_king_arthur"
        print("PASS: parse_speak_action_success_with_target (new format)")

    def test_parse_speak_action_success_to_in_message():
        print("Test: parse_speak_action_success_to_in_message (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "speak: I want to go to the market")
        assert isinstance(result, Success)
        action = result.unwrap()
        assert isinstance(action, SpeakAction)
        assert action.message == "i want to go to the market"
        assert action.target_npc_id is None
        print("PASS: parse_speak_action_success_to_in_message (new format)")

    def test_parse_speak_action_failure_empty_payload():
        print("Test: parse_speak_action_failure_empty_payload (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "speak:")
        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PlayerActionParseError)
        assert error.reason == "Empty message payload for speak"
        print("PASS: parse_speak_action_failure_empty_payload (new format)")

    def test_parse_speak_action_failure_only_target():
        print("Test: parse_speak_action_failure_only_target (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "speak: to npc_bartender")
        assert isinstance(result, Failure), f"Expected Failure, got {result}"
        error = result.failure()
        assert isinstance(error, PlayerActionParseError)
        assert error.reason == "Empty message when 'to <target_id>' is used"
        print("PASS: parse_speak_action_failure_only_target (new format)")

    def test_parse_use_item_action_success_simple():
        print("Test: parse_use_item_action_success_simple (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "use: item_health_potion")
        assert isinstance(result, Success)
        action = result.unwrap()
        assert isinstance(action, UseItemAction)
        assert action.item_card_id == "item_health_potion"
        assert action.target_id is None
        print("PASS: parse_use_item_action_success_simple (new format)")

    def test_parse_use_item_action_success_with_target():
        print("Test: parse_use_item_action_success_with_target (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(
            player_id, "use: item_key_01 on door_main_gate"
        )
        assert isinstance(result, Success)
        action = result.unwrap()
        assert isinstance(action, UseItemAction)
        assert action.item_card_id == "item_key_01"
        assert action.target_id == "door_main_gate"
        print("PASS: parse_use_item_action_success_with_target (new format)")

    def test_parse_use_item_action_failure_empty_payload():
        print("Test: parse_use_item_action_failure_empty_payload (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "use:")
        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PlayerActionParseError)
        assert error.reason == "Empty payload for action"
        print("PASS: parse_use_item_action_failure_empty_payload (new format)")

    def test_parse_general_action_success():
        print("Test: parse_general_action_success (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(
            player_id, "general: Look around the room for clues"
        )
        assert isinstance(result, Success)
        action = result.unwrap()
        assert isinstance(action, GeneralAction)
        assert action.action_type == "GENERAL"
        assert action.description == "Look around the room for clues"
        print("PASS: parse_general_action_success (new format)")

    def test_parse_general_action_empty_payload_success():
        print("Test: parse_general_action_empty_payload_success (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "general:")
        assert isinstance(result, Success), f"Expected Success, got {result}"
        action = result.unwrap()
        assert isinstance(action, GeneralAction)
        assert action.action_type == "GENERAL"
        assert action.description == ""
        print("PASS: parse_general_action_empty_payload_success (new format)")

    def test_parse_invalid_format_no_colon():
        print("Test: parse_invalid_format_no_colon (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "move location_castle")
        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PlayerActionParseError)
        assert error.reason == "Missing or misplaced ':' separator"
        print("PASS: parse_invalid_format_no_colon (new format)")

    def test_parse_empty_action_type():
        print("Test: parse_empty_action_type (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, ": some payload")
        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PlayerActionParseError)
        assert error.reason == "Empty action type"
        print("PASS: parse_empty_action_type (new format)")

    def test_parse_unknown_action_type():
        print("Test: parse_unknown_action_type (new format)")
        player_id = get_test_player_id()
        result = parse_player_text_input(player_id, "fly: to the moon")
        assert isinstance(result, Failure)
        error = result.failure()
        assert isinstance(error, PlayerActionParseError)
        assert error.reason == "Unknown action type prefix"
        print("PASS: parse_unknown_action_type (new format)")

    # Call test functions
    test_create_player_state_success()
    test_create_player_state_success_no_initial_stats()
    test_create_player_state_failure_wrong_card_type()

    test_parse_move_action_success()
    test_parse_move_action_failure_empty_payload()

    test_parse_speak_action_success_simple()
    test_parse_speak_action_success_with_target()
    test_parse_speak_action_success_to_in_message()
    test_parse_speak_action_failure_empty_payload()
    test_parse_speak_action_failure_only_target()

    test_parse_use_item_action_success_simple()
    test_parse_use_item_action_success_with_target()
    test_parse_use_item_action_failure_empty_payload()

    test_parse_general_action_success()
    test_parse_general_action_empty_payload_success()

    test_parse_invalid_format_no_colon()
    test_parse_empty_action_type()
    test_parse_unknown_action_type()

    print("\n--- All Player Provider Tests (New Format) Complete ---")
