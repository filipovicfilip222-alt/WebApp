"""Auth endpoints for Keycloak redirect flow and current user lookup."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.config import settings
from app.schemas_module import KeycloakUserInfo
from app.services import get_current_user

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _keycloak_authorize_url(redirect_uri: str) -> str:
    params = urlencode(
        {
            "client_id": settings.keycloak_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
            "kc_idp_hint": "",
        }
    )
    return f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/auth?{params}"


@router.get("/sso/redirect")
async def sso_redirect(request: Request):
    redirect_uri = str(request.url_for("sso_callback"))
    return RedirectResponse(_keycloak_authorize_url(redirect_uri), status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/sso/callback", name="sso_callback")
async def sso_callback(code: str | None = None, state: str | None = None):
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="studentska_demo_login",
        value="authenticated",
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout():
    logout_url = (
        f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
        "/protocol/openid-connect/logout"
    )
    response = RedirectResponse(logout_url, status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("studentska_demo_login")
    return response


@router.get("/me", response_model=KeycloakUserInfo)
async def me(user: KeycloakUserInfo = Depends(get_current_user)):
    return user
