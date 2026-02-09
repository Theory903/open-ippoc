#!/usr/bin/env bash
# IPPOC Universal Installer - "Sovereignty in One Command"
set -euo pipefail

IPPOC_HOME="${HOME}/.ippoc"
VENV_DIR="${IPPOC_HOME}/venv"
BIN_DIR="${HOME}/.local/bin"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🦞 IPPOC Universal Platform: Starting Installation..."

# 1. Option Parsing
UNINSTALL=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --uninstall) UNINSTALL=true; shift ;;
        *) shift ;;
    esac
done

if [[ "$UNINSTALL" == "true" ]]; then
    echo "🧹 Uninstalling IPPOC..."
    rm -rf "${IPPOC_HOME}"
    rm -f "${BIN_DIR}/ippoc"
    echo "✅ IPPOC removed."
    exit 0
fi

# 2. OS Detection
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_NAME=linux;;
    Darwin*)    OS_NAME=macos;;
    *)          echo "Unsupported OS: ${OS}"; exit 1;;
esac

# 2. Dependency Check (Python 3.10+)
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.10+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PYTHON_VERSION < 3.10" | bc -l) -eq 1 ]]; then
    echo "❌ Error: IPPOC requires Python 3.10+. Found ${PYTHON_VERSION}."
    exit 1
fi

# 3. Create Isolated Environment
echo "📦 Creating isolated environment in ${VENV_DIR}..."
mkdir -p "${IPPOC_HOME}/instances/main/data"
mkdir -p "${IPPOC_HOME}/instances/main/logs"
python3 -m venv "${VENV_DIR}"

# 4. Install Core CLI & Dependencies
echo "🚀 Installing IPPOC core..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -e "${PROJECT_ROOT}"

# 5. Create CLI Shim
mkdir -p "${BIN_DIR}"
cat <<EOF > "${BIN_DIR}/ippoc"
#!/usr/bin/env bash
source "${VENV_DIR}/bin/activate"
export IPPOC_BASE_DIR="${IPPOC_HOME}"
exec python3 -m ippoc.cli.main "\$@"
EOF
chmod +x "${BIN_DIR}/ippoc"

echo "✅ Installation Complete!"
echo "🦞 Run 'ippoc' to begin."
echo "   (Make sure ${BIN_DIR} is in your PATH)"
