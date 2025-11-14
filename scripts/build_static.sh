#!/usr/bin/env bash
set -euo pipefail

# Static build helper for IstanbulPropTech using django-distill
# - Prompts for base path, media base, inline-data option, collectstatic, and output dir
# - Exports static site with django-distill
# - Optionally rewrites absolute URLs in generated HTML for subpath hosting

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

if [[ ! -f manage.py ]]; then
  echo "Error: manage.py not found. Run this script from the repo root or via bash scripts/build_static.sh" >&2
  exit 1
fi

echo "=== IstanbulPropTech static build ==="

# Defaults
DEFAULT_OUT="distill_out"
DEFAULT_BASE_PATH="/"
DEFAULT_MEDIA_BASE="/media"

read -rp "Output directory [${DEFAULT_OUT}]: " OUT_DIR
OUT_DIR=${OUT_DIR:-$DEFAULT_OUT}

read -rp "Serve under a base path (e.g. / or /app) [${DEFAULT_BASE_PATH}]: " BASE_PATH
BASE_PATH=${BASE_PATH:-$DEFAULT_BASE_PATH}

read -rp "Media base URL (e.g. /media or https://cdn.example.com/media) [${DEFAULT_MEDIA_BASE}]: " MEDIA_BASE
MEDIA_BASE=${MEDIA_BASE:-$DEFAULT_MEDIA_BASE}

read -rp "Embed simplified data inline (single-file simplified page)? (y/N): " INLINE_ANS
INLINE_ANS=${INLINE_ANS:-N}

read -rp "Run collectstatic during build? (Y/n): " COLLECT_ANS
COLLECT_ANS=${COLLECT_ANS:-Y}

# Normalize inputs
# Ensure BASE_PATH starts with / and has no trailing slash (except root)
if [[ -n "$BASE_PATH" ]]; then
  if [[ "$BASE_PATH" != /* ]]; then BASE_PATH="/$BASE_PATH"; fi
  if [[ "$BASE_PATH" != "/" ]]; then BASE_PATH="${BASE_PATH%/}"; fi
fi

# Ensure MEDIA_BASE ends with no trailing slash
MEDIA_BASE="${MEDIA_BASE%/}"

INLINE_FLAG=0
if [[ "$INLINE_ANS" =~ ^[Yy]$ ]]; then INLINE_FLAG=1; fi

COLLECT_FLAG=""
if [[ "$COLLECT_ANS" =~ ^[Yy]$ ]]; then COLLECT_FLAG="--collectstatic"; fi

echo
echo "--- Build configuration ---"
echo "Output dir:        $OUT_DIR"
echo "Base path:         $BASE_PATH"
echo "Media base:        $MEDIA_BASE/"
echo "Inline simplified: $INLINE_FLAG"
echo "Collect static:    ${COLLECT_FLAG:+yes}${COLLECT_FLAG:-(no)}"
echo "---------------------------"

mkdir -p "$OUT_DIR"

export SIMPLIFIED_INLINE_DATA="$INLINE_FLAG"

echo "[1/2] Exporting static site with django-distill..."
set -x
python manage.py distill-local $COLLECT_FLAG --force "$OUT_DIR"
set +x

echo "[2/2] Post-processing exported HTML for base/media paths..."

# Rewrite fetch('/api/...') to respect base path when not root
rewrite_api_paths() {
  local file="$1"
  local base="$2"
  if [[ "$base" != "/" && -f "$file" ]]; then
    # Replace fetch('/api/ with fetch('<base>/api/
    sed -i -e "s|fetch('/api/|fetch('${base}/api/|g" "$file"
  fi
}

# Rewrite /media/ to MEDIA_BASE in HTML (images)
rewrite_media_paths() {
  local file="$1"
  local media_base="$2"
  if [[ -f "$file" ]]; then
    sed -i -e "s|/media/|${media_base}/|g" "$file"
  fi
}

# Files to patch if present
INDEX_HTML="$OUT_DIR/index.html"
SIMPLIFIED_HTML="$OUT_DIR/simplified/index.html"

rewrite_api_paths "$INDEX_HTML" "$BASE_PATH"
rewrite_api_paths "$SIMPLIFIED_HTML" "$BASE_PATH"

rewrite_media_paths "$INDEX_HTML" "$MEDIA_BASE"
rewrite_media_paths "$SIMPLIFIED_HTML" "$MEDIA_BASE"

echo
echo "Build complete. Artifacts in: $OUT_DIR"
echo "Deploy by serving $OUT_DIR at: $BASE_PATH"
echo
echo "Notes:"
echo "- If hosting under a subpath, ensure your static host maps $BASE_PATH to $OUT_DIR."
echo "- The simplified page can be data-inline if chosen; mobile map still fetches /api/*."
echo "- Ensure media files are available at ${MEDIA_BASE}/ (upload your MEDIA_ROOT there)."
echo "- Re-run with different answers anytime; previous output is overwritten."

