# PowerShell script for automatic restart of Ashot bot
param(
    [int]$MaxRestartsPerHour = 10,
    [int]$RestartDelay = 5,
    [string]$BotScript = "rar.py",
    [string]$LogFile = "bot_supervisor.log"
)

# Set encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp - $Level - $Message"
    Write-Host $logMessage
    Add-Content -Path $LogFile -Value $logMessage -Encoding UTF8
}

function Get-VenvPython {
    $venvPython = "venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return (Resolve-Path $venvPython).Path
    } else {
        return "python"
    }
}

function Test-CanRestart {
    param([array]$RestartTimes, [int]$MaxRestartsPerHour)
    $currentTime = Get-Date
    $recentRestarts = $RestartTimes | Where-Object { ($currentTime - $_).TotalHours -lt 1 }
    return $recentRestarts.Count -lt $MaxRestartsPerHour
}

function Start-Bot {
    param([string]$PythonPath, [string]$BotScript)
    
    try {
        Write-Log "ZAPUSK: Starting bot: $BotScript"
        $process = Start-Process -FilePath $PythonPath -ArgumentList $BotScript -PassThru -NoNewWindow
        Write-Log "USPEH: Bot started with PID: $($process.Id)"
        return $process
    }
    catch {
        Write-Log "OSHIBKA: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

Write-Log "START: Starting Ashot bot supervisor"
Write-Log "NASTROYKI: max $MaxRestartsPerHour restarts/hour, delay $RestartDelay sec"

if (-not (Test-Path $BotScript)) {
    Write-Log "OSHIBKA: Bot script not found: $BotScript" "ERROR"
    exit 1
}

$pythonPath = Get-VenvPython
Write-Log "PYTHON: Using Python: $pythonPath"

$restartTimes = @()
$botProcess = $null

while ($true) {
    try {
        if ($null -eq $botProcess -or $botProcess.HasExited) {
            if ($null -ne $botProcess -and $botProcess.HasExited) {
                Write-Log "ZAVERSHENIE: Process exited with code: $($botProcess.ExitCode)" "WARNING"
            }
            
            if (-not (Test-CanRestart -RestartTimes $restartTimes -MaxRestartsPerHour $MaxRestartsPerHour)) {
                Write-Log "LIMIT: Restart limit exceeded" "ERROR"
                Start-Sleep -Seconds 3600
                continue
            }
            
            $restartTimes += Get-Date
            
            if ($RestartDelay -gt 0) {
                Write-Log "ZADERZHKA: Waiting $RestartDelay seconds..."
                Start-Sleep -Seconds $RestartDelay
            }
            
            $botProcess = Start-Bot -PythonPath $pythonPath -BotScript $BotScript
            
            if ($null -eq $botProcess) {
                Write-Log "OSHIBKA: Failed to start bot" "ERROR"
                Start-Sleep -Seconds 30
            }
        }
        
        Start-Sleep -Seconds 10
    }
    catch {
        Write-Log "OSHIBKA: $($_.Exception.Message)" "ERROR"
        Start-Sleep -Seconds 30
    }
}

Write-Log "ZAVERSHENIE: Supervisor stopped" 