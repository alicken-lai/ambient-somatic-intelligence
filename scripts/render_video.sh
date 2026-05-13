#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <input_html> <output_mp4>" >&2
  exit 1
fi

INPUT_HTML="$1"
OUTPUT_MP4="$2"

if [[ ! -f "$INPUT_HTML" ]]; then
  echo "Error: input HTML not found: $INPUT_HTML" >&2
  exit 1
fi

if [[ "${INPUT_HTML##*.}" != "html" ]]; then
  echo "Error: input must be an .html file: $INPUT_HTML" >&2
  exit 1
fi

OUTPUT_DIR="$(dirname "$OUTPUT_MP4")"
mkdir -p "$OUTPUT_DIR"

if ! command -v npx >/dev/null 2>&1; then
  echo "Error: npx is not installed. Please install Node.js/npm first." >&2
  exit 1
fi

echo "[render_video] Rendering with HyperFrames..."
echo "[render_video] Input:  $INPUT_HTML"
echo "[render_video] Output: $OUTPUT_MP4"

if ! npx --yes hyperframes --help >/dev/null 2>&1; then
  echo "Error: HyperFrames CLI is unavailable. Run 'npm install' or retry with network access." >&2
  exit 1
fi

if ! npx hyperframes render "$INPUT_HTML" --output "$OUTPUT_MP4"; then
  echo "Error: HyperFrames render failed." >&2
  exit 1
fi

echo "[render_video] Success: $OUTPUT_MP4"
