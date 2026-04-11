#!/usr/bin/env python3
"""Credential Manager — Secure API key storage and retrieval.

Provides a unified interface for storing and accessing API credentials
using macOS Keychain (via the ``keyring`` library) with automatic fallback
to environment variables.

Storage priority:
    1. macOS Keychain (encrypted, OS-level protection)
    2. Environment variables (less secure, but portable)

Usage::

    from scripts.credential_manager import CredentialManager

    cm = CredentialManager()

    # First-time setup (interactive)
    cm.store("openai", "sk-proj-abcdef...")

    # Runtime retrieval
    api_key = cm.get("openai")

    # Validate all credentials
    report = cm.validate_all()

    # Check rotation schedule
    cm.check_rotation()
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SERVICE_NAME = "autobiography-generator"

CREDENTIAL_REGISTRY: dict[str, dict[str, Any]] = {
    "openai": {
        "keychain_key": "openai-api-key",
        "env_var": "OPENAI_API_KEY",
        "display_name": "OpenAI API Key",
        "pattern": r"^sk-(proj-)?[A-Za-z0-9_-]{20,}$",
        "pattern_description": "starts with 'sk-' or 'sk-proj-' followed by 20+ alphanumeric chars",
        "docs_url": "https://platform.openai.com/api-keys",
        "rotation_days": 90,
    },
    "gemini": {
        "keychain_key": "gemini-api-key",
        "env_var": "GEMINI_API_KEY",
        "display_name": "Gemini API Key",
        "pattern": r"^AIza[A-Za-z0-9_-]{30,}$",
        "pattern_description": "starts with 'AIza' followed by 30+ alphanumeric chars",
        "docs_url": "https://aistudio.google.com/apikey",
        "rotation_days": 90,
    },
    "anthropic": {
        "keychain_key": "anthropic-api-key",
        "env_var": "ANTHROPIC_API_KEY",
        "display_name": "Anthropic API Key",
        "pattern": r"^sk-ant-[A-Za-z0-9_-]{20,}$",
        "pattern_description": "starts with 'sk-ant-' followed by 20+ alphanumeric chars",
        "docs_url": "https://console.anthropic.com/settings/keys",
        "rotation_days": 90,
    },
}

ROTATION_METADATA_KEY_SUFFIX = "-rotation-meta"


# ---------------------------------------------------------------------------
# Keychain backend (lazy import to handle missing dependency gracefully)
# ---------------------------------------------------------------------------


def _keyring_available() -> bool:
    """Check whether the keyring library is importable."""
    try:
        import keyring as _kr  # noqa: F811, F401

        # Verify the backend is functional (not the null backend)
        backend = _kr.get_keyring()
        backend_name = type(backend).__name__
        if "fail" in backend_name.lower() or "null" in backend_name.lower():
            return False
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# CredentialManager
# ---------------------------------------------------------------------------


class CredentialManager:
    """Unified credential access with Keychain-first, env-var-fallback strategy."""

    def __init__(self) -> None:
        self._keyring_ok = _keyring_available()
        if not self._keyring_ok:
            logger.warning(
                "keyring library not available or backend non-functional. "
                "Install with: pip install keyring. "
                "Falling back to environment variables only."
            )

    # -- public API ---------------------------------------------------------

    def get(self, provider: str) -> str | None:
        """Retrieve an API key for *provider*.

        Tries Keychain first, then environment variable.
        Returns ``None`` if not found in either location.
        Never logs or prints the key value.
        """
        spec = self._spec(provider)

        # Tier 1: Keychain
        value = self._get_from_keychain(spec["keychain_key"])
        if value:
            logger.debug("Retrieved %s from Keychain", spec["display_name"])
            return value

        # Tier 2: Environment variable
        value = os.environ.get(spec["env_var"])
        if value:
            logger.debug("Retrieved %s from env var %s", spec["display_name"], spec["env_var"])
            return value

        logger.warning(
            "%s not found. Store it with: "
            "CredentialManager().store('%s', '<key>') "
            "or set env var %s",
            spec["display_name"],
            provider,
            spec["env_var"],
        )
        return None

    def store(self, provider: str, api_key: str) -> bool:
        """Store an API key in macOS Keychain.

        Validates the key format before storing.
        Records rotation metadata alongside the key.

        Returns:
            True if stored successfully, False otherwise.
        """
        spec = self._spec(provider)

        # Validate format
        if not self._validate_format(api_key, spec):
            logger.error(
                "%s format invalid. Expected: %s",
                spec["display_name"],
                spec["pattern_description"],
            )
            return False

        if not self._keyring_ok:
            logger.error(
                "Keychain not available. Cannot store credential. "
                "Install keyring: pip install keyring"
            )
            return False

        try:
            import keyring

            keyring.set_password(SERVICE_NAME, spec["keychain_key"], api_key)

            # Store rotation metadata
            meta = json.dumps({
                "stored_at": datetime.now().isoformat(),
                "rotation_due": (
                    datetime.now() + timedelta(days=spec["rotation_days"])
                ).isoformat(),
                "provider": provider,
            })
            keyring.set_password(
                SERVICE_NAME,
                spec["keychain_key"] + ROTATION_METADATA_KEY_SUFFIX,
                meta,
            )

            logger.info(
                "%s stored in Keychain. Rotation due in %d days.",
                spec["display_name"],
                spec["rotation_days"],
            )
            return True

        except Exception:
            logger.exception("Failed to store %s in Keychain", spec["display_name"])
            return False

    def delete(self, provider: str) -> bool:
        """Remove an API key from macOS Keychain."""
        spec = self._spec(provider)
        if not self._keyring_ok:
            logger.error("Keychain not available.")
            return False

        try:
            import keyring

            keyring.delete_password(SERVICE_NAME, spec["keychain_key"])
            # Also delete rotation metadata
            try:
                keyring.delete_password(
                    SERVICE_NAME,
                    spec["keychain_key"] + ROTATION_METADATA_KEY_SUFFIX,
                )
            except Exception:
                pass  # metadata may not exist
            logger.info("%s deleted from Keychain.", spec["display_name"])
            return True
        except Exception:
            logger.exception("Failed to delete %s from Keychain", spec["display_name"])
            return False

    def validate_all(self) -> dict[str, dict[str, Any]]:
        """Validate format of all registered credentials.

        Returns a dict of {provider: {found, source, format_valid, rotation_info}}.
        """
        results: dict[str, dict[str, Any]] = {}

        for provider, spec in CREDENTIAL_REGISTRY.items():
            result: dict[str, Any] = {
                "display_name": spec["display_name"],
                "found": False,
                "source": None,
                "format_valid": False,
                "rotation_info": None,
            }

            value = self.get(provider)
            if value:
                result["found"] = True
                # Determine source
                kc_val = self._get_from_keychain(spec["keychain_key"])
                result["source"] = "keychain" if kc_val else "environment"
                result["format_valid"] = self._validate_format(value, spec)

                # Check rotation
                rotation = self._get_rotation_meta(spec["keychain_key"])
                if rotation:
                    result["rotation_info"] = rotation

            results[provider] = result

        return results

    def check_rotation(self) -> list[str]:
        """Return list of warnings for credentials due for rotation."""
        warnings: list[str] = []

        for provider, spec in CREDENTIAL_REGISTRY.items():
            meta = self._get_rotation_meta(spec["keychain_key"])
            if not meta:
                continue

            due_str = meta.get("rotation_due")
            if not due_str:
                continue

            try:
                due_date = datetime.fromisoformat(due_str)
                if datetime.now() > due_date:
                    days_overdue = (datetime.now() - due_date).days
                    msg = (
                        f"WARNING: {spec['display_name']} rotation overdue by "
                        f"{days_overdue} days. Rotate at: {spec['docs_url']}"
                    )
                    warnings.append(msg)
                    logger.warning(msg)
                elif (due_date - datetime.now()).days < 14:
                    days_left = (due_date - datetime.now()).days
                    msg = (
                        f"NOTICE: {spec['display_name']} rotation due in "
                        f"{days_left} days. Rotate at: {spec['docs_url']}"
                    )
                    warnings.append(msg)
                    logger.info(msg)
            except (ValueError, TypeError):
                pass

        return warnings

    def mask(self, api_key: str) -> str:
        """Return a masked version of an API key for safe logging.

        Shows only the first 4 and last 4 characters.
        """
        if len(api_key) <= 12:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"

    # -- internal -----------------------------------------------------------

    def _spec(self, provider: str) -> dict[str, Any]:
        """Look up provider specification, raising on unknown provider."""
        provider = provider.lower().strip()
        if provider not in CREDENTIAL_REGISTRY:
            msg = (
                f"Unknown provider '{provider}'. "
                f"Known providers: {', '.join(CREDENTIAL_REGISTRY.keys())}"
            )
            raise ValueError(msg)
        return CREDENTIAL_REGISTRY[provider]

    def _get_from_keychain(self, keychain_key: str) -> str | None:
        """Retrieve a value from macOS Keychain."""
        if not self._keyring_ok:
            return None
        try:
            import keyring

            return keyring.get_password(SERVICE_NAME, keychain_key)
        except Exception:
            return None

    def _validate_format(self, value: str, spec: dict[str, Any]) -> bool:
        """Check if a credential matches the expected format pattern."""
        pattern = spec.get("pattern")
        if not pattern:
            return True  # no pattern defined = always valid
        return bool(re.match(pattern, value))

    def _get_rotation_meta(self, keychain_key: str) -> dict[str, Any] | None:
        """Retrieve rotation metadata from Keychain."""
        raw = self._get_from_keychain(keychain_key + ROTATION_METADATA_KEY_SUFFIX)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------


def main() -> None:
    """Command-line interface for credential management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage API credentials for AI Autobiography Generator"
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # store
    store_p = sub.add_parser("store", help="Store a credential in Keychain")
    store_p.add_argument("provider", choices=list(CREDENTIAL_REGISTRY.keys()))
    store_p.add_argument("api_key", help="The API key value")

    # get
    get_p = sub.add_parser("get", help="Retrieve a credential (masked)")
    get_p.add_argument("provider", choices=list(CREDENTIAL_REGISTRY.keys()))

    # delete
    del_p = sub.add_parser("delete", help="Delete a credential from Keychain")
    del_p.add_argument("provider", choices=list(CREDENTIAL_REGISTRY.keys()))

    # validate
    sub.add_parser("validate", help="Validate all credentials")

    # rotation
    sub.add_parser("rotation", help="Check rotation schedule")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    cm = CredentialManager()

    if args.command == "store":
        success = cm.store(args.provider, args.api_key)
        sys.exit(0 if success else 1)

    elif args.command == "get":
        value = cm.get(args.provider)
        if value:
            print(f"{args.provider}: {cm.mask(value)}")
        else:
            print(f"{args.provider}: NOT FOUND")
            sys.exit(1)

    elif args.command == "delete":
        success = cm.delete(args.provider)
        sys.exit(0 if success else 1)

    elif args.command == "validate":
        results = cm.validate_all()
        for provider, info in results.items():
            status = "OK" if info["found"] and info["format_valid"] else "FAIL"
            source = info["source"] or "not found"
            fmt = "valid" if info["format_valid"] else "INVALID"
            print(f"  [{status}] {info['display_name']}: source={source}, format={fmt}")

    elif args.command == "rotation":
        warnings = cm.check_rotation()
        if warnings:
            for w in warnings:
                print(f"  {w}")
        else:
            print("  All credentials within rotation window.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
