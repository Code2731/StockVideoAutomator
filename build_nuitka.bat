@echo off
chcp 65001 > nul
echo === Stock Video Automator Nuitka Build (Windows) ===
echo Building standalone executable...

REM 의존성 설치 확인
python -m pip install nuitka PySide6 requests yt-dlp mcp imageio

REM MSVC나 MinGW(C 컴파일러)가 필요합니다.
REM Windows에서는 아이콘을 .ico 파일로 지정합니다.

python -m nuitka ^
    --standalone ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=app/resources/app_icon.ico ^
    --company-name="My Company" ^
    --product-name="Stock Video Automator" ^
    --file-version="1.0.0" ^
    --product-version="1.0.0" ^
    --file-description="Stock Video Downloader application" ^
    --enable-plugin=pyside6 ^
    --enable-plugin=anti-bloat ^
    --include-data-dir=app/resources=app/resources ^
    --noinclude-default-mode=error ^
    --noinclude-pytest-mode=nofollow ^
    --nofollow-import-to=pytest ^
    --nofollow-import-to=unittest ^
    --assume-yes-for-downloads ^
    --show-progress ^
    --output-dir=build ^
    main.py

echo === Build Complete ===
echo 결과물은 build/main.dist 폴더 내의 main.exe로 생성되었습니다.
pause
