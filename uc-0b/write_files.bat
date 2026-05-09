@echo off
REM Calls the PowerShell script to write files (run from elevated prompt if needed)
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\code_sarathi\techm-prompt-to-production\uc-0b\write_files.ps1"
if %ERRORLEVEL% EQU 0 (
  echo Files written successfully.
) else (
  echo PowerShell script failed with exit code %ERRORLEVEL%.
)