import json

import pytest

from app.models import session_state
from app.models.video_info import VideoInfo


@pytest.fixture
def state_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(session_state, "app_data_dir", lambda: str(tmp_path))
    return tmp_path


def test_load_missing_returns_empty(state_dir):
    assert session_state.load() == []


def test_save_and_load_roundtrip(state_dir):
    vi = VideoInfo(
        url="https://youtu.be/abc",
        video_id="abc",
        title="제목",
        status="paused",
        options={"quality": "720p"},
    )
    session_state.save([vi])

    loaded = session_state.load()
    assert len(loaded) == 1
    assert loaded[0].video_id == "abc"
    assert loaded[0].title == "제목"
    assert loaded[0].status == "paused"
    assert loaded[0].options == {"quality": "720p"}


def test_heavy_fields_excluded_from_disk(state_dir):
    vi = VideoInfo(video_id="abc", formats=[{"a": 1}], subtitles={"ko": []})
    session_state.save([vi])
    raw = json.loads((state_dir / "active_downloads.json").read_text("utf-8"))
    assert "formats" not in raw[0]
    assert "subtitles" not in raw[0]


def test_save_empty_clears(state_dir):
    session_state.save([VideoInfo(video_id="abc")])
    assert (state_dir / "active_downloads.json").exists()
    session_state.save([])
    assert not (state_dir / "active_downloads.json").exists()


def test_load_corrupt_returns_empty(state_dir):
    (state_dir / "active_downloads.json").write_text("{not json", "utf-8")
    assert session_state.load() == []
