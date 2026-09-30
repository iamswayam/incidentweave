"""FastAPI application entry point for IncidentWeave."""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import router as api_router

app = FastAPI(title="IncidentWeave")
app.include_router(api_router)


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Return a consistent error shape without exposing request internals."""

    del request
    if isinstance(exc.detail, dict):
        code = str(exc.detail.get("code") or "http_error")
        message = str(exc.detail.get("message") or "The request could not be completed.")
    else:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = (
            "The requested resource was not found."
            if exc.status_code == 404
            else "The request could not be completed."
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Hide validation internals behind the documented API error shape."""

    del request, exc
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
            }
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Avoid returning internal or credential-bearing exception text."""

    del request, exc
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An internal error occurred.",
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Return a minimal application health response."""

    return {"status": "ok"}
