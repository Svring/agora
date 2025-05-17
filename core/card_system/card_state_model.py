from pydantic import BaseModel, Field
from pathlib import Path
from typing import Dict, Tuple

from .card_base_model import BaseCard, CardType  # Assuming CardType is in base_card
from .card_reports_model import CardLoadingReport


# State Model
class CardSystemState(BaseModel):
    card_data_root_dir: Path
    cards: Dict[str, BaseCard] = Field(default_factory=dict)
    cards_by_type: Dict[CardType, Tuple[BaseCard, ...]] = Field(
        default_factory=lambda: {card_type: tuple() for card_type in CardType}
    )
    last_loading_report: CardLoadingReport = Field(default_factory=CardLoadingReport)

    class Config:
        arbitrary_types_allowed = True
        frozen = True
