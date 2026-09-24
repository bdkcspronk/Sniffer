$ErrorActionPreference = 'Stop'

$ProjectDirectory = $PSScriptRoot
$SystemScript = Join-Path $ProjectDirectory 'run_system.py'

if (-not (Test-Path $SystemScript)) {
    throw "run_system.py was not found at: $SystemScript"
}

$PythonCandidates = @(
    (Join-Path $ProjectDirectory '.venv\Scripts\python.exe'),
    (Join-Path $env:USERPROFILE '.platformio\penv\Scripts\python.exe')
)

$PythonExecutable = $PythonCandidates |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if (-not $PythonExecutable) {
    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $PythonExecutable = $PythonCommand.Source
    }
}

if (-not $PythonExecutable) {
    throw 'Python was not found. Install Python or PlatformIO before running this script.'
}

Set-Location $ProjectDirectory
& $PythonExecutable $SystemScript @args
exit $LASTEXITCODE
