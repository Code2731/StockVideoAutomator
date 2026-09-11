import requests

from app.workers.app_update_worker import AppUpdateWorker


class _FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def _run_worker():
    worker = AppUpdateWorker()
    results = []
    worker.finished.connect(lambda ok, info: results.append((ok, info)))
    worker.run()
    return results


def test_update_available(monkeypatch):
    monkeypatch.setattr(
        requests, "get",
        lambda *a, **k: _FakeResponse({
            "tag_name": "v9.9.9",
            "html_url": "https://example.com/release",
            "assets": [{"name": "app.zip", "browser_download_url": "u"}],
        }),
    )
    ok, info = _run_worker()[0]
    assert ok is True
    assert info["update_available"] is True
    assert info["latest_version"] == "v9.9.9"
    assert info["assets"][0]["name"] == "app.zip"


def test_no_update(monkeypatch):
    monkeypatch.setattr(
        requests, "get",
        lambda *a, **k: _FakeResponse({"tag_name": "0.0.1", "assets": []}),
    )
    ok, info = _run_worker()[0]
    assert ok is True
    assert info["update_available"] is False


def test_request_failure(monkeypatch):
    def _boom(*a, **k):
        raise requests.RequestException("network down")

    monkeypatch.setattr(requests, "get", _boom)
    ok, info = _run_worker()[0]
    assert ok is False
    assert "network down" in info["error"]
