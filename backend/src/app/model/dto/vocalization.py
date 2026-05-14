from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class VocalizationCreateDTO(BaseModel):
    speaker: str = Field(..., min_length=1)
    record_date: datetime
    location: str = Field(..., min_length=1)
    vocalization: str = Field(..., min_length=1)
    comment: str = Field(default="")


class VocalizationUpdateDTO(BaseModel):
    speaker: Optional[str] = Field(default=None, min_length=1)
    record_date: Optional[datetime] = None
    location: Optional[str] = Field(default=None, min_length=1)
    vocalization: Optional[str] = Field(default=None, min_length=1)
    comment: Optional[str] = None
    validated: Optional[bool] = None

    @model_validator(mode="after")
    def validate_not_null_fields(self):
        for field in ["speaker", "record_date", "location", "vocalization"]:
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class VocalizationReadDTO(BaseModel):
    id: Optional[int] = None
    speaker: Optional[str] = None
    record_date: Optional[datetime] = None
    location: Optional[str] = None
    vocalization: Optional[str] = None
    audio_file: Optional[str] = None
    comment: Optional[str] = None
    validated: Optional[bool] = None
    url: Optional[str] = None

    model_config = {"from_attributes": True}
