#!/usr/bin/env bash

set -eu
# トークンをトレース出力に含めない。
set +x

if [[ ! -t 0 ]]; then
  printf '%s\n' 'コンテナ内の対話ターミナルで実行してください。' >&2
  exit 1
fi

sh "$(dirname -- "$0")/configure-github-git.sh"
umask 077
IFS= read -r -s -p 'atoyomin用のfine-grained PAT: ' github_token
printf '\n'
if [[ -z "$github_token" ]]; then
  printf '%s\n' 'PATが空のため保存しませんでした。' >&2
  exit 1
fi

printf 'protocol=https\nhost=github.com\npath=tm-87-2026/atoyomin.git\nusername=x-access-token\npassword=%s\n\n' "$github_token" |
  git credential-store --file "$HOME/.config/atoyomin/credentials" store
unset github_token
printf '%s\n' 'PATを保存しました。git ls-remote origin HEAD で接続を確認してください。'
