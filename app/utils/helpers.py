from typing import Optional, Union
import os
import sys
import re
import shutil


APP_DATA_DIR_NAME = ".stock_video_automator"


def app_data_dir() -> str:
    """애플리케이션 데이터 디렉터리 경로를 반환한다 (없으면 생성)."""
    base = os.path.join(os.path.expanduser("~"), APP_DATA_DIR_NAME)
    os.makedirs(base, exist_ok=True)
    return base


def resource_path(*paths: str) -> str:
    """PyInstaller/Nuitka 빌드 환경에서도 올바른 리소스 경로를 반환한다."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    elif "__compiled__" in globals():
        base = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # 개발 환경: 프로젝트 루트 (helpers.py → utils → app → project root)
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *paths)


def format_file_size(size_bytes: Union[int, float, None]) -> str:
    if not size_bytes:
        return "알 수 없음"
    size_bytes = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "00:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_speed(bytes_per_sec: Optional[float]) -> str:
    if not bytes_per_sec:
        return ""
    return f"{format_file_size(bytes_per_sec)}/s"


def is_youtube_url(url: str) -> bool:
    patterns = [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=",
        r"(https?://)?(www\.)?youtube\.com/playlist\?list=",
        r"(https?://)?(www\.)?youtube\.com/shorts/",
        r"(https?://)?youtu\.be/",
        r"(https?://)?(www\.)?youtube\.com/@[\w-]+",
        r"(https?://)?(www\.)?youtube\.com/channel/",
    ]
    return any(re.search(p, url) for p in patterns)


def is_playlist_url(url: str) -> bool:
    # yt-dlp 특수 URL(:ytwatchlater, :ytfav, :ytsubs 등)은 재생목록으로 취급
    if url.startswith(":yt"):
        return True
    return "playlist?list=" in url or "&list=" in url or "/feed/" in url


def _ffmpeg_candidates() -> list:
    """플랫폼별로 ffmpeg 실행 파일이 있을 만한 후보 경로를 반환한다."""
    exe = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    candidates = []

    # 패키징된 앱 내부 동봉 경로
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    candidates.append(os.path.join(app_dir, "ffmpeg", exe))
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(sys._MEIPASS, "ffmpeg", exe))

    # Python 실행 파일과 같은 디렉터리 (Windows: Scripts)
    py_dir = os.path.dirname(sys.executable)
    candidates.append(os.path.join(py_dir, exe))
    candidates.append(os.path.join(py_dir, "Scripts", exe))

    # OS별 패키지 매니저 기본 경로
    if sys.platform == "darwin":
        candidates += ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]
    elif sys.platform != "win32":
        candidates += ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]

    return candidates


def find_ffmpeg() -> Optional[str]:
    """ffmpeg 실행 파일 경로를 탐색한다. 없으면 None을 반환한다."""
    found = shutil.which("ffmpeg")
    if found:
        return found

    for candidate in _ffmpeg_candidates():
        if os.path.isfile(candidate):
            return candidate
    return None


def setup_environment() -> None:
    """앱 시작 시 1회만 실행되어 환경 변수 및 외부 의존성(deno, ffmpeg) 경로를 설정한다."""
    # deno 경로 자동 추가 (yt-dlp JS 런타임)
    deno_dir = os.path.join(os.path.expanduser("~"), ".deno", "bin")
    if os.path.isdir(deno_dir) and deno_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = deno_dir + os.pathsep + os.environ.get("PATH", "")

    # ffmpeg 경로 자동 탐색 및 캐싱
    ffmpeg_path = find_ffmpeg()
    if ffmpeg_path:
        os.environ["APP_FFMPEG_LOCATION"] = os.path.dirname(ffmpeg_path)
