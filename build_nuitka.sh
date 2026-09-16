#!/usr/bin/env bash
# macOS용 Nuitka 빌드 스크립트
set -euo pipefail

cd "$(dirname "$0")"

VERSION="$(python3 -c "import runpy; print(runpy.run_path('app/version.py')['__version__'])")"
APP_NAME="Stock Video Automator"

echo "=== Stock Video Automator Nuitka Build (macOS) v${VERSION} ==="
echo "Building standalone application..."

python3 -m pip install -r requirements-build.txt

python3 -m nuitka \
    --standalone \
    --macos-create-app-bundle \
    --macos-app-icon=app/resources/app_icon.png \
    --macos-app-name="${APP_NAME}" \
    --macos-app-version="${VERSION}" \
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
echo "결과물: build/main.app"
