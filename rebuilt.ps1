param(
    [switch]$deldb,
    [switch]$Install,
    [switch]$Reload,
    [switch]$NoReload,
    [int]$BackendPort = 8000
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$LogDir = Join-Path $RootDir ".logs"
$BackendOutLog = Join-Path $LogDir "backend.out.log"
$BackendErrLog = Join-Path $LogDir "backend.err.log"
$MiddlewareComposeFile = Join-Path $RootDir "docker-compose.middleware.yml"
$PostgresContainerName = "smart_outdoor_postgres_local"

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

function Invoke-MiddlewareCompose {
    param([string[]]$Arguments)

    Push-Location $RootDir
    try {
        & docker compose -f $MiddlewareComposeFile @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "middleware docker compose failed with exit code ${LASTEXITCODE}: $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Get-ListeningProcessIds {
    param([int]$Port)

    $processIds = @()
    $connections = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    $processIds += @($connections | Select-Object -ExpandProperty OwningProcess -Unique)

    $netstatLines = @(netstat -ano | Select-String ":${Port}")
    foreach ($line in $netstatLines) {
        $text = $line.ToString()
        if ($text -match "\sLISTENING\s+(\d+)\s*$") {
            $processIds += [int]$Matches[1]
        }
    }

    return @($processIds | Where-Object { $_ } | Sort-Object -Unique)
}

function Stop-ProcessOnPort {
    param([int]$Port)

    for ($attempt = 1; $attempt -le 5; $attempt++) {
        $processIds = @(Get-ListeningProcessIds -Port $Port)
        if (-not $processIds) {
            return
        }

        foreach ($processId in $processIds) {
            if ($processId -and $processId -ne $PID) {
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "Stopping process on port ${Port}: PID=$processId Name=$($process.ProcessName)"
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                }
            }
        }

        foreach ($processId in $processIds) {
            $spawnedChildren = @(
                Get-CimInstance Win32_Process |
                    Where-Object {
                        $_.ProcessId -ne $PID -and
                        $_.CommandLine -match "spawn_main\(parent_pid=$processId,"
                    }
            )
            foreach ($child in $spawnedChildren) {
                Write-Host "Stopping backend reload child on port ${Port}: PID=$($child.ProcessId) ParentPID=$processId"
                Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue
            }
        }

        Start-Sleep -Milliseconds 500
    }
}

function Stop-BackendUvicornProcesses {
    $processes = @(
        Get-CimInstance Win32_Process |
            Where-Object {
                $_.ProcessId -ne $PID -and
                $_.CommandLine -match "uvicorn" -and
                $_.CommandLine -match "app\.main:app"
            }
    )
    foreach ($process in $processes) {
        Write-Host "Stopping backend uvicorn process: PID=$($process.ProcessId)"
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Ensure-PostgresPortAvailable {
    $published = @(& docker ps --filter "publish=5432" --format "{{.Names}}" 2>$null)
    $published = @($published | Where-Object { $_ })
    foreach ($containerName in $published) {
        if ($containerName -eq $PostgresContainerName) {
            return
        }
        if ($containerName -eq "smart_outdoor_postgres") {
            Write-Host "Stopping legacy local postgres container using port 5432: $containerName" -ForegroundColor Yellow
            & docker stop $containerName | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to stop legacy local postgres container: $containerName"
            }
            continue
        }
        throw "Port 5432 is already published by docker container '$containerName'. Stop it first or change docker-compose.middleware.yml."
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
        $status = (& docker inspect --format "{{.State.Health.Status}}" $PostgresContainerName 2>$null)
        if ($LASTEXITCODE -eq 0 -and $status -eq "healthy") {
            Write-Host "PostgreSQL is healthy."
            return
        }
        Start-Sleep -Seconds 2
    }

    Write-Host "PostgreSQL logs:" -ForegroundColor Yellow
    & docker logs $PostgresContainerName --tail 80
    throw "PostgreSQL did not become healthy in time."
}

function Wait-BackendReady {
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:${BackendPort}/openapi.json" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Host "Backend is ready: http://127.0.0.1:${BackendPort}/openapi.json"
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

Write-Step "Stopping existing backend on port ${BackendPort}"
Stop-ProcessOnPort -Port $BackendPort
Stop-BackendUvicornProcesses

if ($deldb) {
    Write-Step "Deleting local middleware PostgreSQL data volume and rebuilding database"
    Invoke-MiddlewareCompose -Arguments @("down", "-v", "--remove-orphans")
    Ensure-PostgresPortAvailable
    Invoke-MiddlewareCompose -Arguments @("up", "-d", "postgres")
}
else {
    Write-Step "Starting local middleware PostgreSQL without deleting data"
    Ensure-PostgresPortAvailable
    Invoke-MiddlewareCompose -Arguments @("up", "-d", "postgres")
}
Wait-PostgresHealthy

if ($Install) {
    Write-Step "Installing backend package"
    Invoke-Checked -FilePath "python" -Arguments @("-m", "pip", "install", "-e", ".") -WorkingDirectory $BackendDir
}

Write-Step "Starting backend"
$env:DATABASE_URL = "postgresql+psycopg://smart_outdoor:smart_outdoor_dev_password@127.0.0.1:5432/smart_outdoor"
$env:PYTHONPATH = $BackendDir

$uvicornArgs = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$BackendPort")
if ($Reload -and -not $NoReload) {
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
Write-Host "Backend API: http://127.0.0.1:${BackendPort}"
Write-Host "OpenAPI: http://127.0.0.1:${BackendPort}/openapi.json"
