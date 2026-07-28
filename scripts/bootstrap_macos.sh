#!/bin/sh
set -eu

CHECK_ONLY=0
if [ "${1:-}" = "--check-only" ]; then
  CHECK_ONLY=1
fi

REPOSITORY="marcostrasto/ecd-spectra"
PLUGIN_ID="ecd-spectra@ecd-spectra"
SETUP_ROOT="${HOME}/Library/Application Support/ECDSpectra"
RUNTIME_ROOT="${SETUP_ROOT}/runtime"
CLI_PREFIX="${SETUP_ROOT}/codex-cli"

codex_works() {
  [ -n "${1:-}" ] && [ -x "$1" ] && "$1" --version >/dev/null 2>&1
}

find_codex() {
  if command -v codex >/dev/null 2>&1; then
    command -v codex
    return
  fi

  app_codex="/Applications/Codex.app/Contents/Resources/codex"
  if [ -x "$app_codex" ]; then
    printf '%s\n' "$app_codex"
    return
  fi

  private_codex="${CLI_PREFIX}/bin/codex"
  if [ -x "$private_codex" ]; then
    printf '%s\n' "$private_codex"
  fi
}

install_private_node() {
  architecture="$(uname -m)"
  case "$architecture" in
    arm64) node_arch="arm64" ;;
    x86_64) node_arch="x64" ;;
    *) printf 'Unsupported macOS architecture: %s\n' "$architecture" >&2; exit 1 ;;
  esac

  version="$(
    curl -fsSL https://nodejs.org/dist/index.tab |
      awk -F '	' 'NR > 1 && $10 != "-" { print $1; exit }'
  )"
  [ -n "$version" ] || {
    printf 'Unable to determine the current Node.js LTS release.\n' >&2
    exit 1
  }

  archive="node-${version}-darwin-${node_arch}.tar.gz"
  node_dir="${RUNTIME_ROOT}/node-${version}-darwin-${node_arch}"
  mkdir -p "$RUNTIME_ROOT" "$SETUP_ROOT"

  if [ ! -x "${node_dir}/bin/node" ]; then
    curl -fsSL "https://nodejs.org/dist/${version}/${archive}" -o "${SETUP_ROOT}/${archive}"
    tar -xzf "${SETUP_ROOT}/${archive}" -C "$RUNTIME_ROOT"
    rm -f "${SETUP_ROOT}/${archive}"
  fi

  printf '%s\n' "${node_dir}/bin/npm"
}

resolve_codex() {
  candidate="$(find_codex || true)"
  if codex_works "$candidate"; then
    printf '%s\n' "$candidate"
    return
  fi

  if command -v npm >/dev/null 2>&1; then
    npm_path="$(command -v npm)"
  else
    npm_path="$(install_private_node)"
  fi

  mkdir -p "$CLI_PREFIX"
  "$npm_path" install --global --prefix "$CLI_PREFIX" @openai/codex
  candidate="${CLI_PREFIX}/bin/codex"
  codex_works "$candidate" || {
    printf 'Codex CLI installation completed, but the CLI is not executable.\n' >&2
    exit 1
  }
  printf '%s\n' "$candidate"
}

if [ "$(uname -s)" != "Darwin" ]; then
  printf 'This bootstrap is intended for macOS.\n' >&2
  exit 1
fi

existing="$(find_codex || true)"
if [ "$CHECK_ONLY" -eq 1 ]; then
  if codex_works "$existing"; then
    printf '{"status":"ready","detail":"Codex CLI is available."}\n'
    exit 0
  fi
  printf '{"status":"setup_required","detail":"Codex CLI and ECD Spectra must be installed."}\n'
  exit 2
fi

CODEX_BIN="$(resolve_codex)"
"$CODEX_BIN" --version
"$CODEX_BIN" plugin marketplace add "$REPOSITORY" --ref main
"$CODEX_BIN" plugin add "$PLUGIN_ID"
"$CODEX_BIN" plugin list

printf '{"status":"complete","detail":"ECD Spectra is installed. Restart Codex and open a new conversation in the PDF project."}\n'
