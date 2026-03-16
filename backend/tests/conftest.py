"""Pytest fixtures and configuration."""
from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _ensure_test_env() -> None:
    """Ensure minimal env for tests that don't need real DB."""
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("SERVICE_NAME", "test")
