@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo === JATIC-Library build ===

REM 1. Version from package
for /f "tokens=*" %%v in ('uv run python -c "from jatic_library import __version__; print(__version__)"') do (
    set "APP_VERSION=%%v"
)
if "%APP_VERSION%"=="" (
    echo [ERROR] Failed to resolve version.
    exit /b 1
)
echo Version: %APP_VERSION%

REM 2. Clean previous artifacts
echo Cleaning dist/ and build/ ...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM 3. PyInstaller (onedir)
echo Running PyInstaller ...
uv run pyinstaller --noconfirm --clean jatic-library.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller failed.
    exit /b 1
)

REM 4. Bundle docs for end users
echo Copying README / LICENSE / BETA_TEST ...
copy /y README.md dist\JATIC-Library\README.md >nul
copy /y LICENSE dist\JATIC-Library\LICENSE >nul
copy /y docs\BETA_TEST.md dist\JATIC-Library\BETA_TEST.md >nul

REM 5. Zip for distribution
set "ZIP_NAME=JATIC-Library-%APP_VERSION%-win64.zip"
echo Creating %ZIP_NAME% ...
if exist "dist\%ZIP_NAME%" del /q "dist\%ZIP_NAME%"
powershell -NoProfile -Command "Compress-Archive -Path 'dist\JATIC-Library\*' -DestinationPath 'dist\%ZIP_NAME%' -CompressionLevel Optimal"
if errorlevel 1 (
    echo [ERROR] zip creation failed.
    exit /b 1
)

echo === Build complete ===
echo Output:   dist\JATIC-Library\
echo Bundle:   dist\%ZIP_NAME%
exit /b 0
