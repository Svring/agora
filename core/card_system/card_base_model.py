# Pydantic base model for all cards
from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, Any, Optional, Tuple
import uuid


class CardType(str, Enum):
    """Enumeration for different types of cards."""

    STORY_BACKGROUND = "STORY_BACKGROUND"
    DM_PROFILE = "DM_PROFILE"
    PLAYER_ARCHETYPE = "PLAYER_ARCHETYPE"
    NPC = "NPC"
    ITEM = "ITEM"
    LOCATION = "LOCATION"
    EVENT = "EVENT"
    ABILITY = "ABILITY"
    LORE = "LORE"
    GAME_RULE = "GAME_RULE"
    FACTION = "FACTION"  # New card type
    CUSTOM = "CUSTOM"  # For user-defined or highly specific cards


class BaseCard(BaseModel):
    """
    Pydantic base model for all cards in the system.
    This model defines the common structure for any card.
    """

    card_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the card, typically a UUID.",
    )
    card_type: CardType = Field(
        ..., description="The type of the card, drawn from the CardType enum."
    )
    name: str = Field(..., min_length=1, description="Human-readable name of the card.")
    description: str = Field(
        ...,
        description="A textual description of the card's purpose, content, or effect.",
    )
    tags: Optional[Tuple[str, ...]] = Field(
        default_factory=tuple,
        description="A tuple of tags for categorization and searchability.",
    )
    version: str = Field(
        default="1.0.0", description="Version of the card data format or content."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Flexible field for additional, card-specific data not covered by common fields.",
    )
    # Future considerations might include:
    # - created_at: datetime = Field(default_factory=datetime.utcnow)
    # - updated_at: datetime = Field(default_factory=datetime.utcnow)
    # - created_by: Optional[str] = None (e.g. user ID or system process)
    # - visibility_rules: Optional[Dict[str, Any]] = None # Or link to a separate visibility system

    class Config:
        frozen = True
        use_enum_values = True
        extra = "forbid"
