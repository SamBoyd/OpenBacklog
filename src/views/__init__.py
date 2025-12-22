import logging
from urllib.parse import quote_plus, urlencode

from fastapi import Depends, Form, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.orm import Session

from src import controller

# Use the new auth module for authentication
from src.auth import auth_module
from src.auth.tokens import renew_jwt
from src.config import settings
from src.db import get_db
from src.main import app
from src.main import auth_module as main_auth_module
from src.main import templates
from src.models import AccessToken, User

logger = logging.getLogger(__name__)

dependency_to_override = auth_module.require_auth


async def request_logging_dependency(request: Request, db: Session = Depends(get_db)):
    print("--- Request Logging Dependency ---")
    access_token = request.cookies.get("access_token")
    all_cookies = request.cookies
    access_token_db = (
        db.query(AccessToken).filter(AccessToken.token == access_token).first()
    )
    print(f"All cookies received by server: {all_cookies}")
    print(f"Access Token found by logging dependency: {access_token_db}")
    if access_token_db is not None:
        user = db.query(User).filter(User.id == access_token_db.user_id).first()
        print(f"User found by logging dependency: {user}")
    else:
        print("No access token found by logging dependency")

    # Commit the read-only transaction to prevent "idle in transaction" state
    db.commit()


# Healthcheck endpoint
@app.get("/healthcheck", response_class=JSONResponse)
async def healthcheck() -> JSONResponse:
    return JSONResponse(content={"status": "ok"})


# === Routes not requiring being logged in  ===
@app.get("/", response_class=HTMLResponse, response_model=None)
async def serve_react_app(request: Request, db: Session = Depends(get_db)):
    # Check if user is authenticated
    user = await main_auth_module.get_current_user(request, db, None)  # type: ignore

    if not user:
        # User is not authenticated, serve the landing page
        return controller.get_landing_page(request)

    # User is authenticated, redirect to workspace
    return RedirectResponse(url="/workspace", status_code=302)


@app.get("/auth/auth0-logout-callback", response_class=RedirectResponse)
def auth0_logout_callback(request: Request) -> RedirectResponse:
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    response.delete_cookie("auth0_jwt")
    return response


# === Routes requiring being logged in  =======


@app.get("/workspace", response_class=HTMLResponse)
@app.get("/workspace/{rest_of_path:path}", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    _log_trigger: None = Depends(request_logging_dependency),
    user=Depends(dependency_to_override),
) -> HTMLResponse:
    return controller.get_react_app(request, user)


@app.get("/changelog", response_class=HTMLResponse)
async def changelog(
    request: Request, user=Depends(dependency_to_override)
) -> HTMLResponse:
    return controller.get_changelog_template(request, user)


@app.get("/support", response_class=HTMLResponse)
async def support(
    request: Request, user=Depends(dependency_to_override)
) -> HTMLResponse:
    return controller.get_support_template(request, user)


@app.get("/account", response_class=HTMLResponse)
async def account(
    request: Request, user=Depends(dependency_to_override), session=Depends(get_db)
) -> HTMLResponse:
    return controller.get_account_template(request, user, session)


@app.get("/logout", response_class=RedirectResponse)
def logout(request: Request, user=Depends(dependency_to_override)) -> RedirectResponse:
    redirect_url = f"https://{settings.auth0_domain}/v2/logout?" + urlencode(
        {
            "returnTo": f"{settings.app_url}/auth/auth0-logout-callback",
            "client_id": settings.auth0_client_id,
        },
        quote_via=quote_plus,
    )

    response = RedirectResponse(url=redirect_url)
    response.delete_cookie("access_token")
    response.delete_cookie("auth0_jwt")
    response.delete_cookie("refresh_token")
    return response


@app.post("/auth/renew-jwt", response_class=JSONResponse)
def renew_jwt_view(request: Request) -> JSONResponse:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return JSONResponse({"error": "No refresh token available"}, status_code=401)

    new_tokens = renew_jwt(refresh_token)
    response = JSONResponse({})
    response.set_cookie("auth0_jwt", new_tokens["access_token"])
    response.set_cookie("refresh_token", new_tokens["refresh_token"])
    return response


@app.get("/profile-picture/{filename}", response_class=FileResponse)
def get_profile_picture(filename: str) -> FileResponse:
    return controller.get_profile_picture(filename)


@app.post("/upload-profile-picture", response_class=Response)
async def upload_profile_picture(
    request: Request,
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),  # added dependency for db session
) -> Response:
    form = await request.form()
    file = form["file"]
    return controller.upload_profile_picture(user, file, db)


@app.get("/delete-account", response_class=HTMLResponse)
async def delete_account(
    request: Request,
    user=Depends(dependency_to_override),
    csrf_protect: CsrfProtect = Depends(),
) -> HTMLResponse:
    reasons = [
        "Too expensive",
        "Lack of needed features",
        "Complex user interface",
        "Found a better alternative",
        "Privacy concerns",
        "Other",
    ]
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(
        "pages/delete_account.html",
        {
            "request": request,
            "user": user,
            "reasons": reasons,
            "csrf_token": csrf_token,
        },
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@app.post("/confirm-delete-account", response_class=RedirectResponse)
async def confirm_delete_account(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
    reason: str = Form(...),
    csrftoken: str = Form(...),
) -> RedirectResponse:
    try:
        await csrf_protect.validate_csrf(
            request,
            cookie_key=settings.csrf_token_name,
            secret_key=settings.csrf_token_secret_key,
        )
    except Exception as e:
        response = RedirectResponse(url="/account", status_code=302)
        csrf_protect.unset_csrf_cookie(response)  # prevent token reuse
        return response

    controller.confirm_delete_account(user, reason, db)

    response = RedirectResponse(url="/", status_code=302)
    csrf_protect.unset_csrf_cookie(response)
    response.delete_cookie("access_token")
    response.delete_cookie("auth0_jwt")
    response.delete_cookie("refresh_token")
    return response
