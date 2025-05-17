from pydantic import BaseModel
from pathlib import Path
from typing import Optional, Union


# Error Types
class FileReadError(BaseModel):
    path: Path
    error: str

    class Config:
        arbitrary_types_allowed = True
        frozen = True


class YAMLParseError(BaseModel):
    path: Path
    error: str

    class Config:
        arbitrary_types_allowed = True
        frozen = True


class CardStructureError(BaseModel):
    path: Path
    message: str
    item_index: Optional[int] = None
    data_type_found: str = ""

    class Config:
        arbitrary_types_allowed = True
        frozen = True


class CardValidationError(BaseModel):
    path: Path
    card_name: Optional[str] = None
    errors: str  # Pydantic's error summary
    item_index: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True
        frozen = True


class DuplicateCardIdError(BaseModel):
    path: Path
    card_id: str
    new_card_name: str
    existing_card_name: str
    item_index: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True
        frozen = True


CardLoadingError = Union[
    FileReadError,
    YAMLParseError,
    CardStructureError,
    CardValidationError,
    DuplicateCardIdError,
]
