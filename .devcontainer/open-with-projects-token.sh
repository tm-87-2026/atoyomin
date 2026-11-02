#!/usr/bin/env bash
# WSLホストで実行し、Windowsの資格情報ストアのPATをVS Codeへ渡す。
set +x
set -euo pipefail
if [ -f /.dockerenv ]; then
  echo "コンテナの外にあるWSLターミナルで実行してください。" >&2
  exit 1
fi
for required in powershell.exe wslpath code; do
  if ! command -v "$required" >/dev/null 2>&1; then
    echo "WSLホストで $required を利用できる状態にしてください。" >&2
    exit 1
  fi
done
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
token_script=$(wslpath -w "$script_dir/windows-projects-token.ps1")
if ! projects_token=$(powershell.exe -NoProfile -NonInteractive -File "$token_script" -Mode Read); then
  echo "Projects用PATを取得できないため、VS Codeを起動しません。" >&2
  exit 1
fi
projects_token=${projects_token//$'\r'/}
if [[ ! $projects_token =~ ^github_pat_[A-Za-z0-9_]+$ ]]; then
  echo "Projects用PATの取得結果が不正なため、VS Codeを起動しません。" >&2
  exit 1
fi
export GH_TOKEN="$projects_token"
unset projects_token
unset GH_DEBUG GITHUB_TOKEN
# WindowsのVS Code起動と、そこからのWSL接続の両方向へ引き継ぐ。
# 既存の共有設定は残し、GH_TOKENに付いている片方向・パス変換フラグは外す。
projects_wslenv=GH_TOKEN
IFS=: read -r -a projects_shared_vars <<< "${WSLENV:-}"
for projects_shared_var in "${projects_shared_vars[@]}"; do
  if [ -n "$projects_shared_var" ] && [ "${projects_shared_var%%/*}" != GH_TOKEN ]; then
    projects_wslenv+=":$projects_shared_var"
  fi
done
export WSLENV="$projects_wslenv"
unset projects_wslenv projects_shared_vars projects_shared_var
cd -- "$script_dir/.."
code --new-window .
