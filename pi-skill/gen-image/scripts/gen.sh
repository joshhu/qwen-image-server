#!/usr/bin/env bash
# 用法：gen.sh "<prompt>" <out.png> [WxH] [steps]
set -euo pipefail
PROMPT="$1"; OUT="$2"; SIZE="${3:-1344x768}"; STEPS="${4:-40}"
ENDPOINT="${IMAGE_API_URL:?請設定 IMAGE_API_URL，例如 http://<AMD-IP>:7860}"
BODY="$(jq -n --arg p "$PROMPT" --arg s "$SIZE" --argjson st "$STEPS" \
        '{prompt:$p, size:$s, steps:$st, n:1, response_format:"b64_json"}')"

if ! RESP="$(curl -sS --fail-with-body --max-time 1800 "${ENDPOINT%/}/v1/images/generations" \
      -H 'Content-Type: application/json' -d "$BODY")"; then
  echo "error: $RESP" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
# tr -d '\r'：Windows 版 jq 會輸出 CRLF
printf '%s' "$RESP" | jq -r '.data[0].b64_json' | tr -d '\r\n' | base64 -d > "$OUT"
echo "saved: $OUT ($SIZE)"
