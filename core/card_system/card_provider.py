# Loads, validates, and provides access to cards
# import yaml # or json
# from pathlib import Path
# from typing import List, Dict
# from .base_card import BaseCard

import yaml
from pathlib import Path
from typing import List, Dict, Optional, Union, Any, Tuple
from pydantic import (
    ValidationError as PydanticValidationError,
    # BaseModel, # No longer needed directly here for model definitions
    # Field,   # No longer needed directly here for model definitions
)
from returns.maybe import Maybe
from returns.result import Result, Success, Failure
from functools import reduce  # For later use in load_cards_from_directory

from .card_base_model import BaseCard, CardType
from .card_errors_model import (
    FileReadError,
    YAMLParseError,
    CardStructureError,
    CardValidationError,
    DuplicateCardIdError,
    CardLoadingError,
)
from .card_reports_model import CardLoadingReport
from .card_state_model import CardSystemState


# Error Types # (All moved to card_errors.py)
# Report Type # (Moved to card_reports.py)
# State Model # (Moved to card_models.py)


# --- Functional Implementation ---


def create_card_system_state(card_data_root_dir: Union[str, Path]) -> CardSystemState:
    """Initializes a new, empty CardSystemState."""
    root_dir = Path(card_data_root_dir)
    if not root_dir.is_dir():
        print(
            f"Warning: Card data directory {root_dir} does not exist or is not a directory."
        )
    return CardSystemState(
        card_data_root_dir=root_dir,
        cards={},
        cards_by_type={ct: tuple() for ct in CardType},
    )


def add_successful_card_to_state(
    card: BaseCard, current_state: CardSystemState, current_report: CardLoadingReport
) -> Tuple[CardSystemState, CardLoadingReport]:
    """
    Adds a successfully parsed card, returning new state and report instances.
    """
    # For cards dictionary (Dict is mutable, so we create a new one)
    new_cards = current_state.cards.copy()
    new_cards[card.card_id] = card

    # For cards_by_type dictionary (values are Tuples, so create new tuple)
    new_cards_by_type = current_state.cards_by_type.copy()
    current_type_list = list(new_cards_by_type.get(card.card_type, tuple()))
    current_type_list.append(card)
    new_cards_by_type[card.card_type] = tuple(current_type_list)

    updated_state = current_state.model_copy(
        update={"cards": new_cards, "cards_by_type": new_cards_by_type}
    )
    updated_report = current_report.model_copy(
        update={
            "cards_successfully_parsed": current_report.cards_successfully_parsed + 1
        }
    )
    return updated_state, updated_report


def add_error_to_loading_report(
    error: CardLoadingError, current_report: CardLoadingReport
) -> CardLoadingReport:
    """
    Adds a loading error, returning a new report instance.
    """
    new_errors = current_report.errors + (error,)  # Append to tuple

    update_fields = {"errors": new_errors}
    match error:
        case FileReadError():
            update_fields["files_with_read_errors"] = (
                current_report.files_with_read_errors + 1
            )
        case YAMLParseError():
            update_fields["files_with_yaml_errors"] = (
                current_report.files_with_yaml_errors + 1
            )
        case CardStructureError():
            update_fields["card_data_structure_errors"] = (
                current_report.card_data_structure_errors + 1
            )
        case CardValidationError():
            update_fields["card_validation_errors"] = (
                current_report.card_validation_errors + 1
            )
        case DuplicateCardIdError():
            update_fields["card_duplicate_id_errors"] = (
                current_report.card_duplicate_id_errors + 1
            )

    return current_report.copy(update=update_fields)


