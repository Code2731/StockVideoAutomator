"""VideoInfo.formats를 사용자에게 보여줄 형식 목록으로 변환하는 순수 로직.

Qt에 의존하지 않아 단위 테스트가 쉽다.
"""

from dataclasses import dataclass
from typing import List

from app.models.video_info import VideoInfo


@dataclass
class FormatOption:
    label: str
    detail: str
    filesize: int
    selector: str
    height: int = 0
    fps: int = 0


def _short_codec(value: str) -> str:
    return (value or "").split(".")[0]


def list_formats(video_info: VideoInfo, download_type: str = "video") -> List[FormatOption]:
    """사용 가능한 형식 목록을 정렬해 반환한다. 첫 항목은 '자동' 선택지다."""
    formats = video_info.formats or []
    options: List[FormatOption] = []

    if download_type == "video":
        for f in formats:
            if f.get("vcodec", "none") == "none":
                continue
            fmt_id = f.get("format_id") or f.get("format") or ""
            if not fmt_id:
                continue
            height = f.get("height") or 0
            fps = f.get("fps") or 0
            ext = (f.get("ext") or "").upper()
            vcodec = _short_codec(f.get("vcodec", ""))
            has_audio = f.get("acodec", "none") != "none"
            size = f.get("filesize") or f.get("filesize_approx") or 0

            label = f"{height}p" if height else (f.get("resolution") or "알 수 없음")
            if fps and fps >= 50:
                label += f" {int(fps)}fps"
            note = "영상+오디오" if has_audio else "영상 전용"
            detail = f"{ext} · {vcodec} · {note}"
            selector = fmt_id if has_audio else f"{fmt_id}+bestaudio/{fmt_id}"
            options.append(FormatOption(label, detail, size, selector, height, int(fps)))

        options.sort(
            key=lambda o: (o.height, o.fps, o.filesize), reverse=True
        )
    else:
        for f in formats:
            if f.get("vcodec", "none") != "none" or f.get("acodec", "none") == "none":
                continue
            fmt_id = f.get("format_id") or f.get("format") or ""
            if not fmt_id:
                continue
            size = f.get("filesize") or f.get("filesize_approx") or 0
            abr = f.get("abr") or 0
            label = f"{int(abr)} kbps" if abr else "오디오"
            detail = f"{(f.get('ext') or '').upper()} · {_short_codec(f.get('acodec', ''))}"
            options.append(FormatOption(label, detail, size, fmt_id))

        options.sort(key=lambda o: o.filesize, reverse=True)

    # selector 기준 중복 제거
    seen = set()
    unique: List[FormatOption] = []
    for opt in options:
        if opt.selector in seen:
            continue
        seen.add(opt.selector)
        unique.append(opt)

    # 맨 앞에 "자동 (현재 설정)" 추가 — selector ""는 툴바 설정 사용을 의미
    auto_label = "자동 (현재 설정)" if download_type == "video" else "자동 (최고 음질)"
    unique.insert(0, FormatOption(auto_label, "", 0, ""))
    return unique
