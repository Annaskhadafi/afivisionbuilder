#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
root="$(CDPATH= cd -- "$script_dir/.." && pwd)"
runtime_dir="${XDG_DATA_HOME:-$HOME/.local/share}/VisoNode/ai-runtime"

base_python=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --runtime-dir)
            [[ -n "${2:-}" ]] || { echo "--runtime-dir requires a path" >&2; exit 2; }
            runtime_dir="$2"
            shift 2
            ;;
        --python)
            [[ -n "${2:-}" ]] || { echo "--python requires a path" >&2; exit 2; }
            base_python="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

requirements="$root/requirements-ai.txt"
dependency_installer="$root/install_ai_dependencies.py"
venv="$runtime_dir/.venv"

if [[ ! -f "$requirements" ]]; then
    echo "requirements-ai.txt was not found at $requirements" >&2
    exit 1
fi
if [[ ! -f "$dependency_installer" ]]; then
    echo "AI dependency installer was not found at $dependency_installer" >&2
    exit 1
fi

mkdir -p "$runtime_dir"
# Keep the external AI interpreter isolated from extension modules bundled
# beside the compiled desktop executable.
cd "$runtime_dir"
needs_venv=true
if [[ -x "$venv/bin/python" ]] && "$venv/bin/python" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 3)' >/dev/null 2>&1; then
    needs_venv=false
fi
if [[ "$needs_venv" == true ]]; then
    created=false
    candidates=()
    [[ -n "$base_python" ]] && candidates+=("$base_python")
    candidates+=(python3.12 python3 python)
    for candidate in "${candidates[@]}"; do
        if [[ "$candidate" != */* ]] && ! command -v "$candidate" >/dev/null 2>&1; then
            continue
        fi
        candidate_path="$candidate"
        if [[ "$candidate" != */* ]]; then
            candidate_path="$(command -v "$candidate")"
        fi
        if ! "$candidate_path" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 3)' >/dev/null 2>&1; then
            continue
        fi
        if "$candidate_path" -m venv --clear "$venv"; then
            created=true
            break
        fi
    done
    if [[ "$created" != true ]]; then
        echo "Could not create the AI runtime. Python 3.12 with venv support is required." >&2
        exit 1
    fi
fi

python="$venv/bin/python"
installer_args=(-P "$dependency_installer" --python "$python" --runtime-dir "$runtime_dir" --cuda-wheel auto)
if [[ "$(uname -s)" == Darwin ]]; then
    echo "Installing the macOS AI runtime with CPU and Apple Metal (MPS) support."
fi
# The Python installer selects the pinned runtime from GPU compute capability.
"$python" "${installer_args[@]}"

echo
echo "AI runtime installed. VisoNode will use:"
echo "$python"
