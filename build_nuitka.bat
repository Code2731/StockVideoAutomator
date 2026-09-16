@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"

python -c "import runpy;print(runpy.run_path('app/version.py')['__version__'])" > _version.tmp
set /p VERSION=<_version.tmp
del _version.tmp

echo === Stock Video Automator Nuitka Build (Windows) v%VERSION% ===
echo Building standalone executable...

REM MSVC 또는 MinGW(C 컴파일러)가 필요합니다.
python -m pip install -r requirements-build.txt

python -m nuitka ^
    --standalone ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=app/resources/app_icon.ico ^
    --company-name="Stock Video Automator" ^
    --product-name="Stock Video Automator" ^
    --file-version="%VERSION%" ^
    --product-version="%VERSION%" ^
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
echo 결과물: build\main.dist\main.exe
