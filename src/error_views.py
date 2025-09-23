import logging

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.responses import Response as StarletteResponse

from src.main import app, templates

logger = logging.getLogger(__name__)


@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    # Check if the request path starts with /api/ - if so, let it pass through
    if request.url.path.startswith("/api/") or request.url.path.startswith("/billing/"):
        # For API routes, return JSON error responses
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    logger.error(f"handling auth exception: {exc}")

    # For non-API routes, apply the original HTML error handling
    redirect_error_codes = [401, 403, 404]
    if exc.status_code in redirect_error_codes:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse(
        request,
        "pages/error_500.html",
        {"request": request, "status_code": exc.status_code, "detail": exc.detail},
        status_code=500,
    )


@app.exception_handler(404)
async def not_found_exception_handler(
    request: Request, exc: Exception
) -> StarletteResponse:
    # Check if the request path starts with /api/ - if so, let it pass through
    if request.url.path.startswith("/api/") or request.url.path.startswith("/billing/"):
        # For API routes, return JSON error responses
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    # For non-API routes, return HTML error page
    return templates.TemplateResponse(
        request, "pages/error_404.html", {"request": request}, status_code=404
    )


# === Test endpoints ===


@app.get("/test-internal-server-error", response_class=HTMLResponse)
async def test_internal_server_error(request: Request):
    raise HTTPException(status_code=500, detail="Internal Server Error")