def read_file_content(path: Path) -> Result[str, FileReadError]:
    """Reads the content of a file, returning Result with FileReadError on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return Success(f.read())
    except IOError as e:
        return Failure(FileReadError(path=path, error=str(e)))


def parse_yaml_documents(
    content: str, file_path: Path
) -> Result[List[Any], YAMLParseError]:
    """Parses YAML content into a list of documents, returning Result with YAMLParseError on failure."""
    try:
        if not content.strip():
            return Success([])  # No documents to parse
        documents = list(yaml.safe_load_all(content))
        # Filter out None documents that safe_load_all might produce
        return Success([doc for doc in documents if doc is not None])
    except yaml.YAMLError as e:
        return Failure(YAMLParseError(path=file_path, error=str(e)))


def process_card_data(
    card_data: Dict[str, Any],
    file_path: Path,
    existing_card_ids: Dict[str, BaseCard],  # Changed from existing_cards for clarity
    item_index: Optional[int] = None,
) -> Result[BaseCard, Union[CardValidationError, DuplicateCardIdError]]:
    """
    Validates and creates a BaseCard from raw dictionary data.
    Returns Result with CardValidationError or DuplicateCardIdError on failure.
    """
    try:
        # Pydantic's model_validate handles this better if BaseCard is a Pydantic model
        # Assuming BaseCard might still raise PydanticValidationError directly or via a custom validator
        card = BaseCard(**card_data)
    except PydanticValidationError as e:
        return Failure(
            CardValidationError(
                path=file_path,
                card_name=card_data.get("name"),
                errors=str(e),
                item_index=item_index,
            )
        )
    except (
        Exception
    ) as e:  # Catch any other unexpected error during BaseCard instantiation
        return Failure(
            CardValidationError(
                path=file_path,
                card_name=card_data.get("name"),
                errors=f"Unexpected error creating card object: {str(e)}",
                item_index=item_index,
            )
        )

    if card.card_id in existing_card_ids:
        existing_card = existing_card_ids[card.card_id]
        return Failure(
            DuplicateCardIdError(
                path=file_path,
                card_id=card.card_id,
                new_card_name=card.name,
                existing_card_name=existing_card.name,
                item_index=item_index,
            )
        )
    return Success(card)


def _process_single_card_item_pure(
    card_data_item: Any,
    file_path: Path,
    current_state: CardSystemState,
    current_report: CardLoadingReport,
    item_idx: Optional[int] = None,
) -> Tuple[CardSystemState, CardLoadingReport]:
    """Processes a single card item, returning new state and report."""
    if not isinstance(card_data_item, dict):
        error = CardStructureError(
            path=file_path,
            message=(
                "Card data item is not a dictionary."
                if item_idx is None
                else f"Card item in list (index {item_idx}) is not a dictionary."
            ),
            item_index=item_idx,
            data_type_found=type(card_data_item).__name__,
        )
        return current_state, add_error_to_loading_report(error, current_report)

    # process_card_data itself does not mutate state, but needs existing_card_ids for validation
    card_processing_result: Result[
        BaseCard, Union[CardValidationError, DuplicateCardIdError]
    ] = process_card_data(
        card_data_item, file_path, current_state.cards, item_index=item_idx
    )

    match card_processing_result:
        case Success(card):
            return add_successful_card_to_state(card, current_state, current_report)
        case Failure(error):  # CardValidationError or DuplicateCardIdError
            return current_state, add_error_to_loading_report(error, current_report)


def _process_parsed_documents_pure(
    raw_yaml_documents: List[Any],
    file_path: Path,
    initial_state: CardSystemState,
    initial_report: CardLoadingReport,
) -> Tuple[CardSystemState, CardLoadingReport]:
    """Processes a list of raw YAML documents, accumulating state and report immutably."""

    current_state, current_report = initial_state, initial_report

    if not raw_yaml_documents:
        # No error, but nothing to process further for this file.
        # Increment yaml_documents_processed if it were mutable, but report is immutable.
        # This is tricky. The count should probably be done in the calling function (_process_file_for_fold)
        # Or, we update the report here if docs were found, even if empty after filtering.
        # Let's assume for now that yaml_documents_processed is updated *before* calling this
        # if raw_yaml_documents is not empty initially (before potential filtering in parse_yaml_documents).
        # For simplicity, if the list is empty here, we just return current state/report.
        return current_state, current_report

    # If we reach here, docs were present. Update report for processed docs count.
    # This count update should be done carefully. parse_yaml_documents already filters Nones.
    # The original logic incremented yaml_documents_processed by len(raw_yaml_documents) if not empty.
    # Let's defer this to _process_file_for_fold which has the result of parse_yaml_documents
    # before this function is called.

    for doc_idx, raw_data_doc in enumerate(raw_yaml_documents):
        match raw_data_doc:
            case list() as card_list:
                for item_idx, card_data_item in enumerate(card_list):
                    current_state, current_report = _process_single_card_item_pure(
                        card_data_item,
                        file_path,
                        current_state,
                        current_report,
                        item_idx=item_idx,
                    )
            case dict() as card_dict:
                current_state, current_report = _process_single_card_item_pure(
                    card_dict, file_path, current_state, current_report
                )
            case _:
                error = CardStructureError(
                    path=file_path,
                    message=f"YAML document (index {doc_idx}) is not a list or dictionary.",
                    data_type_found=type(raw_data_doc).__name__,
                )
                current_report = add_error_to_loading_report(error, current_report)
    return current_state, current_report


def _process_file_for_fold(
    accumulator: Tuple[CardSystemState, CardLoadingReport], file_path: Path
) -> Tuple[CardSystemState, CardLoadingReport]:
    current_state, current_report = accumulator

    def handle_successful_parse(
        docs: List[Any],
    ) -> Tuple[CardSystemState, CardLoadingReport]:
        report_after_counting_docs = current_report
        if docs:
            report_after_counting_docs = current_report.model_copy(
                update={
                    "yaml_documents_processed": current_report.yaml_documents_processed
                    + len(docs)
                }
            )
        return _process_parsed_documents_pure(
            docs, file_path, current_state, report_after_counting_docs
        )

    # Modified to return Result, specifically Success, as alt expects it.
    def handle_parse_failure(
        error: Union[FileReadError, YAMLParseError],
    ) -> Result[Tuple[CardSystemState, CardLoadingReport], Any]:
        # current_state remains unchanged, only report is updated.
        # The error type for the Result here is nominal as we always return Success.
        return Success(
            (current_state, add_error_to_loading_report(error, current_report))
        )

    # The chain now always results in Success(Tuple[State, Report]), so unwrap() is safe.
    return (
        read_file_content(file_path)
        .bind(lambda content: parse_yaml_documents(content, file_path))
        .map(handle_successful_parse)
        .alt(handle_parse_failure)
        .unwrap()  # Changed from unwrap_or to unwrap, as the chain now ensures Success
    )


def load_cards_from_directory(
    card_data_root_dir: Union[str, Path],
) -> Tuple[CardSystemState, CardLoadingReport]:
    """
    Loads all cards from YAML files using a pure functional approach with immutable updates.
    Returns a tuple of the populated CardSystemState and a CardLoadingReport.
    """
    initial_state = create_card_system_state(card_data_root_dir)
    # Initialize report with files_attempted, other counts start at 0

    if not initial_state.card_data_root_dir.is_dir():
        # No files to attempt, return initial empty state and a basic report
        return initial_state, CardLoadingReport()

    yaml_files = list(initial_state.card_data_root_dir.rglob("*.yaml")) + list(
        initial_state.card_data_root_dir.rglob("*.yml")
    )

    if not yaml_files:
        print(
            f"No YAML files found in {initial_state.card_data_root_dir} or its subdirectories."
        )
        # No files to attempt, return initial empty state and a basic report
        return initial_state, CardLoadingReport(files_attempted=0)

    # Initialize report with files_attempted
    initial_report = CardLoadingReport(files_attempted=len(yaml_files))

    # Use functools.reduce to fold over yaml_files
    final_state, final_report = reduce(
        _process_file_for_fold, yaml_files, (initial_state, initial_report)
    )

    summary_message = (
        f"Card loading complete. Report summary:\\n"
        f"  Files Attempted: {final_report.files_attempted}\\n"
        f"  YAML Documents Processed: {final_report.yaml_documents_processed}\\n"
        f"  Cards Successfully Parsed: {final_report.cards_successfully_parsed}\\n"
        f"  Total Errors Encountered: {final_report.total_errors_encountered}\\n"
        f"    - File Read Errors: {final_report.files_with_read_errors}\\n"
        f"    - YAML Parse Errors: {final_report.files_with_yaml_errors}\\n"
        f"    - Card Data Structure Errors: {final_report.card_data_structure_errors}\\n"
        f"    - Card Validation Errors: {final_report.card_validation_errors}\\n"
        f"    - Duplicate Card ID Errors: {final_report.card_duplicate_id_errors}"
    )
    print(summary_message)
    if final_report.errors:
        print("See report.errors for detailed error information.")

    return final_state, final_report


# --- Accessor Functions ---


def get_card_by_id(state: CardSystemState, card_id: str) -> Maybe[BaseCard]:
    """Retrieves a card by its ID from the state."""
    return Maybe.from_optional(state.cards.get(card_id))


def get_all_cards(state: CardSystemState) -> List[BaseCard]:
    """Retrieves all loaded cards from the state."""
    return list(state.cards.values())


def get_cards_by_type(state: CardSystemState, card_type: CardType) -> List[BaseCard]:
    """Retrieves all cards of a specific type from the state."""
    return list(state.cards_by_type.get(card_type, tuple()))


def get_card_system_stats_summary(
    state: CardSystemState, report: CardLoadingReport
) -> Dict[str, Any]:
    """Provides a concise summary of the current card system state and last load report."""
    return {
        "card_data_root": str(state.card_data_root_dir),
        "total_cards_in_memory": len(state.cards),
        "card_types_present_count": len(
            [ct for ct, cards_list in state.cards_by_type.items() if cards_list]
        ),
        "last_load_files_attempted": report.files_attempted,
        "last_load_successful_cards": report.cards_successfully_parsed,
        "last_load_total_errors": report.total_errors_encountered,
    }


# Example Usage (adapted for functional and immutable approach)
if __name__ == "__main__":
    print("Setting up dummy card data for CardManager Functional V4 testing...")
    dummy_root = Path("./dummy_game_data_card_manager_v4")
    dummy_root.mkdir(exist_ok=True)

    import shutil

    for item in dummy_root.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink(missing_ok=True)

    story_bg_dir = dummy_root / "story_backgrounds"
    story_bg_dir.mkdir(exist_ok=True)
    npc_dir = dummy_root / "world_elements" / "npcs"
    npc_dir.mkdir(parents=True, exist_ok=True)
    items_dir = dummy_root / "world_elements" / "items"
    items_dir.mkdir(parents=True, exist_ok=True)
    factions_dir = dummy_root / "world_elements" / "factions"
    factions_dir.mkdir(parents=True, exist_ok=True)

    # Valid Card 1 (Single card in file)
    with open(story_bg_dir / "ancient_ruins.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "card_type": "STORY_BACKGROUND",
                "name": "The Ancient Ruins of Eldoria",
                "description": "A sprawling complex, lost to time.",
                "tags": ["exploration", "mystery"],
                "metadata": {"era": "Pre-Cataclysm"},
            },
            f,
        )
    # Valid Cards (List of cards in file, one with explicit ID)
    with open(npc_dir / "common_npcs.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            [
                {
                    "card_id": "npc-guard-001",
                    "card_type": "NPC",
                    "name": "Guard Captain Rex",
                    "description": "Stern city watch captain.",
                    "tags": ["guard"],
                    "metadata": {"level": 5},
                },
                {
                    "card_type": "NPC",
                    "name": "Mysterious Merchant Sylvia",
                    "description": "Sells rare goods.",
                    "tags": ["merchant"],
                    "version": "1.1.0",
                },
            ],
            f,
        )
    # Duplicate ID Card
    with open(npc_dir / "duplicate_npc.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "card_id": "npc-guard-001",
                "card_type": "NPC",
                "name": "Guard Impostor",
                "description": "Not the real captain.",
            },
            f,
        )
    # File with one valid, one invalid (missing 'name'), one structurally incorrect
    with open(story_bg_dir / "mixed_quality.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            [
                {
                    "card_type": "STORY_BACKGROUND",
                    "name": "Whispering Woods",
                    "description": "Dark forest.",
                },
                {
                    "card_type": "STORY_BACKGROUND",
                    "description": "Oasis without a name.",
                },
                "just_a_string_not_a_card_dict",
            ],
            f,
            Dumper=yaml.Dumper,
        )
    # Invalid YAML file
    with open(dummy_root / "malformed_card.yaml", "w", encoding="utf-8") as f:
        f.write(
            "valid_key_in_first_doc: valid_value\\n---\\nanother_key:\\n\\t- this_is_a_tab_indent_error"
        )
    # Semantically invalid card (tags not a list)
    with open(items_dir / "invalid_tags_item.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "card_type": "ITEM",
                "name": "Magic Sword",
                "description": "Blade.",
                "tags": "not-a-list",
            },
            f,
        )
    # Card with a non-existent CardType string
    with open(items_dir / "invalid_enum_item.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "card_type": "NON_EXISTENT_TYPE",
                "name": "Typo Item",
                "description": "Bad type.",
            },
            f,
        )
    # File with only comments or empty
    with open(dummy_root / "empty.yaml", "w", encoding="utf-8") as f:
        f.write("# This file is empty\\n---\\n# Another empty doc")
    # Valid Faction Card
    with open(factions_dir / "shadow_syndicate.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "card_type": "FACTION",
                "name": "The Shadow Syndicate",
                "description": "A clandestine organization.",
                "tags": ["secretive", "criminal"],
                "metadata": {"influence_level": "moderate"},
            },
            f,
        )

    print(f"Dummy data created in {dummy_root.resolve()}")

    print("Initializing Card System and Loading cards (pure functional approach)...")
    # Call the refactored loader, which returns the final state and report
    final_card_state, final_loading_report = load_cards_from_directory(dummy_root)

    print("--- Card Loading Report --- ")
    print(f"  Files Attempted: {final_loading_report.files_attempted}")
    print(f"  YAML Docs Processed: {final_loading_report.yaml_documents_processed}")
    print(
        f"  Cards Successfully Parsed: {final_loading_report.cards_successfully_parsed}"
    )
    print(f"  Total Errors: {final_loading_report.total_errors_encountered}")
    if final_loading_report.errors:
        # Print a few errors for brevity
        for i, error in enumerate(final_loading_report.errors[:3]):
            print(f"  Error {i+1}: {error}")
        if len(final_loading_report.errors) > 3:
            print(f"  ... and {len(final_loading_report.errors) - 3} more errors.")

    print("--- Stats from get_card_system_stats_summary() ---")
    stats = get_card_system_stats_summary(final_card_state, final_loading_report)
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').capitalize()}: {value}")

    print("--- All Successfully Loaded Cards ---")
    all_loaded_cards = get_all_cards(final_card_state)
    if all_loaded_cards:
        for card in all_loaded_cards:
            print(f"  ID: {card.card_id}, Type: {card.card_type}, Name: {card.name}")
    else:
        print("  No cards were successfully loaded.")

    print("--- Story Backgrounds (using get_cards_by_type) ---")
    story_bg_list = get_cards_by_type(final_card_state, CardType.STORY_BACKGROUND)
    if story_bg_list:
        for bg in story_bg_list:
            print(f"  Story Background: {bg.name} (ID: {bg.card_id})")
    else:
        print("  No Story Backgrounds found or loaded.")

    print("--- NPCs (using get_cards_by_type) ---")
    npcs_list = get_cards_by_type(final_card_state, CardType.NPC)
    if npcs_list:
        for n in npcs_list:
            print(f"  NPC: {n.name} (ID: {n.card_id})")
    else:
        print("  No NPCs found or loaded.")

    print("--- Factions (New Type Test) ---")
    factions_list = get_cards_by_type(final_card_state, CardType.FACTION)
    if factions_list:
        for faction in factions_list:
            print(
                f"  Faction: {faction.name} (ID: {faction.id if hasattr(faction, 'id') else faction.card_id})"
            )
    else:
        print("  No Factions found or loaded.")

    print("--- Retrieving a specific card (npc-guard-001) using Maybe ---")
    get_card_by_id(final_card_state, "npc-guard-001").map(
        lambda card: print(f"  Found: {card.name}, Desc: {card.description}")
    ).or_else_call(lambda: print("  Card npc-guard-001 not found."))

    print("--- Retrieving a non-existent card using Maybe ---")
    get_card_by_id(final_card_state, "i-do-not-exist").map(
        lambda card: print(f"  Found: {card.name}")
    ).or_else_call(lambda: print("  Card i-do-not-exist not found, as expected."))

    print("--- Inspecting some specific errors from the report --- ")
    for error_instance in final_loading_report.errors:
        if isinstance(error_instance, DuplicateCardIdError):
            print(f"  DETECTED DUPLICATE: {error_instance}")
        elif (
            isinstance(error_instance, CardValidationError)
            and error_instance.card_name == "Typo Item"
        ):
            print(f"  DETECTED INVALID ENUM/TYPE: {error_instance}")
        elif isinstance(
            error_instance, YAMLParseError
        ) and "malformed_card.yaml" in str(error_instance.path):
            print(f"  DETECTED YAML PARSE ERROR: {error_instance}")

    if dummy_root.exists():
        shutil.rmtree(dummy_root)
        print(f"Cleaned up dummy directory: {dummy_root}")
    print("CardManager Functional V4 test complete.")
