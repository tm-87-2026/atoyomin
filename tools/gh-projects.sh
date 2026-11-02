#!/usr/bin/env bash
# ホストから読み取り専用で共有したPATを、そのghプロセスだけに渡す。
set +x
set -euo pipefail
if [ "${1:-}" != project ] && { [ "${1:-}" != api ] || [ "${2:-}" != graphql ]; }; then
  echo '使い方: bash tools/gh-projects.sh project <操作> [引数...]' >&2
  echo 'GraphQL: bash tools/gh-projects.sh api graphql [引数...]' >&2
  exit 1
fi
token_file=/run/atoyomin-projects/token
if [ ! -f "$token_file" ] || [ ! -r "$token_file" ]; then
  echo 'Projects用PATを読み取れません。docs/development/github-projects.mdの設定手順を確認してください。' >&2
  exit 1
fi
projects_token=$(< "$token_file")
if [[ ! $projects_token =~ ^github_pat_[A-Za-z0-9_]+$ ]]; then
  echo 'PATファイルにはfine-grained PATだけを1行で保存してください。' >&2
  exit 1
fi
export GH_TOKEN="$projects_token"
export GH_HOST=github.com
unset projects_token GH_DEBUG GITHUB_TOKEN
exec gh "$@"
