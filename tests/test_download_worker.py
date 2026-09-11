import pytest
import yt_dlp

from app.models.video_info import VideoInfo
from app.workers import download_worker as dw


class _FakeSettings:
    speed_limit = 0
    download_threads = 1

    def get_proxy_url(self):
        return ""

    def get_cookie_browser_name(self):
        return ""


@pytest.fixture
def worker(monkeypatch):
    monkeypatch.setattr(dw, "SettingsManager", _FakeSettings)
    vi = VideoInfo(url="https://youtu.be/abc", video_id="abc", title="t")
    return dw.DownloadWorker(video_info=vi, save_dir="/tmp")


def test_default_format_string(worker):
    assert worker._get_format_string() == (
        "bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio/best"
    )


def test_format_string_with_filters(worker):
    worker.quality = "720p"
    worker.codec = "H265"
    worker.frame_rate = "60fps"
    assert worker._get_format_string() == (
        "bestvideo[height<=720][vcodec^=hev][fps<=60]+bestaudio/"
        "bestvideo[height<=720]+bestaudio/best"
    )


def test_format_string_best_quality_no_height_filter(worker):
    worker.quality = "best"
    assert "height" not in worker._get_format_string()


def test_pause_and_cancel_flags(worker):
    assert worker._paused is False
    assert worker._cancelled is False
    worker.pause()
    assert worker._paused is True
    assert worker._cancelled is False
    worker.cancel()
    assert worker._cancelled is True


def test_build_options_keeps_partial_files(worker):
    opts = worker._build_options()
    assert opts["continuedl"] is True
    assert opts["nopart"] is False
    assert opts["format"].startswith("bestvideo")


def _pp_keys(opts):
    return [pp["key"] for pp in opts.get("postprocessors", [])]


def test_metadata_tagging_added(worker):
    assert "FFmpegMetadata" in _pp_keys(worker._build_options())


def test_subtitle_conversion_added(worker):
    worker.subtitle = True
    worker.subtitle_lang = "한국어"
    opts = worker._build_options()
    assert opts["writesubtitles"] is True
    assert opts["subtitleslangs"] == ["ko"]
    assert "FFmpegSubtitlesConvertor" in _pp_keys(opts)


def test_audio_extract_postprocessor(worker):
    worker.download_type = "audio"
    worker.fmt = "mp3"
    opts = worker._build_options()
    keys = _pp_keys(opts)
    assert "FFmpegExtractAudio" in keys
    assert "FFmpegMetadata" in keys


def test_progress_hook_pauses(worker):
    worker._paused = True
    with pytest.raises(dw._DownloadPaused):
        worker._progress_hook({"status": "downloading"})


def test_progress_hook_cancels(worker):
    worker._yt_dlp = yt_dlp
    worker._cancelled = True
    with pytest.raises(yt_dlp.utils.DownloadError):
        worker._progress_hook({"status": "downloading"})
