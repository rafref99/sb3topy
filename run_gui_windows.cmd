@echo off
setlocal

set "APP_DIR=%~dp0"
cd /d "%APP_DIR%" || exit /b 1

set "PYTHON_BIN="
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_BIN=py -3.12"
)

if not defined PYTHON_BIN (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_BIN=python"
)

if not defined PYTHON_BIN (
    echo Python 3.12 is required to run sb3topy.
    echo Install Python, then run: python -m pip install -r requirements.txt
    pause
    exit /b 1
)

%PYTHON_BIN% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" > "%TEMP%\sb3topy_python_version.txt"
if errorlevel 1 (
    set /p PYTHON_VERSION=<"%TEMP%\sb3topy_python_version.txt"
    del "%TEMP%\sb3topy_python_version.txt" >nul 2>nul
    echo Python 3.12 is required to run sb3topy.
    echo Found Python %PYTHON_VERSION% using: %PYTHON_BIN%
    echo Install Python 3.12, then run: python -m pip install -r requirements.txt
    pause
    exit /b 1
) else (
    del "%TEMP%\sb3topy_python_version.txt" >nul 2>nul
)

if defined PYTHONPATH (
    set "PYTHONPATH=%APP_DIR%src;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%APP_DIR%src"
)

set "MISSING_PACKAGES="
%PYTHON_BIN% -c "import importlib.util, sys; packages={'pygame':'pygame','requests':'requests','customtkinter':'customtkinter','tkinterdnd2':'tkinterdnd2','CairoSVG':'cairosvg'}; missing=[name for name, module in packages.items() if importlib.util.find_spec(module) is None]; print(' '.join(missing)); sys.exit(1 if missing else 0)" > "%TEMP%\sb3topy_missing_packages.txt"
if errorlevel 1 (
    set /p MISSING_PACKAGES=<"%TEMP%\sb3topy_missing_packages.txt"
    del "%TEMP%\sb3topy_missing_packages.txt" >nul 2>nul
    echo Missing required Python packages: %MISSING_PACKAGES%
    choice /C YN /N /M "Install them now with '%PYTHON_BIN% -m pip install -r requirements.txt'? [Y/N] "
    if errorlevel 2 (
        echo Cannot run sb3topy until the required packages are installed.
        pause
        exit /b 1
    )
    %PYTHON_BIN% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Package installation failed.
        pause
        exit /b 1
    )
) else (
    del "%TEMP%\sb3topy_missing_packages.txt" >nul 2>nul
)

%PYTHON_BIN% -m sb3topy --gui
set "STATUS=%ERRORLEVEL%"

if not "%STATUS%"=="0" (
    echo.
    echo sb3topy exited with an error.
    echo If dependencies are missing, run: %PYTHON_BIN% -m pip install -r requirements.txt
    pause
)

exit /b %STATUS%
