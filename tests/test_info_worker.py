from app.workers import info_worker as iw


class _FakeSettings:
    def __init__(self, browser="", proxy=""):
        self._browser = browser
        self._proxy = proxy

    def get_cookie_browser_name(self):
        return self._browser

    def get_proxy_url(self):
        return self._proxy


def test_build_opts_defaults(monkeypatch):
    monkeypatch.setattr(iw, "SettingsManager", lambda: _FakeSettings())
    opts = iw.InfoWorker("https://youtu.be/x")._build_ydl_opts()
    assert "cookiesfrombrowser" not in opts
    assert "proxy" not in opts
    assert opts["extract_flat"] is False


def test_build_opts_with_cookies_and_proxy(monkeypatch):
    monkeypatch.setattr(
        iw, "SettingsManager",
        lambda: _FakeSettings("chrome", "http://127.0.0.1:8080"),
    )
    opts = iw.InfoWorker(":ytwatchlater")._build_ydl_opts()
    assert opts["cookiesfrombrowser"] == ("chrome",)
    assert opts["proxy"] == "http://127.0.0.1:8080"
