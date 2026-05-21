@echo off
setlocal
cd /d "%~dp0"
echo Building JATIC-Library with PyInstaller...
python -m uv run pyinstaller --noconfirm jatic-library.spec
if errorlevel 1 exit /b 1
echo Output: dist\JATIC-Library\
exit /b 0
