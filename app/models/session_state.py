"""진행 중/대기 중 다운로드를 디스크에 저장해 앱 재시작 후 이어받기를 지원한다.

완료되지 않은 다운로드만 대상으로 하며, `partial` 파일은 yt-dlp가 유지하므로
재시작 후 재개하면 이어받기가 가능하다.
"""

import json
import os
from dataclasses import asdict, fields
from typing import List

from app.models.video_info import VideoInfo
from app.utils.helpers import app_data_dir
from app.utils.logger import get_logger

logger = get_logger(__name__)

_FILENAME = "active_downloads.json"
# 상태 파일 크기를 줄이기 위해 직렬화에서 제외할 필드
_EXCLUDED_FIELDS = {"formats", "subtitles", "auto_captions"}


def _state_path() -> str:
    return os.path.join(app_data_dir(), _FILENAME)


def save(items: List[VideoInfo]) -> None:
    """현재 활성/대기 다운로드 목록을 저장한다. 비어 있으면 파일을 제거한다."""
    if not items:
        clear()
        return

    payload = []
    for vi in items:
        data = asdict(vi)
        for key in _EXCLUDED_FIELDS:
            data.pop(key, None)
        payload.append(data)

    try:
        with open(_state_path(), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError:
        logger.warning("활성 다운로드 상태 저장 실패", exc_info=True)


def load() -> List[VideoInfo]:
    """저장된 활성/대기 다운로드 목록을 복원한다. 실패 시 빈 목록을 반환한다."""
    path = _state_path()
    if not os.path.exists(path):
        return []

    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        logger.warning("활성 다운로드 상태 로드 실패", exc_info=True)
        return []

    if not isinstance(payload, list):
        return []

    valid_fields = {f.name for f in fields(VideoInfo)}
    result = []
    for data in payload:
        if not isinstance(data, dict):
            continue
        kwargs = {k: v for k, v in data.items() if k in valid_fields}
        result.append(VideoInfo(**kwargs))
    return result


def clear() -> None:
    """저장된 상태 파일을 제거한다."""
    try:
        os.remove(_state_path())
    except FileNotFoundError:
        pass
    except OSError:
        logger.warning("활성 다운로드 상태 삭제 실패", exc_info=True)
