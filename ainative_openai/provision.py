"""
Auto-provisioning for AINative API keys.

Provisions a free API key via the instant-db endpoint, saves it to
``~/.ainative/config.json``, and prints a claim URL so the user can
convert the temporary key into a permanent one.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

INSTANT_DB_URL = "https://api.ainative.studio/api/v1/public/instant-db"
CONFIG_DIR = Path.home() / ".ainative"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    """Load saved config from ``~/.ainative/config.json``."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_config(data: dict) -> None:
    """Save config to ``~/.ainative/config.json``."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("Could not save config to %s: %s", CONFIG_FILE, exc)


def load_saved_key() -> Optional[str]:
    """Return the API key from ``~/.ainative/config.json`` if present."""
    config = _load_config()
    return config.get("api_key")


def provision() -> str:
    """
    Auto-provision a free AINative API key via the instant-db endpoint.

    The key is saved to ``~/.ainative/config.json`` and the claim URL is
    printed so the user can convert to a permanent key.

    Returns:
        The provisioned API key.

    Raises:
        RuntimeError: If provisioning fails.
    """
    logger.info("Auto-provisioning AINative API key via instant-db...")
    try:
        resp = requests.post(
            INSTANT_DB_URL,
            json={"agree_terms": True},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        api_key = data.get("api_key") or data.get("key")
        if not api_key:
            raise ValueError(
                f"No api_key in instant-db response: {list(data.keys())}"
            )

        claim_url = data.get("claim_url", "https://ainative.studio/claim")
        project_id = data.get("project_id", "")

        # Save to config
        config = _load_config()
        config["api_key"] = api_key
        if project_id:
            config["project_id"] = project_id
        config["claim_url"] = claim_url
        _save_config(config)

        # Print claim URL so user knows how to keep the key
        print(
            f"\n  AINative API key auto-provisioned (free tier, 72h expiry).\n"
            f"  Claim for permanent access: {claim_url}\n"
            f"  Config saved to: {CONFIG_FILE}\n"
        )

        return api_key

    except Exception as exc:
        raise RuntimeError(
            "Failed to auto-provision AINative API key. "
            "Set AINATIVE_API_KEY or sign up at https://ainative.studio\n"
            f"Error: {exc}"
        ) from exc
