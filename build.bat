@echo off
echo Building dev-start executable...

REM Install dependencies
python -m pip install -r requirements.txt

REM Build executable
pyinstaller dev-start.spec --clean

echo.
echo Build complete! Executable is in dist\dev-start.exe
pause
