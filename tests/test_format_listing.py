from app.models.video_info import VideoInfo
from app.utils.format_listing import list_formats


def _video_info():
    return VideoInfo(
        video_id="abc",
        title="t",
        formats=[
            {
                "format_id": "137", "ext": "mp4", "height": 1080, "fps": 30,
                "vcodec": "avc1.640028", "acodec": "none",
                "filesize": 1000,
            },
            {
                "format_id": "22", "ext": "mp4", "height": 720, "fps": 30,
                "vcodec": "avc1.64001F", "acodec": "mp4a.40.2",
                "filesize": 2000,
            },
            {
                "format_id": "140", "ext": "m4a", "vcodec": "none",
                "acodec": "mp4a.40.2", "abr": 128, "filesize": 500,
            },
        ],
    )


def test_video_formats_sorted_and_selector():
    options = list_formats(_video_info(), "video")
    assert options[0].selector == ""  # 자동
    assert [o.label for o in options[1:]] == ["1080p", "720p"]

    video_only = options[1]
    assert video_only.selector == "137+bestaudio/137"
    assert "영상 전용" in video_only.detail

    combined = options[2]
    assert combined.selector == "22"
    assert "영상+오디오" in combined.detail


def test_audio_formats():
    options = list_formats(_video_info(), "audio")
    assert options[0].selector == ""
    assert len(options) == 2
    assert options[1].selector == "140"
    assert "128 kbps" == options[1].label


def test_empty_formats_returns_auto_only():
    options = list_formats(VideoInfo(video_id="x"), "video")
    assert len(options) == 1
    assert options[0].selector == ""


def test_fps_60_label():
    vi = VideoInfo(formats=[{
        "format_id": "1", "ext": "mp4", "height": 1080, "fps": 60,
        "vcodec": "avc1", "acodec": "none", "filesize": 10,
    }])
    options = list_formats(vi, "video")
    assert "60fps" in options[1].label
