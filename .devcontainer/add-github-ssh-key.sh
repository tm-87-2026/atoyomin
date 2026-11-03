#!/usr/bin/env bash
# 対話可能なホストのターミナルで、必要な鍵だけをagentへ登録する。
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
key=${1:-"$HOME/.ssh/id_ed25519"}
if [ "$#" -gt 1 ] || [ ! -f "$key" ] || [ ! -f "$key.pub" ]; then
  echo "使い方: bash .devcontainer/add-github-ssh-key.sh [秘密鍵のパス]" >&2
  echo "秘密鍵と対応する.pubファイルが必要です。" >&2
  exit 1
fi
agent_env=$(bash "$script_dir/ssh-agent-env.sh")
eval "$agent_env"
fingerprint=$(ssh-keygen -lf "$key.pub" | awk '{print $2}')
if ssh-add -l 2>/dev/null | awk '{print $2}' | grep -Fxq -- "$fingerprint"; then
  echo "指定した鍵は登録済みです。"
  exit 0
fi
if [ ! -t 0 ]; then
  echo "鍵の登録は、人が操作するWSLターミナルで実行してください。" >&2
  exit 1
fi
ssh-add "$key"
