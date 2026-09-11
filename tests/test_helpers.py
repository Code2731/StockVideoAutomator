import os
import sys

import pytest

from app.utils import helpers


def test_format_file_size_unknown():
    assert helpers.format_file_size(None) == "알 수 없음"
    assert helpers.format_file_size(0) == "알 수 없음"


def test_format_file_size_units():
    assert helpers.format_file_size(512) == "512.0 B"
    assert helpers.format_file_size(1024) == "1.0 KB"
    assert helpers.format_file_size(1024 ** 2) == "1.0 MB"
    assert helpers.format_file_size(1024 ** 3) == "1.0 GB"


def test_format_duration():
    assert helpers.format_duration(None) == "00:00"
    assert helpers.format_duration(0) == "00:00"
    assert helpers.format_duration(65) == "01:05"
    assert helpers.format_duration(3661) == "1:01:01"


def test_format_speed():
    assert helpers.format_speed(None) == ""
    assert helpers.format_speed(0) == ""
    assert helpers.format_speed(2048) == "2.0 KB/s"


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=abc123",
    "http://youtube.com/watch?v=abc123",
    "https://youtu.be/abc123",
    "https://www.youtube.com/shorts/abc123",
    "https://www.youtube.com/playlist?list=PL123",
    "https://www.youtube.com/@channel",
    "https://www.youtube.com/channel/UC123",
])
def test_is_youtube_url_true(url):
    assert helpers.is_youtube_url(url) is True


@pytest.mark.parametrize("url", [
    "",
    "https://vimeo.com/12345",
    "not a url",
])
def test_is_youtube_url_false(url):
    assert helpers.is_youtube_url(url) is False


def test_is_playlist_url():
    assert helpers.is_playlist_url("https://www.youtube.com/playlist?list=PL1") is True
    assert helpers.is_playlist_url("https://www.youtube.com/watch?v=a&list=PL1") is True
    assert helpers.is_playlist_url("https://www.youtube.com/watch?v=a") is False


@pytest.mark.parametrize("url", [":ytwatchlater", ":ytfav", ":ytsubs", ":ythistory"])
def test_is_playlist_url_special(url):
    assert helpers.is_playlist_url(url) is True


def test_app_data_dir_creates_directory(monkeypatch, tmp_path):
    target = tmp_path / "data"
    monkeypatch.setattr(
        helpers.os.path, "expanduser", lambda _path: str(target)
    )
    result = helpers.app_data_dir()
    assert result == str(target / helpers.APP_DATA_DIR_NAME)
    assert os.path.isdir(result)


def test_ffmpeg_candidates_returns_expected_executable():
    candidates = helpers._ffmpeg_candidates()
    assert candidates
    exe = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    assert all(c.endswith(exe) for c in candidates)


def test_find_ffmpeg_returns_none_when_missing(monkeypatch):
    monkeypatch.setattr(helpers.shutil, "which", lambda _name: None)
    monkeypatch.setattr(helpers.os.path, "isfile", lambda _path: False)
    assert helpers.find_ffmpeg() is None


def test_find_ffmpeg_prefers_path(monkeypatch):
    monkeypatch.setattr(helpers.shutil, "which", lambda _name: "/custom/bin/ffmpeg")
    assert helpers.find_ffmpeg() == "/custom/bin/ffmpeg"
