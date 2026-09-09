from ai_project_health_monitor.core.config import (
    Environment,
    LLMProvider,
    Settings,
    get_settings,
)


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "AI Project Health Monitor"
    assert settings.app_version == "0.1.0"
    assert settings.environment == Environment.DEVELOPMENT
    assert settings.debug is False


def test_settings_accept_environment_values() -> None:
    settings = Settings(environment=Environment.TESTING)

    assert settings.environment == Environment.TESTING


def test_settings_reject_invalid_environment() -> None:
    invalid_settings = {"environment": "invalid"}

    try:
        Settings.model_validate(invalid_settings)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid environment should raise ValueError")


def test_get_settings_returns_cached_instance() -> None:
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second


def test_settings_default_llm_configuration() -> None:
    settings = Settings(_env_file=None)

    assert settings.llm_provider == LLMProvider.OLLAMA
    assert settings.llm_model == "qwen3:8b"
    assert settings.ollama_host == "http://localhost:11434"


def test_settings_accept_together_configuration() -> None:
    settings = Settings(
        llm_provider=LLMProvider.TOGETHER,
        llm_model="openai/gpt-oss-20b",
        together_api_key="test-key",
    )

    assert settings.llm_provider == LLMProvider.TOGETHER
    assert settings.llm_model == "openai/gpt-oss-20b"
    assert settings.together_api_key == "test-key"


def test_settings_accept_openai_configuration() -> None:
    settings = Settings(
        llm_provider=LLMProvider.OPENAI,
        llm_model="test-model",
        openai_api_key="test-key",
    )

    assert settings.llm_provider == LLMProvider.OPENAI
    assert settings.llm_model == "test-model"
    assert settings.openai_api_key == "test-key"