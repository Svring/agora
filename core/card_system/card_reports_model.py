from pydantic import BaseModel, Field
from typing import Tuple

from .card_errors_model import CardLoadingError


# Report Type
class CardLoadingReport(BaseModel):
    files_attempted: int = 0
    yaml_documents_processed: int = 0
    cards_successfully_parsed: int = 0
    files_with_read_errors: int = 0
    files_with_yaml_errors: int = 0
    card_data_structure_errors: int = 0
    card_validation_errors: int = 0
    card_duplicate_id_errors: int = 0
    errors: Tuple[CardLoadingError, ...] = Field(default_factory=tuple)

    @property
    def total_errors_encountered(self) -> int:
        return (
            self.files_with_read_errors
            + self.files_with_yaml_errors
            + self.card_data_structure_errors
            + self.card_validation_errors
            + self.card_duplicate_id_errors
        )

    class Config:
        arbitrary_types_allowed = True  # Though not strictly needed here, keep for consistency if it was in original
        frozen = True
