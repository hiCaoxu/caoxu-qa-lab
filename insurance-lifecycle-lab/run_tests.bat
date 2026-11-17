@echo off
cd /d %~dp0
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
.venv\Scripts\python.exe -m pytest -p pytest_metadata.plugin -p pytest_html.plugin --html=reports/report.html --self-contained-html
