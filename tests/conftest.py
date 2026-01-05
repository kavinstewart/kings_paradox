"""Pytest configuration and shared fixtures for technical risk tests."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Return the test data directory."""
    return project_root / "tests" / "data"


@pytest.fixture(scope="session")
def openai_api_key() -> str | None:
    """Return OpenAI API key from environment."""
    return os.getenv("OPENAI_API_KEY")


@pytest.fixture(scope="session")
def anthropic_api_key() -> str | None:
    """Return Anthropic API key from environment."""
    return os.getenv("ANTHROPIC_API_KEY")


@pytest.fixture
def skip_if_no_openai(openai_api_key: str | None) -> None:
    """Skip test if OpenAI API key is not available."""
    if not openai_api_key:
        pytest.skip("OPENAI_API_KEY not set")


@pytest.fixture
def skip_if_no_anthropic(anthropic_api_key: str | None) -> None:
    """Skip test if Anthropic API key is not available."""
    if not anthropic_api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")
