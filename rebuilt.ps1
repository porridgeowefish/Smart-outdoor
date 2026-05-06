param(
    [switch]$deldb,
    [switch]$Install,
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$LogDir = Join-Path $RootDir ".logs"
$BackendOutLog = Join-Path $LogDir "backend.out.log"
$BackendErrLog = Join-Path $LogDir "backend.err.log"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $RootDir
    )

    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-DockerCompose {
    param([string[]]$Arguments)

    Push-Location $RootDir
    try {
        & docker compose @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Stop-ProcessOnPort {
    param([int]$Port)

    $connections = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        if ($processId -and $processId -ne $PID) {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Stopping process on port ${Port}: PID=$processId Name=$($process.ProcessName)"
                Stop-Process -Id $processId -Force
            }
        }
    }
}

function Import-DotEnv {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return
    }

    Write-Host "Loading env file: $Path"
    Get-Content -Path $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $parts = $line.Split("=", 2)
        $name = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if ($name) {
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

function Wait-PostgresHealthy {
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        $status = (& docker inspect --format "{{.State.Health.Status}}" smart_outdoor_postgres 2>$null)
        if ($LASTEXITCODE -eq 0 -and $status -eq "healthy") {
            Write-Host "PostgreSQL is healthy."
            return
        }
        Start-Sleep -Seconds 2
    }

    Write-Host "PostgreSQL logs:" -ForegroundColor Yellow
    & docker logs smart_outdoor_postgres --tail 80
    throw "PostgreSQL did not become healthy in time."
}

function Wait-BackendReady {
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/openapi.json" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Host "Backend is ready: http://127.0.0.1:8000/openapi.json"
                return
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    Write-Host "Backend stdout log: $BackendOutLog" -ForegroundColor Yellow
    Write-Host "Backend stderr log: $BackendErrLog" -ForegroundColor Yellow
    if (Test-Path $BackendErrLog) {
        Get-Content $BackendErrLog -Tail 80
    }
    throw "Backend did not become ready in time."
}

Write-Step "Checking tools"
Require-Command "docker"
Require-Command "python"
Invoke-Checked -FilePath "docker" -Arguments @("compose", "version")

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Import-DotEnv -Path (Join-Path $BackendDir ".env")

Write-Step "Stopping existing backend on port 8000"
Stop-ProcessOnPort -Port 8000

if ($deldb) {
    Write-Step "Deleting PostgreSQL data volume and rebuilding database"
    Invoke-DockerCompose -Arguments @("down", "-v", "--remove-orphans")
    Invoke-DockerCompose -Arguments @("up", "-d", "postgres")
}
else {
    Write-Step "Starting PostgreSQL without deleting data"
    Invoke-DockerCompose -Arguments @("up", "-d", "postgres")
}
Wait-PostgresHealthy

if ($Install) {
    Write-Step "Installing backend package"
    Invoke-Checked -FilePath "python" -Arguments @("-m", "pip", "install", "-e", ".") -WorkingDirectory $BackendDir
}

Write-Step "Starting backend"
$env:DATABASE_URL = "postgresql+psycopg://smart_outdoor:smart_outdoor_dev_password@127.0.0.1:5432/smart_outdoor"
$env:PYTHONPATH = $BackendDir

$uvicornArgs = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000")
if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

$backendProcess = Start-Process `
    -FilePath "python" `
    -ArgumentList $uvicornArgs `
    -WorkingDirectory $BackendDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $BackendOutLog `
    -RedirectStandardError $BackendErrLog `
    -PassThru

Write-Host "Backend process started: PID=$($backendProcess.Id)"
Write-Host "Logs:"
Write-Host "  stdout: $BackendOutLog"
Write-Host "  stderr: $BackendErrLog"

Wait-BackendReady

Write-Step "Done"
Write-Host "PostgreSQL: 127.0.0.1:5432"
Write-Host "Backend API: http://127.0.0.1:8000"
Write-Host "OpenAPI: http://127.0.0.1:8000/openapi.json"
