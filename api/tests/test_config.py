from app.config import Settings


def test_settings_reads_nav_feed_values_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@db:5432/x")
    monkeypatch.setenv("HTTP_USER_AGENT", "test-agent")
    monkeypatch.setenv("NAV_FEED_BASE_URL", "https://feed.example.com")
    monkeypatch.setenv("NAV_FEED_TOKEN", "test-token")

    settings = Settings(_env_file=None)

    assert settings.nav_feed_base_url == "https://feed.example.com"
    assert settings.nav_feed_token == "test-token"
