import logging
import uuid
from typing import Optional

import requests
from sqlalchemy.orm import Session

from src.config import settings
from src.models import APIProvider, User, UserKey
from src.secrets.vault_factory import get_vault

logger = logging.getLogger(__name__)

LITELLM_API_URL = settings.litellm_url


def retrieve_litellm_master_key():
    return settings.litellm_master_key


def regenerate_litellm_master_key():
    logger.info("Regenerating LiteLLM master key...")

    new_key = f"sk-proj-{uuid.uuid4()}"

    # Try to store in vault, but continue even if vault is unavailable
    vault = get_vault()
    vault_path = vault.store_api_key_in_vault(
        settings.litellm_master_key_vault_path, new_key
    )
    if vault_path:
        logger.info(f"LiteLLM master key stored in Vault at path: {vault_path}")
    else:
        logger.warning("Vault unavailable, LiteLLM master key could not be stored")

    # Tell litellm about the new master key
    try:
        requests.post(
            f"{LITELLM_API_URL}/key/regenerate",
            headers={"Authorization": f"Bearer {settings.litellm_master_key}"},
            json={"key": settings.litellm_master_key, "new_master_key": new_key},
            timeout=15,
        )
        logger.info("LiteLLM master key regenerated successfully")
    except Exception as e:
        logger.error(f"Failed to regenerate LiteLLM master key: {e}")

    logger.info(f"new LiteLLM master key: {new_key}")


def retrieve_litellm_key_for_user(user: User, db: Session) -> Optional[str]:
    """
    Retrieves the LiteLLM key for a user.
    """
    user_key = (
        db.query(UserKey)
        .filter(UserKey.user_id == user.id, UserKey.provider == APIProvider.LITELLM)
        .first()
    )

    if user_key:
        vault = get_vault()
        api_key = vault.retrieve_api_key_from_vault(user_key.vault_path)
        if api_key is None:
            logger.warning(
                f"Could not retrieve LiteLLM key for user {user.id} - vault unavailable"
            )
        return api_key

    return None


def get_litellm_user_info(user: User, master_key: str) -> dict:
    """
    Retrieves the LiteLLM user info for a user.
    """
    response = requests.get(
        f"{LITELLM_API_URL}/user/info?user_id={user.id}",
        headers={
            "Authorization": f"Bearer {master_key}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise ValueError(
            f"Failed to get user info from LiteLLM, status code: {response.status_code}, response: {response.text}"
        )

    return response.json()


def create_litellm_user(user: User, master_key: str) -> str:
    """
    Creates a new LiteLLM user.

    Returns:
        str: The new LiteLLM key
    """
    response = requests.post(
        f"{LITELLM_API_URL}/user/new",
        headers={"Authorization": f"Bearer {master_key}"},
        json={"user_id": str(user.id)},
        timeout=30,
    )

    if response.status_code != 200:
        raise ValueError(
            f"Failed to create user in LiteLLM. Status code: {response.status_code}, response: {response.text}"
        )

    data = response.json()
    new_key = data["key"]

    if not new_key:
        raise ValueError(
            f"Failed to create user in LiteLLM. Status code: {response.status_code}, response: {response.text}"
        )

    return new_key
