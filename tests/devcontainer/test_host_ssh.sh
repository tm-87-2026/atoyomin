#!/usr/bin/env bash
# 一時ホームと実際のagentで、ホスト設定の再実行・復旧・鍵登録を検証する。
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work_dir=$(mktemp -d)
export HOME="$work_dir/home"
mkdir -p "$HOME" "$work_dir/scripts"
unset SSH_AUTH_SOCK SSH_AGENT_PID || true
stop_agent() {
  local agent_pid
  while read -r agent_pid; do
    [ -z "$agent_pid" ] || kill "$agent_pid"
  done < <(pgrep -f "^ssh-agent -a $HOME/.ssh/atoyomin-agent/agent.sock -s$" || true)
}
cleanup() { stop_agent; rm -rf "$work_dir"; }
trap cleanup EXIT
cp "$repo_dir"/.devcontainer/*ssh*.sh "$work_dir/scripts/"
# テスト用コピーだけコンテナ判定先を存在しないパスに変え、隔離ホームへ設定する。
sed -i "s|/.dockerenv|$work_dir/not-a-container|" "$work_dir/scripts/setup-host-ssh.sh"
printf '# keep existing settings\nexport EXISTING_SETTING=yes\n# BEGIN env-28 temporary agent test\nexport SSH_AUTH_SOCK=/old/socket\n# END env-28 temporary agent test\n' > "$HOME/.profile"
bash "$work_dir/scripts/setup-host-ssh.sh" >/dev/null
bash "$work_dir/scripts/setup-host-ssh.sh" >/dev/null
[ "$(grep -c '^# BEGIN atoyomin SSH agent$' "$HOME/.profile")" -eq 1 ]
! grep -q '/old/socket' "$HOME/.profile"
grep -q 'export EXISTING_SETTING=yes' "$HOME/.profile"
# 登録したログイン設定から接続先が取得されることを確認する。
eval "$(bash "$work_dir/scripts/ssh-agent-env.sh")"
expected_socket=$SSH_AUTH_SOCK
unset SSH_AUTH_SOCK
. "$HOME/.profile"
[ "$SSH_AUTH_SOCK" = "$expected_socket" ]
[ "$EXISTING_SETTING" = yes ]
status=0
ssh-add -l >/dev/null 2>&1 || status=$?
[ "$status" -eq 1 ]
# 複数の同時呼び出しでもagentが一つだけ起動する。
stop_agent
sleep 0.2
for n in {1..8}; do
  bash "$work_dir/scripts/ssh-agent-env.sh" > "$work_dir/env-$n" &
done
wait
[ "$(pgrep -fc "^ssh-agent -a $HOME/.ssh/atoyomin-agent/agent.sock -s$")" -eq 1 ]
for n in {2..8}; do cmp "$work_dir/env-1" "$work_dir/env-$n"; done
# 未登録鍵は非対話実行で拒否し、登録済みなら繰り返し実行できる。
ssh-keygen -q -t ed25519 -N '' -f "$HOME/test-key"
if bash "$work_dir/scripts/add-github-ssh-key.sh" "$HOME/test-key" </dev/null >/dev/null 2>&1; then
  echo '非対話の鍵登録を拒否しませんでした。' >&2
  exit 1
fi
ssh-add "$HOME/test-key" >/dev/null 2>&1
bash "$work_dir/scripts/add-github-ssh-key.sh" "$HOME/test-key" </dev/null >/dev/null
# 優先されるログイン設定を選び、他のファイルを変更しない。
printf '# preferred login file\n' > "$HOME/.bash_profile"
cp "$HOME/.profile" "$work_dir/profile-before"
bash "$work_dir/scripts/setup-host-ssh.sh" >/dev/null
cmp "$HOME/.profile" "$work_dir/profile-before"
grep -q '^# BEGIN atoyomin SSH agent$' "$HOME/.bash_profile"
# 不完全な管理ブロックは元のファイルを保持したまま拒否する。
printf '# BEGIN atoyomin SSH agent\n' > "$HOME/.bash_profile"
cp "$HOME/.bash_profile" "$work_dir/broken-before"
if bash "$work_dir/scripts/setup-host-ssh.sh" >/dev/null 2>&1; then exit 1; fi
cmp "$HOME/.bash_profile" "$work_dir/broken-before"
echo 'host SSH tests passed'
