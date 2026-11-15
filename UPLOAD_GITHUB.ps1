#Requires -Version 5.1
# Upload the entire project into the *root* of the existing GitHub repository.
# A temporary clone preserves remote history. No force-push is used.
$ErrorActionPreference = 'Stop'
$repoUrl = 'https://github.com/gkhkfmkh/playerok_universal_fixed.git'
$projectRoot = Split-Path -Parent $PSCommandPath
$requiredFiles = @('server.py', 'bot.py', 'requirements.txt', 'tgbot', 'core', 'playerokapi')
$temporaryCheckout = Join-Path ([System.IO.Path]::GetTempPath()) ('playerok-upload-' + [guid]::NewGuid().ToString('N'))

function Run-Git {
    param([string[]] $Arguments)
    & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ('Git failed with exit code ' + $LASTEXITCODE + ': git ' + ($Arguments -join ' '))
    }
}

try {
    foreach ($relative in $requiredFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $projectRoot $relative))) {
            throw ('Missing required project path: ' + $relative + '. Unzip the entire archive first.')
        }
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git is not installed. Install Git for Windows from https://git-scm.com/download/win'
    }

    Write-Host '1/4  Cloning your GitHub repository...'
    Run-Git @('clone', '--', $repoUrl, $temporaryCheckout)

    Write-Host '2/4  Replacing old repository files with the complete project...'
    # Intentionally clear tracked content in the temporary clone; never touch the actual source folder.
    # This removes the old nested "playerok-universal-main" folder.
    Get-ChildItem -LiteralPath $temporaryCheckout -Force | Where-Object { $_.Name -ne '.git' } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
    # The distributed ZIP contains only source files; exclude typical local credentials and caches.
    $skip = @('.git', '.venv', 'venv', '.env', '__pycache__', 'bot_settings', 'bot_data', 'modules', 'logs', '.temp', '.idea', '.vscode')
    Get-ChildItem -LiteralPath $projectRoot -Force | Where-Object { $_.Name -notin $skip } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $temporaryCheckout $_.Name) -Recurse -Force
    }
    Run-Git @('-C', $temporaryCheckout, 'add', '-A')
    $stagedChanges = & git -C $temporaryCheckout diff --cached --name-only
    if ($LASTEXITCODE -ne 0) { throw 'Unable to review staged changes.' }
    if (-not $stagedChanges) {
        Write-Host 'No changes: GitHub is already up to date.'
        exit 0
    }

    $configuredName = & git -C $temporaryCheckout config user.name
    $configuredEmail = & git -C $temporaryCheckout config user.email
    if (-not $configuredName) {
        $configuredName = Read-Host 'Git commit name (for example, your GitHub username)'
        if (-not $configuredName) { throw 'Git commit name is required.' }
        Run-Git @('-C', $temporaryCheckout, 'config', 'user.name', $configuredName)
    }
    if (-not $configuredEmail) {
        $configuredEmail = Read-Host 'Git email (can be your GitHub noreply address)'
        if (-not $configuredEmail) { throw 'Git email is required.' }
        Run-Git @('-C', $temporaryCheckout, 'config', 'user.email', $configuredEmail)
    }

    Write-Host '3/4  Creating one commit with all project files...'
    Run-Git @('-C', $temporaryCheckout, 'commit', '-m', 'Deploy Playerok Universal at repository root')
    Write-Host '4/4  Pushing commit to GitHub (authentication may be requested)...'
    Run-Git @('-C', $temporaryCheckout, 'push', 'origin', 'HEAD:main')
    Write-Host ''
    Write-Host 'SUCCESS. GitHub now has server.py and bot.py at repository root.'
    Write-Host ('Repository: ' + $repoUrl)
    Write-Host 'Hosting startup filename: server.py'
    exit 0
}
catch {
    Write-Host ''
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'Check Git installation, access to the repository, GitHub sign-in and internet connection.'
    exit 1
}
finally {
    if (Test-Path -LiteralPath $temporaryCheckout) {
        try { Remove-Item -LiteralPath $temporaryCheckout -Recurse -Force -ErrorAction Stop }
        catch { Write-Warning ('Temporary directory could not be cleaned: ' + $temporaryCheckout) }
    }
}
