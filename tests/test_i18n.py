import pytest

import app.utils.i18n as i18n


@pytest.mark.parametrize("lang,expected", [
    ("한국어", "파일"),
    ("English", "File"),
    ("日本語", "ファイル"),
    ("中文", "文件"),
])
def test_menu_translation(monkeypatch, lang, expected):
    monkeypatch.setattr(i18n, "_current_language", lang)
    assert i18n.tr("menu.file") == expected


def test_format_kwargs(monkeypatch):
    monkeypatch.setattr(i18n, "_current_language", "English")
    assert i18n.tr("msg.paused_count", count=3) == "3 downloads paused"


def test_unknown_key_returns_key(monkeypatch):
    monkeypatch.setattr(i18n, "_current_language", "English")
    assert i18n.tr("nonexistent.key") == "nonexistent.key"


def test_fallback_to_korean(monkeypatch):
    monkeypatch.setattr(i18n, "_current_language", "English")
    monkeypatch.delitem(i18n._EN, "menu.file", raising=False)
    assert i18n.tr("menu.file") == "파일"


def test_set_language_persists(monkeypatch):
    saved = {}

    class FakeSettings:
        language = "한국어"

        def sync(self):
            saved["synced"] = True

    monkeypatch.setattr(
        "app.utils.settings_manager.SettingsManager", lambda: FakeSettings()
    )
    i18n.set_language("English")
    assert i18n.get_language() == "English"
    assert saved.get("synced") is True


def test_set_language_invalid_falls_back(monkeypatch):
    monkeypatch.setattr(
        "app.utils.settings_manager.SettingsManager",
        lambda: type("S", (), {"language": "한국어", "sync": lambda self: None})(),
    )
    i18n.set_language("Klingon")
    assert i18n.get_language() == "한국어"


@pytest.mark.parametrize("lang", ["English", "日本語", "中文"])
def test_all_languages_cover_base_keys(lang):
    missing = set(i18n._KO) - set(i18n._TRANSLATIONS[lang])
    assert not missing, f"{lang} missing keys: {sorted(missing)}"
