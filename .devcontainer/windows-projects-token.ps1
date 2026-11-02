# WindowsのghでProjects用PATを登録・取得し、保存元を確認する。
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Register', 'Read')]
    [string]$Mode
)

$ErrorActionPreference = 'Stop'
# ホスト側の環境変数による認証の上書きやHTTPデバッグ出力を避ける。
'GH_TOKEN', 'GITHUB_TOKEN', 'GH_DEBUG', 'GH_CONFIG_DIR' | ForEach-Object {
    Remove-Item "Env:$_" -ErrorAction SilentlyContinue
}

try {
    $gh = (Get-Command gh.exe -ErrorAction Stop).Source
    if ($Mode -eq 'Register') {
        $secret = Read-Host 'Projects用fine-grained PAT' -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
        try {
            $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
            if ($token -notmatch '^github_pat_[A-Za-z0-9_]+$') {
                throw 'fine-grained PATを入力してください。'
            }
            $token | & $gh auth login --hostname github.com --with-token --git-protocol ssh 2>$null
            if ($LASTEXITCODE -ne 0) {
                throw 'PATの登録に失敗しました。期限と組織のポリシーを確認してください。'
            }
        } finally {
            $token = $null
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
            $secret.Dispose()
        }
    }

    # --jsonの終了コードだけでは認証成功を判断できないため、stateも確認する。
    $statusJson = & $gh auth status --hostname github.com --json hosts 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw 'Windowsのghの認証状態を確認できません。'
    }
    $status = $statusJson | ConvertFrom-Json
    $active = @($status.hosts.'github.com' | Where-Object { $_.active })
    if ($active.Count -ne 1 -or $active[0].state -ne 'success' -or $active[0].tokenSource -ne 'keyring') {
        throw '有効なPATがWindowsの資格情報ストアにありません。平文へのフォールバックは利用しません。登録直後の場合はgh auth statusで保存先を確認し、平文保存されていればgh auth logoutで削除してPATを失効してください。'
    }
    if ($Mode -eq 'Register') {
        Write-Output 'Windowsの資格情報ストアへの登録を確認しました。'
        exit 0
    }
    $token = & $gh auth token --hostname github.com --user $active[0].login 2>$null
    if ($LASTEXITCODE -ne 0 -or $token -notmatch '^github_pat_[A-Za-z0-9_]+$') {
        throw 'fine-grained PATを取得できません。'
    }
    # 呼び出し元のスクリプトが捕捉する出力。ターミナルからReadを直接実行しない。
    Write-Output $token
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
} finally {
    $token = $null
}
