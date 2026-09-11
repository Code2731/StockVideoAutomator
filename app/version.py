"""애플리케이션 버전 및 배포 저장소 정보."""

import re

__version__ = "1.0.0"

GITHUB_REPO = "Code2731/StockVideoAutomator"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"


def parse_version(text: str) -> tuple:
    """'v1.2.3' 형태의 문자열을 (1, 2, 3) 튜플로 변환한다."""
    if not text:
        return ()
    text = str(text).strip().lstrip("vV")
    result = []
    for part in re.split(r"[.\-+_]", text):
        match = re.match(r"^\d+", part)
        if not match:
            break
        result.append(int(match.group()))
    return tuple(result)


def is_newer(latest: str, current: str) -> bool:
    """latest가 current보다 최신 버전이면 True를 반환한다."""
    latest_parsed = parse_version(latest)
    current_parsed = parse_version(current)
    if not latest_parsed or not current_parsed:
        return False
    return latest_parsed > current_parsed
