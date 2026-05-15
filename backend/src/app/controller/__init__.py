from fastapi import APIRouter

from .vocalization_controller import router as vocalization_router

router = APIRouter()

router.include_router(vocalization_router)
