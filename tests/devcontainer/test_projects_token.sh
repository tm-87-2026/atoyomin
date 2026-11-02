#!/usr/bin/env bash
# 実際のPATを使わず、起動失敗時の遮断と環境変数での受け渡しを検証する。
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$work_dir/repo/.devcontainer" "$work_dir/bin"
cp "$repo_dir/.devcontainer/open-with-projects-token.sh" "$work_dir/repo/.devcontainer/"
# テスト用コピーでのみWSLホストを模擬する。
sed -i "s|/.dockerenv|$work_dir/not-a-container|" "$work_dir/repo/.devcontainer/open-with-projects-token.sh"
cat > "$work_dir/bin/wslpath" <<'SH'
#!/usr/bin/env bash
printf '%s\n' "$2"
SH
cat > "$work_dir/bin/powershell.exe" <<'SH'
#!/usr/bin/env bash
case "$TEST_TOKEN_MODE" in
  fail) exit 1 ;;
  empty) exit 0 ;;
  invalid) printf 'gho_fake_oauth\n' ;;
  multiline) printf 'github_pat_fake\nunexpected\n' ;;
  success) printf 'github_pat_fake\r\n' ;;
esac
SH
cat > "$work_dir/bin/code" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
[ "$GH_TOKEN" = github_pat_fake ]
[ -z "${GITHUB_TOKEN:-}" ]
[ -z "${GH_DEBUG:-}" ]
[ "$WSLENV" = 'GH_TOKEN:KEEP/p' ]
[ "$PWD" = "$TEST_PROJECT_DIR" ]
[ "$#" -eq 2 ] && [ "$1" = --new-window ] && [ "$2" = . ]
touch "$TEST_LAUNCHED"
SH
chmod +x "$work_dir/bin/"*
export PATH="$work_dir/bin:$PATH"
export TEST_PROJECT_DIR="$work_dir/repo" TEST_LAUNCHED="$work_dir/launched"
export GH_TOKEN=old_token GITHUB_TOKEN=old_token GH_DEBUG=api
export WSLENV='KEEP/p:GH_TOKEN/w'
for TEST_TOKEN_MODE in fail empty invalid multiline; do
  export TEST_TOKEN_MODE
  if bash "$work_dir/repo/.devcontainer/open-with-projects-token.sh" > "$work_dir/output" 2>&1; then
    echo "取得失敗時にVS Codeを起動しました: $TEST_TOKEN_MODE" >&2
    exit 1
  fi
  [ ! -e "$TEST_LAUNCHED" ]
done
export TEST_TOKEN_MODE=success
# 呼び出し側が-xを指定してもPATはログに出さない。
bash -x "$work_dir/repo/.devcontainer/open-with-projects-token.sh" > "$work_dir/output" 2>&1
[ -e "$TEST_LAUNCHED" ]
if grep -q github_pat_fake "$work_dir/output"; then
  echo '起動ログにPATが含まれています。' >&2
  exit 1
fi
echo 'Projects token launcher tests passed'
