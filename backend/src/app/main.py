from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from src.app.controller import router
from src.infra.exception.exception_handler import global_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="API - Soim Falante", version="0.1")

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, global_exception_handler)
app.add_exception_handler(RequestValidationError, global_exception_handler)

app.include_router(router=router, prefix="/api")


@app.get("/api")
async def get_root():
    return "v0.1"
