"""
app.core.config — Centralized configuration for CarePilot CN.

Reads from Streamlit secrets first, then falls back to environment
variables, then defaults. This design works on both Streamlit Cloud
and local development.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

import streamlit as st


def _read_secret(section: str, key: str, default: str = "") -> str:
    """Read a value from Streamlit secrets with fallback to env vars."""
    try:
        return str(st.secrets[section][key])
    except (KeyError, FileNotFoundError, AttributeError):
        env_key = f"{section.upper()}_{key.upper()}"
        return os.environ.get(env_key, default)


@dataclass(frozen=True)
class Settings:
    app_name: str = "CarePilot CN · 慢性病智能管理平台"
    app_env: str = "streamlit"

    # LLM Configuration
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = "gpt-4o-mini"

    # App-level flags
    enable_fake_llm: bool = True
    default_window_days: int = 14

    # Paths (writable on Streamlit Cloud)
    data_dir: Path = field(default_factory=lambda: Path("data"))
    export_dir: Path = field(default_factory=lambda: Path("data/exports"))

    @property
    def database_url(self) -> str:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{self.data_dir / 'carepilot_cn.db'}"

    @property
    def export_path(self) -> Path:
        self.export_dir.mkdir(parents=True, exist_ok=True)
        return self.export_dir

    @property
    def llm_configured(self) -> bool:
        """True if user has provided LLM credentials."""
        return bool(self.llm_api_key and (self.llm_base_url or self.llm_provider == "google"))

    @property
    def use_real_llm(self) -> bool:
        """Should we actually call LLM APIs?"""
        return self.llm_configured and not self.enable_fake_llm


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build settings from Streamlit secrets / env vars with safe fallbacks."""
    return Settings(
        llm_provider=_read_secret("llm", "provider", "openai"),
        llm_api_key=_read_secret("llm", "api_key", ""),
        llm_base_url=_read_secret("llm", "base_url", ""),
        llm_model=_read_secret("llm", "model", "gpt-4o-mini"),
        enable_fake_llm=_read_secret("app", "enable_fake_llm", "true").lower() in ("true", "1", "yes"),
        default_window_days=int(_read_secret("app", "default_window_days", "14")),
    )
