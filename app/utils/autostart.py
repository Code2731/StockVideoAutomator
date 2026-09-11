"""운영체제별 자동 시작 등록/해제.

- Windows: HKCU Run 레지스트리
- macOS:   ~/Library/LaunchAgents/<APP_ID>.plist
- Linux:   ~/.config/autostart/stock-video-automator.desktop
"""

import os
import subprocess
import sys

from app.utils.logger import get_logger

logger = get_logger(__name__)

APP_ID = "com.stockvideoautomator.app"
APP_NAME = "StockVideoAutomator"

_MACOS_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" \
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""

_LINUX_DESKTOP = """[Desktop Entry]
Type=Application
Name=Stock Video Automator
Exec={exe}
X-GNOME-Autostart-enabled=true
Terminal=false
"""


def set_enabled(enabled: bool, exe_path: str) -> bool:
    """자동 시작을 켜거나 끈다. 성공하면 True를 반환한다."""
    try:
        if sys.platform == "win32":
            return _set_windows(enabled, exe_path)
        if sys.platform == "darwin":
            return _set_macos(enabled, exe_path)
        return _set_linux(enabled, exe_path)
    except Exception:
        logger.warning("자동 시작 설정 실패 (enabled=%s)", enabled, exc_info=True)
        return False


def _set_windows(enabled: bool, exe_path: str) -> bool:
    import winreg

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    )
    try:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)
    return True


def macos_plist_path() -> str:
    return os.path.expanduser(f"~/Library/LaunchAgents/{APP_ID}.plist")


def _set_macos(enabled: bool, exe_path: str) -> bool:
    path = macos_plist_path()
    if enabled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_MACOS_PLIST.format(label=APP_ID, exe=exe_path))
        subprocess.run(["launchctl", "load", "-w", path], capture_output=True)
    else:
        if os.path.exists(path):
            subprocess.run(["launchctl", "unload", "-w", path], capture_output=True)
            os.remove(path)
    return True


def linux_desktop_path() -> str:
    config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(config_home, "autostart", "stock-video-automator.desktop")


def _set_linux(enabled: bool, exe_path: str) -> bool:
    path = linux_desktop_path()
    if enabled:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_LINUX_DESKTOP.format(exe=exe_path))
    else:
        if os.path.exists(path):
            os.remove(path)
    return True
