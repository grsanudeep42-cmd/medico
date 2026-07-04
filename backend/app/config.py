"""Application settings loaded from environment variables."""
from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str

    # ── Security ──────────────────────────────────────────────────────────────
    secret_key: str
    backend_cors_origins: list[str] = ["http://localhost:3000"]

    # ── Required Diagnostic Tests by Facility Tier (IPHS-based) ───────────────
    required_tests_by_tier: dict[str, list[str]] = {
        "primary": ["Hb", "urine routine", "blood sugar", "malaria smear"],
        "community": [
            "Hb",
            "urine routine",
            "blood sugar",
            "malaria smear",
            "X-ray",
            "ECG",
            "wider pathology panel",
        ],
        "apex": [
            "Hb",
            "urine routine",
            "blood sugar",
            "malaria smear",
            "X-ray",
            "ECG",
            "wider pathology panel",
        ],
    }

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v: object) -> list[str]:
        """Accept JSON list OR a plain comma-separated string from the env."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v  # type: ignore[return-value]


settings = Settings()  # type: ignore[call-arg]
