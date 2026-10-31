#!/usr/bin/env sh

set -eu

credential_dir="$HOME/.config/atoyomin"
mkdir -p "$credential_dir"
chmod 700 "$credential_dir"

git config --global url."https://github.com/".insteadOf "git@github.com:"
# このリポジトリでは、ホストから転送された認証情報を先に使わない。
credential_key='credential.https://github.com/tm-87-2026/atoyomin.git'
git config --global "$credential_key.useHttpPath" true
git config --global --replace-all "$credential_key.helper" ''
git config --global --add "$credential_key.helper" 'store --file ~/.config/atoyomin/credentials'
