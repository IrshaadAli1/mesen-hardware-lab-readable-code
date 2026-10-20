@echo off
cd /d "%~dp0"
py -3 hardware_lab.py
if errorlevel 1 pause
