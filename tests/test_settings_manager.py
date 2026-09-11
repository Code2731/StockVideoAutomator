import pytest
from PySide6.QtCore import QSettings

import app.utils.settings_manager as sm


@pytest.fixture
def settings(tmp_path, monkeypatch):
    sm.SettingsManager._instance = None
    monkeypatch.setattr(
        sm,
        "QSettings",
        lambda *args, **kwargs: QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )
    instance = sm.SettingsManager()
    yield instance
    sm.SettingsManager._instance = None


def test_defaults(settings):
    assert settings.language == "한국어"
    assert settings.concurrent_downloads == 3
    assert settings.download_threads == 4
    assert settings.run_in_background is False
    assert settings.proxy_type == "사용 안 함"


def test_roundtrip(settings):
    settings.concurrent_downloads = 7
    settings.run_in_background = True
    settings.default_save_path = "/tmp/videos"
    assert settings.concurrent_downloads == 7
    assert settings.run_in_background is True
    assert settings.default_save_path == "/tmp/videos"


def test_proxy_url_disabled(settings):
    settings.proxy_type = "사용 안 함"
    settings.proxy_host = "127.0.0.1"
    assert settings.get_proxy_url() == ""


def test_proxy_url_http(settings):
    settings.proxy_type = "HTTP"
    settings.proxy_host = "127.0.0.1"
    settings.proxy_port = "8080"
    assert settings.get_proxy_url() == "http://127.0.0.1:8080"


def test_proxy_url_socks5_without_port(settings):
    settings.proxy_type = "SOCKS5"
    settings.proxy_host = "10.0.0.1"
    settings.proxy_port = ""
    assert settings.get_proxy_url() == "socks5://10.0.0.1"


@pytest.mark.parametrize("browser,expected", [
    ("사용 안 함", ""),
    ("Chrome", "chrome"),
    ("Firefox", "firefox"),
    ("Edge", "edge"),
    ("Brave", "brave"),
])
def test_cookie_browser_name(settings, browser, expected):
    settings.cookie_browser = browser
    assert settings.get_cookie_browser_name() == expected


def test_auto_start_path_is_string(settings):
    assert isinstance(settings.get_auto_start_path(), str)
