#!/usr/bin/env bash
# 実際のPATを使わず、ファイルの読み直しとghへの受け渡しを検証する。
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$work_dir/bin" "$work_dir/secrets"
cp "$repo_dir/tools/gh-projects.sh" "$work_dir/gh-projects.sh"
# テスト用コピーだけマウント先を一時ディレクトリに置き換える。
sed -i "s|/run/atoyomin-projects/token|$work_dir/secrets/token|" "$work_dir/gh-projects.sh"
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
for test_value in missing empty invalid multiline; do
  rm -f "$work_dir/secrets/token" "$TEST_ARGUMENTS"
  case "$test_value" in
    empty) : > "$work_dir/secrets/token" ;;
    invalid) printf 'export GH_TOKEN=github_pat_fake\n' > "$work_dir/secrets/token" ;;
    multiline) printf 'github_pat_fake\nunexpected\n' > "$work_dir/secrets/token" ;;
  esac
  if bash "$work_dir/gh-projects.sh" project list > "$work_dir/output" 2>&1; then
    echo "PAT不備を拒否しませんでした: $test_value" >&2
    exit 1
  fi
  [ ! -e "$TEST_ARGUMENTS" ]
done
export TEST_EXPECTED_TOKEN=github_pat_fake
printf '%s\n' "$TEST_EXPECTED_TOKEN" > "$work_dir/secrets/token"
bash -x "$work_dir/gh-projects.sh" project list --owner 'owner with spaces' > "$work_dir/output" 2>&1
printf 'project\nlist\n--owner\nowner with spaces\n' > "$work_dir/expected-arguments"
cmp "$TEST_ARGUMENTS" "$work_dir/expected-arguments"
! grep -q github_pat_fake "$work_dir/output"
# ホストでファイルを差し替えても次の実行で新しいPATを利用する。
export TEST_EXPECTED_TOKEN=github_pat_updated
printf '%s\n' "$TEST_EXPECTED_TOKEN" > "$work_dir/secrets/new-token"
mv "$work_dir/secrets/new-token" "$work_dir/secrets/token"
bash "$work_dir/gh-projects.sh" api graphql -f 'query={viewer{login}}'
if bash "$work_dir/gh-projects.sh" auth login > "$work_dir/output" 2>&1; then
  echo '認証設定を変更するコマンドを拒否しませんでした。' >&2
  exit 1
fi
export TEST_GH_STATUS=7
test_status=0
bash "$work_dir/gh-projects.sh" project list || test_status=$?
[ "$test_status" -eq 7 ]
echo 'Projects token file tests passed'
