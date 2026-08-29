"""Consistent JSON error envelope for every non-2xx response.

FastAPI's defaults return ``{"detail": "..."}`` for HTTPException and
``{"detail": [{loc, msg, type}, ...]}`` for validation failures - two different
shapes a client has to special-case. Every error from this API instead looks like:

    {"error": {"code": "not_found", "message": "Project not found"}}

with an optional ``details`` list on validation errors:

    {"error": {"code": "validation_error", "message": "Request validation failed",
               "details": [{"field": "email", "message": "value is not a valid email address"}]}}
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_CODES: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
    status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
}


def error_response(
    status_code: int,
    message: str,
    details: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    code = _CODES.get(status_code, "http_error")
    body: dict[str, dict] = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        # Preserve e.g. WWW-Authenticate on 401s.
        return error_response(exc.status_code, message, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_exception(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                # loc is ("body", "password") or ("query", "sort_by"); drop the location prefix.
                "field": ".".join(str(part) for part in err["loc"][1:]) or str(err["loc"][0]),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Request validation failed", details=details
        )
