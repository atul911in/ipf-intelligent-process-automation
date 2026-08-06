@echo off
echo Starting IPF IPA React UI on http://localhost:3000
cd /d "%~dp0"
npm run dev -- --port 3000
