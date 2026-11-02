#!/usr/bin/env bash
# 実際のPATを使わず、ファイルの読み直しとghへの受け渡しを検証する。
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$work_dir/bin" "$work_dir/repo/tools"
cp "$repo_dir/tools/gh-projects.sh" "$work_dir/repo/tools/gh-projects.sh"
env_file="$work_dir/repo/.env.github-projects"
runner="$work_dir/repo/tools/gh-projects.sh"
cat > "$work_dir/bin/gh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
[ "$GH_TOKEN" = "$TEST_EXPECTED_TOKEN" ]
[ "$GH_HOST" = github.com ]
[ -z "${GITHUB_TOKEN:-}" ]
[ -z "${GH_DEBUG:-}" ]
printf '%s\n' "$@" > "$TEST_ARGUMENTS"
exit "${TEST_GH_STATUS:-0}"
SH
chmod +x "$work_dir/bin/gh"
export PATH="$work_dir/bin:$PATH" TEST_ARGUMENTS="$work_dir/arguments"
export GH_TOKEN=old_token GITHUB_TOKEN=old_token GH_DEBUG=api
for test_value in missing empty invalid multiline duplicate command; do
  rm -f "$env_file" "$TEST_ARGUMENTS"
  case "$test_value" in
    empty) : > "$env_file" ;;
    invalid) printf 'export GH_TOKEN=github_pat_fake\n' > "$env_file" ;;
    multiline) printf 'GH_TOKEN=github_pat_fake\nunexpected\n' > "$env_file" ;;
    duplicate) printf 'GH_TOKEN=github_pat_fake\nGH_TOKEN=github_pat_other\n' > "$env_file" ;;
    command) printf 'GH_TOKEN=$(touch "%s")\n' "$work_dir/executed" > "$env_file" ;;
  esac
  if bash "$runner" project list > "$work_dir/output" 2>&1; then
    echo "PAT不備を拒否しませんでした: $test_value" >&2
    exit 1
  fi
  [ ! -e "$TEST_ARGUMENTS" ]
  [ ! -e "$work_dir/executed" ]
done
export TEST_EXPECTED_TOKEN=github_pat_fake
printf 'GH_TOKEN=%s\n' "$TEST_EXPECTED_TOKEN" > "$env_file"
bash -x "$runner" project list --owner 'owner with spaces' > "$work_dir/output" 2>&1
printf 'project\nlist\n--owner\nowner with spaces\n' > "$work_dir/expected-arguments"
cmp "$TEST_ARGUMENTS" "$work_dir/expected-arguments"
! grep -q github_pat_fake "$work_dir/output"
# envファイルを差し替えても次の実行で新しいPATを利用する。
export TEST_EXPECTED_TOKEN=github_pat_updated
printf 'GH_TOKEN=%s\n' "$TEST_EXPECTED_TOKEN" > "$work_dir/repo/.env.github-projects.new"
mv "$work_dir/repo/.env.github-projects.new" "$env_file"
bash "$runner" api graphql -f 'query={viewer{login}}'
# コメント・空行・CRLF・末尾改行なしも扱い、呼び出し元のディレクトリに依存しない。
printf '# comment\r\n\r\nGH_TOKEN=%s' "$TEST_EXPECTED_TOKEN" > "$env_file"
(cd "$work_dir" && bash "$runner" project list)
if bash "$runner" auth login > "$work_dir/output" 2>&1; then
  echo '認証設定を変更するコマンドを拒否しませんでした。' >&2
  exit 1
fi
export TEST_GH_STATUS=7
test_status=0
bash "$runner" project list || test_status=$?
[ "$test_status" -eq 7 ]
echo 'Projects env file tests passed'
