#!/usr/bin/env bash
# ignore対象のenvファイルからPATを読み、そのghプロセスだけに渡す。
set +x
set -euo pipefail
case "${1:-}" in
  issue|pr|project|api) ;;
  *)
    echo '使い方: bash tools/gh.sh <issue|pr|project|api> [引数...]' >&2
    exit 1
    ;;
esac
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
token_file="$repo_dir/.env.github"
if [ ! -f "$token_file" ] || [ ! -r "$token_file" ]; then
  echo 'GitHub API用PATを読み取れません。docs/development/github-api.mdの設定手順を確認してください。' >&2
  exit 1
fi
github_token=
token_found=0
# sourceやevalは使わず、コメント・空行と引用符なしのGH_TOKEN=値だけを読む。
while IFS= read -r line || [ -n "$line" ]; do
  line=${line%$'\r'}
  case "$line" in
    ''|\#*) continue ;;
    GH_TOKEN=*)
      if [ "$token_found" -eq 1 ]; then
        echo 'GH_TOKENが重複しています。' >&2
        exit 1
      fi
      github_token=${line#GH_TOKEN=}
      token_found=1
      ;;
    *) echo 'envファイルはGH_TOKEN=値の形式で指定してください。' >&2; exit 1 ;;
  esac
done < "$token_file"
if [[ ! $github_token =~ ^github_pat_[A-Za-z0-9_]+$ ]]; then
  echo 'GH_TOKENには引用符なしのfine-grained PATを指定してください。' >&2
  exit 1
fi
export GH_TOKEN="$github_token"
export GH_HOST=github.com
unset github_token line token_found GH_DEBUG GITHUB_TOKEN
exec gh "$@"
