#!/usr/bin/env bash
# Rebuild the (non-persistent) toolchain in a fresh container. Safe to re-run.
# Installs: Python venv + packages, Piper voices (commercial-safe), Whisper model, Remotion node_modules.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${MUSEVID_VENV:-$HOME/venv-video}"
MODELS="${MUSEVID_MODELS:-$HOME/models}"

for t in ffmpeg ffprobe node npm python3; do command -v "$t" >/dev/null || { echo "missing $t"; exit 1; }; done

[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -r "$ROOT/pipeline/requirements.txt"

mkdir -p "$MODELS/piper"
HF=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US
for v in joe/medium/en_US-joe-medium libritts_r/medium/en_US-libritts_r-medium; do
  for ext in .onnx .onnx.json; do
    f="$MODELS/piper/$(basename "$v")$ext"
    [ -s "$f" ] || curl -fsSL -o "$f" "$HF/$v$ext"
  done
done

MUSEVID_WHISPER_DIR="$MODELS/whisper" "$VENV/bin/python" -c "
from faster_whisper import WhisperModel
WhisperModel('small.en', device='cpu', compute_type='int8', download_root='$MODELS/whisper')
print('whisper small.en ready')"

(cd "$ROOT/animation" && npm ci --no-fund --no-audit)
echo "setup complete — venv: $VENV, models: $MODELS"
