from returns.result import Result, Success, Failure

from core.card_system.card_base_model import BaseCard  # Assuming this path is correct
from .player_models import (
    PlayerId,
    PlayerState,
    PlayerAction,
    PlayerActionParseError,
    MoveAction,
    SpeakAction,
    UseItemAction,
)


def create_player_state(
    player_id: PlayerId, archetype_card: BaseCard
) -> Result[PlayerState, str]:
    """Initializes a PlayerState from an archetype card."""
    if (
        archetype_card.card_type != "PLAYER_ARCHETYPE"
    ):  # Define PLAYER_ARCHETYPE in CardType enum
        return Failure(f"Card '{archetype_card.name}' is not a PLAYER_ARCHETYPE card.")

    try:
        player_name = (
            archetype_card.name
        )  # Or a specific field like archetype_card.data.get('character_name')
        initial_stats = archetype_card.metadata.get("initial_stats", {})  # Example
        # Potentially also initial inventory, known_lore from card's metadata or tags

        return Success(
            PlayerState(
                player_id=player_id,
                name=player_name,
                archetype_card_id=archetype_card.card_id,
                player_stats=initial_stats,
                # Initialize other fields as needed from archetype_card
            )
        )
    except Exception as e:
        return Failure(
            f"Error creating player state from card {archetype_card.card_id}: {str(e)}"
        )


def parse_player_text_input(
    player_id: PlayerId, text_input: str
) -> Result[PlayerAction, PlayerActionParseError]:
    """Parses raw text input into a structured PlayerAction."""
    # This is a very basic parser.
    # In a real scenario, this would be much more complex, potentially using NLP/regex or an LLM call.
    # For now, it supports simple commands:
    # "move <location_id>"
    # "speak <message> [to <npc_id>]"
    # "use <item_id> [on <target_id>]"

    parts = text_input.lower().strip().split()
    if not parts:
        return Failure(
            PlayerActionParseError(
                message="Input cannot be empty.",
                raw_input=text_input,
                reason="Empty input",
            )
        )

    command = parts[0]

    if command == "move":
        if len(parts) < 2:
            return Failure(
                PlayerActionParseError(
                    message="Move command requires a location ID.",
                    raw_input=text_input,
                    reason="Missing location ID",
                )
            )
        return Success(MoveAction(player_id=player_id, target_location_id=parts[1]))

    elif command == "speak":
        if len(parts) < 2:
            return Failure(
                PlayerActionParseError(
                    message="Speak command requires a message.",
                    raw_input=text_input,
                    reason="Missing message",
                )
            )

        message_parts = []
        target_npc_id = None

        # Find 'to' keyword to separate message and target_npc_id
        if "to" in parts:
            to_index = parts.index("to")
            if to_index > 1 and to_index < len(parts) - 1:
                message_parts = parts[1:to_index]
                target_npc_id = parts[to_index + 1]
            else:
                message_parts = parts[1:]  # Assume 'to' is part of message or malformed
        else:
            message_parts = parts[1:]

        if not message_parts:
            return Failure(
                PlayerActionParseError(
                    message="Speak command requires a message.",
                    raw_input=text_input,
                    reason="Missing message content after parsing 'to'",
                )
            )

        message = " ".join(message_parts)
        return Success(
            SpeakAction(
                player_id=player_id, message=message, target_npc_id=target_npc_id
            )
        )

    elif command == "use":
        if len(parts) < 2:
            return Failure(
                PlayerActionParseError(
                    message="Use command requires an item ID.",
                    raw_input=text_input,
                    reason="Missing item ID",
                )
            )

        item_card_id = parts[1]
        target_id = None
        if "on" in parts and len(parts) > parts.index("on") + 1:
            on_index = parts.index("on")
            if on_index == 2:  # e.g. use item_id on target_id
                target_id = parts[on_index + 1]
            else:
                # Could be part of item_id or malformed, ignore for now or error
                pass
        return Success(
            UseItemAction(
                player_id=player_id, item_card_id=item_card_id, target_id=target_id
            )
        )

    else:
        return Failure(
            PlayerActionParseError(
                message=f"Unknown command: {command}",
                raw_input=text_input,
                reason="Unknown command",
            )
        )
