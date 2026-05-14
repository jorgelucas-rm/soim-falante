import random
import re
import string
import time

from fastapi import Depends, UploadFile

from src.app.adapter import MinioAdapter
from src.app.model.dto import (
    Pagination,
    VocalizationCreateDTO,
    VocalizationReadDTO,
    VocalizationUpdateDTO,
)
from src.app.model.entity import Vocalization
from src.app.repository.vocalization_repository import VocalizationRepository
from src.infra.exception import NotFoundException

_VOCALIZATIONS_PATH = "vocalizations"


class VocalizationService:
    """Serviço responsável pelo gerenciamento de vocalizações, incluindo upload/download via MinIO."""

    def __init__(
        self,
        vocalization_repository: VocalizationRepository,
        minio_adapter: MinioAdapter,
    ):
        self.vocalization_repository = vocalization_repository
        self.minio_adapter = minio_adapter

    def get_all_vocalizations_paginated(
        self,
        page: int = 1,
        page_size: int = 10,
        order_by: str | None = None,
        order_direction: str | None = None,
        filters: dict | None = None,
    ) -> Pagination[VocalizationReadDTO]:
        """Retorna página de vocalizações com suporte a filtros e ordenação."""
        vocalizations, total, total_filtered = self.vocalization_repository.get_paginated(
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_direction=order_direction,
            filters=filters,
        )

        items = self._to_read_dtos(vocalizations)
        total_pages = (total_filtered + page_size - 1) // page_size

        return Pagination[VocalizationReadDTO](
            items=items,
            total=total,
            total_filtered=total_filtered,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_vocalization_by_id(self, vocalization_id: int) -> Vocalization:
        """Retorna a entidade pelo ID; lança NotFoundException se não encontrada."""
        vocalization = self.vocalization_repository.get_by_pk(pk=vocalization_id)

        if not vocalization:
            raise NotFoundException(resource="Vocalization")

        return vocalization

    def get_vocalization_view_by_id(self, vocalization_id: int) -> VocalizationReadDTO:
        """Retorna o DTO da vocalização com URL pré-assinada do MinIO."""
        vocalization = self.get_vocalization_by_id(vocalization_id)
        return self._to_read_dto(vocalization)

    def create_vocalization(self, dto: VocalizationCreateDTO, file: UploadFile) -> VocalizationReadDTO:
        """Faz upload do áudio no MinIO e registra a vocalização no banco."""
        file_name = self._generate_file_name(file.filename or "audio")
        object_name = self.build_object_name(file_name)
        self.minio_adapter.upload_file_to_minio(file=file, object_name=object_name)

        vocalization = Vocalization(**dto.model_dump(), audio_file=file_name)
        saved = self.vocalization_repository.save(entity=vocalization)
        return self._to_read_dto(saved)

    def update_vocalization(self, vocalization_id: int, dto: VocalizationUpdateDTO) -> VocalizationReadDTO:
        """Atualiza os metadados da vocalização."""
        vocalization = self.get_vocalization_by_id(vocalization_id)

        for field, value in dto.model_dump(exclude_unset=True).items():
            setattr(vocalization, field, value)

        saved = self.vocalization_repository.save(entity=vocalization)
        return self._to_read_dto(saved)

    def replace_audio_file(self, vocalization_id: int, file: UploadFile) -> VocalizationReadDTO:
        """Substitui o arquivo de áudio no MinIO."""
        vocalization = self.get_vocalization_by_id(vocalization_id)

        previous_object_name = self.build_object_name(vocalization.audio_file)

        file_name = self._generate_file_name(file.filename or "audio")
        object_name = self.build_object_name(file_name)
        self.minio_adapter.upload_file_to_minio(file=file, object_name=object_name)

        vocalization.audio_file = file_name
        saved = self.vocalization_repository.save(entity=vocalization)

        self.minio_adapter.delete_file_from_minio(previous_object_name)

        return self._to_read_dto(saved)

    def validate_vocalization(self, vocalization_id: int) -> VocalizationReadDTO:
        """Marca a vocalização como validada (validated=True)."""
        return self._update_validated(vocalization_id=vocalization_id, validated=True)

    def invalidate_vocalization(self, vocalization_id: int) -> VocalizationReadDTO:
        """Marca a vocalização como não validada (validated=False)."""
        return self._update_validated(vocalization_id=vocalization_id, validated=False)

    def delete_vocalization(self, vocalization_id: int) -> None:
        """Remove a vocalização e o arquivo de áudio do MinIO."""
        vocalization = self.get_vocalization_by_id(vocalization_id)
        object_name = self.build_object_name(vocalization.audio_file)
        self.minio_adapter.delete_file_from_minio(object_name)
        self.vocalization_repository.delete(entity=vocalization)

    def _update_validated(self, vocalization_id: int, validated: bool) -> VocalizationReadDTO:
        vocalization = self.get_vocalization_by_id(vocalization_id=vocalization_id)
        vocalization.validated = validated
        saved = self.vocalization_repository.save(entity=vocalization)
        return self._to_read_dto(saved)

    def _to_read_dto(self, vocalization: Vocalization) -> VocalizationReadDTO:
        object_name = self.build_object_name(vocalization.audio_file)
        url = self.minio_adapter.get_file_from_minio(object_name)
        return VocalizationReadDTO.model_validate(vocalization).model_copy(update={"url": url})

    def _to_read_dtos(self, vocalizations: list[Vocalization]) -> list[VocalizationReadDTO]:
        object_names = [self.build_object_name(v.audio_file) for v in vocalizations]
        urls = self.minio_adapter.get_files_from_minio(object_names)
        return [
            VocalizationReadDTO.model_validate(v).model_copy(update={"url": urls.get(name)})
            for v, name in zip(vocalizations, object_names)
        ]

    @staticmethod
    def build_object_name(file_name: str) -> str:
        return f"{_VOCALIZATIONS_PATH}/{file_name}"

    @staticmethod
    def _generate_file_name(base_name: str) -> str:
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", base_name)
        random_string = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        return f"{sanitized}_{int(time.time())}_{random_string}"

    @staticmethod
    def get_service(
        vocalization_repository: VocalizationRepository = Depends(
            VocalizationRepository.get_instance(),
        ),
        minio_adapter: MinioAdapter = Depends(MinioAdapter.get_instance),
    ) -> "VocalizationService":
        return VocalizationService(
            vocalization_repository=vocalization_repository,
            minio_adapter=minio_adapter,
        )
