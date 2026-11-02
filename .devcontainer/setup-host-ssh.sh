#!/usr/bin/env bash
# ホストのBashログイン設定に、共通agent処理を一度だけ登録する。
set -euo pipefail
if [ -f /.dockerenv ]; then
  echo "コンテナの外にあるWSLターミナルで実行してください。" >&2
  exit 1
fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
profile="$HOME/.profile"
# Bashが実際に読み込む、最優先の個人ログイン設定を選ぶ。
for candidate in "$HOME/.bash_profile" "$HOME/.bash_login"; do
  if [ -f "$candidate" ]; then
    profile=$candidate
    break
  fi
done
if [ -L "$profile" ]; then
  echo "シンボリックリンクのログイン設定には自動登録しません: $profile" >&2
  exit 1
fi
# 不完全なブロックで既存設定を削除しないよう、先に対応を確認する。
if [ -f "$profile" ]; then
  awk '
    /^# BEGIN (env-28 temporary agent test|atoyomin SSH agent)$/ { if (inside) exit 1; inside=1; next }
    /^# END (env-28 temporary agent test|atoyomin SSH agent)$/ { if (!inside) exit 1; inside=0 }
    END { if (inside) exit 1 }
  ' "$profile" || { echo "既存のagent設定ブロックを確認してください。" >&2; exit 1; }
fi
agent_env=$(bash "$script_dir/ssh-agent-env.sh")
tmp_file=$(mktemp "$HOME/.atoyomin-profile.XXXXXX")
trap 'rm -f "$tmp_file"' EXIT
if [ -f "$profile" ]; then
  awk '
    /^# BEGIN (env-28 temporary agent test|atoyomin SSH agent)$/ { inside=1; next }
    /^# END (env-28 temporary agent test|atoyomin SSH agent)$/ { inside=0; next }
    !inside { print }
  ' "$profile" > "$tmp_file"
fi
{
  printf '\n# BEGIN atoyomin SSH agent\n'
  printf 'if [ -n "${BASH_VERSION:-}" ] && [ -f %q ]; then\n' "$script_dir/ssh-agent-env.sh"
  printf '  if atoyomin_agent_env=$(bash %q); then\n' "$script_dir/ssh-agent-env.sh"
  printf '    eval "$atoyomin_agent_env"\n  fi\n  unset atoyomin_agent_env\nfi\n'
  printf '# END atoyomin SSH agent\n'
} >> "$tmp_file"
if [ -f "$profile" ]; then
  backup=$(mktemp "$profile.atoyomin-backup.XXXXXX")
  cp -p -- "$profile" "$backup"
  chmod --reference="$profile" "$tmp_file"
  echo "既存設定のバックアップ: $backup"
fi
mv -- "$tmp_file" "$profile"
eval "$agent_env"
echo "ログイン設定を更新しました: $profile"
echo '次に鍵を登録してください: bash .devcontainer/add-github-ssh-key.sh'
echo 'その後、VS Codeを開き直してコンテナへ接続してください。'
