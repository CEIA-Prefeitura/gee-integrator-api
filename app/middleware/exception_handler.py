from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from jose import JWTError
from app.config import logger


def _error_response(status_code: int, error: str, detalhes: str | list | None = None):
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "detalhes": detalhes},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"[VALIDATION] {exc.errors()}")
    return _error_response(422, "Erro de validação", exc.errors())


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"[HTTP] {exc.status_code} - {exc.detail}")
    return _error_response(exc.status_code, str(exc.detail))


async def jwt_exception_handler(request: Request, exc: JWTError):
    logger.warning(f"[JWT] {str(exc)}")
    return _error_response(401, "Token inválido", str(exc))


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"[{type(exc).__name__}] {repr(exc)}")
    return _error_response(exc.status_code, str(exc.detail))


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(JWTError, jwt_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
