# Token utility functions

import datetime
from typing import Dict, Union

import jwt
import requests

from src.config import settings
from src.models import User


def renew_jwt(refresh_token: Union[str, None]) -> Dict[str, str]:
    if refresh_token is None:
        return {"error": "No refresh token available"}

    response = requests.post(
        f"https://{settings.auth0_domain}/oauth/token",
        json={
            "grant_type": "refresh_token",
            "client_id": settings.auth0_client_id,
            "client_secret": settings.auth0_client_secret,
            "refresh_token": refresh_token,
        },
        headers={"content-type": "application/json"},
        timeout=settings.internal_request_timeout,
    )

    # Consider adding error handling here (e.g., check response.status_code)
    return response.json()
