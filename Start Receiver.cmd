@echo off
cd /d "%~dp0"
py -3 receiver.py
if errorlevel 1 (
 echo.
 echo If Python was not found, install Python 3.10 or newer, then try again.
)
pause
