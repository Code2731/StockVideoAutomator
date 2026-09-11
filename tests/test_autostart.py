from app.utils import autostart


def test_macos_enable_disable(monkeypatch, tmp_path):
    monkeypatch.setattr(autostart.sys, "platform", "darwin")
    plist = tmp_path / "LaunchAgents" / f"{autostart.APP_ID}.plist"
    monkeypatch.setattr(autostart, "macos_plist_path", lambda: str(plist))
    monkeypatch.setattr(autostart.subprocess, "run", lambda *a, **k: None)

    assert autostart.set_enabled(True, "/Applications/App.app/Contents/MacOS/App")
    assert plist.exists()
    assert autostart.APP_ID in plist.read_text("utf-8")

    assert autostart.set_enabled(False, "x")
    assert not plist.exists()


def test_linux_enable_disable(monkeypatch, tmp_path):
    monkeypatch.setattr(autostart.sys, "platform", "linux")
    desktop = tmp_path / "autostart" / "stock-video-automator.desktop"
    monkeypatch.setattr(autostart, "linux_desktop_path", lambda: str(desktop))

    assert autostart.set_enabled(True, "/usr/bin/app")
    assert desktop.exists()
    assert "Exec=/usr/bin/app" in desktop.read_text("utf-8")

    assert autostart.set_enabled(False, "x")
    assert not desktop.exists()


def test_disable_when_missing_is_safe(monkeypatch, tmp_path):
    monkeypatch.setattr(autostart.sys, "platform", "linux")
    monkeypatch.setattr(
        autostart, "linux_desktop_path",
        lambda: str(tmp_path / "nope" / "app.desktop"),
    )
    assert autostart.set_enabled(False, "x") is True
