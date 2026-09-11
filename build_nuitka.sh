#!/usr/bin/env bash
# macOS용 Nuitka 빌드 스크립트

echo "=== Stock Video Automator Nuitka Build (macOS) ==="
echo "Building standalone application..."

# 의존성 설치 확인
python3 -m pip install nuitka PySide6 requests yt-dlp mcp imageio

# 빌드 옵션
python3 -m nuitka \
    --standalone \
    --macos-create-app-bundle \
    --macos-app-icon=app/resources/app_icon.png \
    --macos-app-name="Stock Video Automator" \
    --macos-app-version="1.0.0" \
    --enable-plugin=pyside6 \
    --enable-plugin=anti-bloat \
    --include-data-dir=app/resources=app/resources \
    --noinclude-default-mode=error \
    --noinclude-pytest-mode=nofollow \
    --nofollow-import-to=pytest \
    --nofollow-import-to=unittest \
    --assume-yes-for-downloads \
    --show-progress \
    --output-dir=build \
    main.py

echo "=== Build Complete ==="
echo "결과물은 build/main.app 에 생성되었습니다."
