#!/usr/bin/env bash
# ログイン設定から呼び出し、agentの接続先をBash用の設定として出力する。
set -euo pipefail

for tool in ssh-agent ssh-add flock; do
  command -v "$tool" >/dev/null || { echo "必要なコマンドがありません: $tool" >&2; exit 1; }
done

# 他の用途のagentとは分離し、同時ログイン時の重複起動を防ぐ。
agent_dir="$HOME/.ssh/atoyomin-agent"
umask 077
mkdir -p "$agent_dir"
chmod 700 "$agent_dir"
export SSH_AUTH_SOCK="$agent_dir/agent.sock"
exec 9>"$agent_dir/lock"
flock -x 9
status=0
ssh-add -l >/dev/null 2>&1 || status=$?
if [ "$status" -eq 2 ]; then
  # 終了済みagentが残したソケットだけを取り除く。
  if [ -e "$SSH_AUTH_SOCK" ] && [ ! -S "$SSH_AUTH_SOCK" ]; then
    echo "ソケット以外のファイルが存在します: $SSH_AUTH_SOCK" >&2
    exit 1
  fi
  rm -f "$SSH_AUTH_SOCK"
  ssh-agent -a "$SSH_AUTH_SOCK" -s 9>&- >/dev/null
elif [ "$status" -ne 0 ] && [ "$status" -ne 1 ]; then
  echo "SSH agentの確認に失敗しました。" >&2
  exit 1
fi
printf 'export SSH_AUTH_SOCK=%q\n' "$SSH_AUTH_SOCK"
