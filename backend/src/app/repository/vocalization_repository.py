from typing import Type

from src.app.model.entity.vocalization import Vocalization
from src.app.repository.base_repository import BaseRepository


class VocalizationRepository(BaseRepository[Vocalization]):

    @property
    def model(self) -> Type[Vocalization]:
        return Vocalization

    @property
    def orderable_fields(self) -> dict:
        return {
            "id": Vocalization.id,
            "speaker": Vocalization.speaker,
            "record_date": Vocalization.record_date,
            "location": Vocalization.location,
            "vocalization": Vocalization.vocalization,
            "comment": Vocalization.comment,
        }

    @property
    def equal_filters(self):
        return {
            "id": Vocalization.id,
            "validated": Vocalization.validated,
        }

    @property
    def like_filters(self) -> dict:
        return {
            "speaker": Vocalization.speaker,
            "location": Vocalization.location,
            "vocalization": Vocalization.vocalization,
            "comment": Vocalization.comment,
        }
