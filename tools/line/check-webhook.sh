#!/usr/bin/env bash
set -euo pipefail
set +x
if [[ $# != 1 || ! -t 0 ]]; then
  printf 'Usage: bash tools/line/check-webhook.sh <Webhook URL> (interactive terminal required)\n' >&2
  exit 1
fi
read -r -s -p 'LINE channel secret (hidden): ' line_probe_secret
printf '\n' >&2
trap 'unset line_probe_secret' EXIT
printf '%s' "$line_probe_secret" | deno run --allow-net "$(dirname "$0")/checkWebhook.ts" "$1"
