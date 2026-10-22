@echo off
setlocal

set "CORPUS_SCRIPT=%~dp0corpus.py"
set "PYTHONUTF8=1"
set "PYTHON_MANAGER_AUTOMATIC_INSTALL=false"

if defined DOC_RESEARCH_PYTHON goto try_override

where py >nul 2>&1
if errorlevel 1 goto try_python
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto try_python
py -3 "%CORPUS_SCRIPT%" %*
exit /b %errorlevel%

:try_python
where python >nul 2>&1
if errorlevel 1 goto missing_python
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto missing_python
python "%CORPUS_SCRIPT%" %*
exit /b %errorlevel%

:try_override
"%DOC_RESEARCH_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto invalid_override
"%DOC_RESEARCH_PYTHON%" "%CORPUS_SCRIPT%" %*
exit /b %errorlevel%

:invalid_override
echo error: DOC_RESEARCH_PYTHON is not an executable Python 3.10+: %DOC_RESEARCH_PYTHON% 1>&2
exit /b 127

:missing_python
echo error: Python 3.10 or newer was not found. 1>&2
where winget >nul 2>&1
if errorlevel 1 goto no_winget
echo install: winget install 9NQ7512CXL7T -e --accept-package-agreements --disable-interactivity 1>&2
echo then: py install default 1>&2
exit /b 127

:no_winget
echo install: start "" https://www.python.org/downloads/windows/ 1>&2
exit /b 127
