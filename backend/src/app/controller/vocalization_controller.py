from datetime import datetime

from fastapi import APIRouter, Body, Depends, File, Form, Path, Query, UploadFile

from src.app.controller.dependencies import get_filters
from src.app.model.dto import (
    Pagination,
    Response,
    VocalizationCreateDTO,
    VocalizationReadDTO,
    VocalizationUpdateDTO,
)
from src.app.model.enum import HttpCode
from src.app.service.vocalization_service import VocalizationService

router = APIRouter(prefix="/vocalizations", tags=["Vocalizations"])


@router.get(
    "",
    response_model=Response[Pagination[VocalizationReadDTO]],
    status_code=HttpCode.OK,
)
async def list_vocalizations(
    service: VocalizationService = Depends(VocalizationService.get_service),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=1000),
    order_by: str | None = Query(None),
    order_direction: str | None = Query(None),
    filters: dict = Depends(get_filters),
):
    return Response(
        code=HttpCode.OK,
        message="Vocalizations retrieved successfully",
        data=service.get_all_vocalizations_paginated(
            page=page,
            page_size=size,
            order_by=order_by,
            order_direction=order_direction,
            filters=filters,
        ),
    )


@router.get(
    "/{vocalization_id}",
    response_model=Response[VocalizationReadDTO],
    status_code=HttpCode.OK,
)
async def get_vocalization(
    service: VocalizationService = Depends(VocalizationService.get_service),
    vocalization_id: int = Path(..., ge=1),
):
    return Response(
        code=HttpCode.OK,
        message="Vocalization retrieved successfully",
        data=service.get_vocalization_view_by_id(vocalization_id=vocalization_id),
    )


@router.post(
    "",
    response_model=Response[VocalizationReadDTO],
    status_code=HttpCode.CREATED,
)
async def create_vocalization(
    service: VocalizationService = Depends(VocalizationService.get_service),
    speaker: str = Form(..., min_length=1),
    record_date: datetime = Form(...),
    location: str = Form(..., min_length=1),
    vocalization: str = Form(..., min_length=1),
    comment: str = Form(default=""),
    file: UploadFile = File(...),
):
    dto = VocalizationCreateDTO(
        speaker=speaker,
        record_date=record_date,
        location=location,
        vocalization=vocalization,
        comment=comment,
    )
    result = service.create_vocalization(dto=dto, file=file)
    return Response(
        code=HttpCode.CREATED,
        message="Vocalization created successfully",
        data=result,
    )


@router.put(
    "/{vocalization_id}",
    response_model=Response[VocalizationReadDTO],
    status_code=HttpCode.OK,
)
async def update_vocalization(
    service: VocalizationService = Depends(VocalizationService.get_service),
    vocalization_id: int = Path(..., ge=1),
    dto: VocalizationUpdateDTO = Body(...),
):
    result = service.update_vocalization(vocalization_id=vocalization_id, dto=dto)
    return Response(
        code=HttpCode.OK,
        message="Vocalization updated successfully",
        data=result,
    )


@router.patch(
    "/{vocalization_id}/audio",
    response_model=Response[VocalizationReadDTO],
    status_code=HttpCode.OK,
)
async def replace_audio(
    service: VocalizationService = Depends(VocalizationService.get_service),
    vocalization_id: int = Path(..., ge=1),
    file: UploadFile = File(...),
):
    result = service.replace_audio_file(vocalization_id=vocalization_id, file=file)
    return Response(
        code=HttpCode.OK,
        message="Audio file replaced successfully",
        data=result,
    )


@router.patch(
    "/{vocalization_id}/validate",
    response_model=Response[VocalizationReadDTO],
    status_code=HttpCode.OK,
)
async def validate_vocalization(
    service: VocalizationService = Depends(VocalizationService.get_service),
    vocalization_id: int = Path(..., ge=1),
):
    result = service.validate_vocalization(vocalization_id=vocalization_id)
    return Response(
        code=HttpCode.OK,
        message="Vocalization validated successfully",
        data=result,
    )


@router.patch(
    "/{vocalization_id}/invalidate",
    response_model=Response[VocalizationReadDTO],
    status_code=HttpCode.OK,
)
async def invalidate_vocalization(
    service: VocalizationService = Depends(VocalizationService.get_service),
    vocalization_id: int = Path(..., ge=1),
):
    result = service.invalidate_vocalization(vocalization_id=vocalization_id)
    return Response(
        code=HttpCode.OK,
        message="Vocalization invalidated successfully",
        data=result,
    )


@router.delete(
    "/{vocalization_id}",
    status_code=HttpCode.NO_CONTENT,
)
async def delete_vocalization(
    service: VocalizationService = Depends(VocalizationService.get_service),
    vocalization_id: int = Path(..., ge=1),
):
    service.delete_vocalization(vocalization_id=vocalization_id)
