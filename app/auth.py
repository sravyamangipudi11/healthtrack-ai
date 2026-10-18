"""Minimal API-key RBAC. Roles: clinician (analyze), admin (analyze + logs). Off by default for local dev."""
import hmac
from fastapi import Header, HTTPException


def make_auth(settings):
    def require(*roles: str):
        def dep(x_api_key: str = Header(default="")) -> str:
            if not settings.auth_enabled:
                return "admin"  # dev mode
            role = next((r for k, r in settings.api_keys.items() if hmac.compare_digest(k, x_api_key)), None)
            if role is None:
                raise HTTPException(401, "Missing or invalid API key")
            if role not in roles:
                raise HTTPException(403, "Role not permitted")
            return role
        return dep
    return require
