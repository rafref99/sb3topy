#!/bin/sh

set -u

APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$APP_DIR" || exit 1

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
else
    echo "Python 3.12 is required to run sb3topy."
    echo "Install Python, then run: python3 -m pip install -r requirements.txt"
    printf "Press Enter to close this window..."
    read _unused
    exit 1
fi

python_version=$("$PYTHON_BIN" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
PY
)

if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1; then
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)
PY
    echo "Python 3.12 is required to run sb3topy."
    echo "Found Python $python_version at: $(command -v "$PYTHON_BIN")"
    echo "Install Python 3.12, then run: python3 -m pip install -r requirements.txt"
    printf "Press Enter to close this window..."
    read _unused
    exit 1
fi

export PYTHONPATH="$APP_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

missing=$("$PYTHON_BIN" - <<'PY'
import importlib.util

packages = {
    "pygame": "pygame",
    "requests": "requests",
    "customtkinter": "customtkinter",
    "tkinterdnd2": "tkinterdnd2",
    "CairoSVG": "cairosvg",
}

missing = [
    name for name, module in packages.items()
    if importlib.util.find_spec(module) is None
]
print(" ".join(missing))
PY
)

if [ -n "$missing" ]; then
    echo "Missing required Python packages: $missing"
    printf "Install them now with '$PYTHON_BIN -m pip install -r requirements.txt'? [y/N] "
    read answer
    case "$answer" in
        [Yy]|[Yy][Ee][Ss])
            "$PYTHON_BIN" -m pip install -r requirements.txt
            status=$?
            if [ "$status" -ne 0 ]; then
                echo
                echo "Package installation failed."
                printf "Press Enter to close this window..."
                read _unused
                exit "$status"
            fi
            ;;
        *)
            echo "Cannot run sb3topy until the required packages are installed."
            printf "Press Enter to close this window..."
            read _unused
            exit 1
            ;;
    esac
fi

"$PYTHON_BIN" -m sb3topy --gui
status=$?

if [ "$status" -ne 0 ]; then
    echo
    echo "sb3topy exited with an error."
    echo "If dependencies are missing, run: $PYTHON_BIN -m pip install -r requirements.txt"
    printf "Press Enter to close this window..."
    read _unused
fi

exit "$status"
