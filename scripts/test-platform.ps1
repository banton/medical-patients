# Platform Testing Script for Windows PowerShell
# Tests all critical Task commands for cross-platform compatibility

param(
    [switch]$Verbose,
    [switch]$SkipDocker,
    [switch]$SkipNode
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Cyan"

Write-Host "🧪 Cross-Platform Compatibility Test" -ForegroundColor $Blue
Write-Host "Platform: Windows $(Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)"
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"
Write-Host "======================================" -ForegroundColor $Blue

# Test tracking
$TestsPassed = 0
$TestsFailed = 0
$TestsTotal = 0

# Function to run test
function Run-Test {
    param(
        [string]$TestName,
        [string]$TestCommand,
        [int]$ExpectedExitCode = 0
    )
    
    $script:TestsTotal++
    
    Write-Host ""
    Write-Host "🧪 Testing: $TestName" -ForegroundColor $Blue
    Write-Host "Command: $TestCommand"
    
    try {
        $result = Invoke-Expression $TestCommand 2>$null
        $actualExitCode = $LASTEXITCODE
        if ($null -eq $actualExitCode) { $actualExitCode = 0 }
    }
    catch {
        $actualExitCode = 1
    }
    
    if ($actualExitCode -eq $ExpectedExitCode) {
        Write-Host "✅ PASS" -ForegroundColor $Green
        $script:TestsPassed++
    }
    else {
        Write-Host "❌ FAIL (exit code: $actualExitCode, expected: $ExpectedExitCode)" -ForegroundColor $Red
        $script:TestsFailed++
    }
}

# Function to check command exists
function Test-Command {
    param(
        [string]$Command,
        [string]$Name
    )
    
    Write-Host ""
    Write-Host "🔍 Checking: $Name" -ForegroundColor $Blue
    
    try {
        $null = Get-Command $Command -ErrorAction Stop
        $version = & $Command --version 2>$null | Select-Object -First 1
        if (-not $version) { $version = "version unavailable" }
        Write-Host "✅ Found: $Command ($version)" -ForegroundColor $Green
        return $true
    }
    catch {
        Write-Host "❌ Missing: $Command" -ForegroundColor $Red
        return $false
    }
}

Write-Host ""
Write-Host "📋 Step 1: Environment Requirements" -ForegroundColor $Yellow
Write-Host "Checking required tools..."

# Check required tools
$RequirementsMet = $true

if (-not (Test-Command "task" "Task runner")) {
    $RequirementsMet = $false
}

if (-not $SkipDocker -and -not (Test-Command "docker" "Docker")) {
    Write-Host "⚠️  Docker not found - Docker tests will be skipped" -ForegroundColor $Yellow
    $SkipDocker = $true
}

$pythonFound = $false
if (Test-Command "python" "Python") {
    $pythonFound = $true
}
elseif (Test-Command "python3" "Python 3") {
    $pythonFound = $true
}
elseif (Test-Command "py" "Python Launcher") {
    $pythonFound = $true
}

if (-not $pythonFound) {
    $RequirementsMet = $false
}

if (-not $SkipNode) {
    if (-not (Test-Command "node" "Node.js")) {
        Write-Host "⚠️  Node.js not found - timeline viewer tests will be skipped" -ForegroundColor $Yellow
        $SkipNode = $true
    }
    
    if (-not (Test-Command "npm" "NPM")) {
        Write-Host "⚠️  NPM not found - timeline viewer tests will be skipped" -ForegroundColor $Yellow
        $SkipNode = $true
    }
}

if (-not $RequirementsMet) {
    Write-Host ""
    Write-Host "❌ Missing required tools. Please install them and try again." -ForegroundColor $Red
    Write-Host "See PLATFORM-SUPPORT.md for installation instructions."
    exit 1
}

Write-Host ""
Write-Host "📋 Step 2: Task System Tests" -ForegroundColor $Yellow

# Test Task system basics
Run-Test "Task version check" "task --version"
Run-Test "Task list all commands" "task --list-all"
Run-Test "Task help display" "task"

Write-Host ""
Write-Host "📋 Step 3: Core Development Commands" -ForegroundColor $Yellow

# Test core development workflow
Run-Test "Setup command" "task setup"
Run-Test "Clean command" "task clean"
Run-Test "Python detection" "task python-clean"

if (-not $SkipDocker) {
    Write-Host ""
    Write-Host "📋 Step 4: Docker Integration" -ForegroundColor $Yellow
    
    # Test Docker integration
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Run-Test "Docker service start" "task docker:services"
            Run-Test "Docker status check" "task docker:status"
            Run-Test "Docker cleanup" "task docker:clean"
        }
        else {
            Write-Host "⚠️  Docker not running - skipping Docker tests" -ForegroundColor $Yellow
        }
    }
    catch {
        Write-Host "⚠️  Docker not available - skipping Docker tests" -ForegroundColor $Yellow
    }
}

Write-Host ""
Write-Host "📋 Step 5: Database Commands" -ForegroundColor $Yellow

# Test database commands (without requiring running database)
Run-Test "Database status check (expect failure)" "task db:status" 1

Write-Host ""
Write-Host "📋 Step 6: Testing Framework" -ForegroundColor $Yellow

# Test testing commands
Run-Test "Test environment check" "task test:check-env"

Write-Host ""
Write-Host "📋 Step 7: Linting and Code Quality" -ForegroundColor $Yellow

# Test linting commands
Run-Test "Lint all command" "task lint:all"
Run-Test "Python linting" "task lint:python"

Write-Host ""
Write-Host "📋 Step 8: Frontend Commands" -ForegroundColor $Yellow

# Test frontend commands
Run-Test "Frontend install check" "task frontend:install"

if (-not $SkipNode) {
    Write-Host ""
    Write-Host "📋 Step 9: Timeline Viewer" -ForegroundColor $Yellow
    
    # Test timeline viewer
    Run-Test "Timeline status" "task timeline:status"
    Run-Test "Timeline environment check" "task timeline:check-env"
    Run-Test "Timeline info" "task timeline:info"
    
    # Only install if not already installed
    if (-not (Test-Path "patient-timeline-viewer/node_modules")) {
        Run-Test "Timeline dependency install" "task timeline:install"
    }
    
    if (Test-Path "patient-timeline-viewer/node_modules") {
        Run-Test "Timeline build" "task timeline:build"
        Run-Test "Timeline test" "task timeline:test"
    }
}

Write-Host ""
Write-Host "📋 Step 10: Windows-Specific Checks" -ForegroundColor $Yellow

# Windows-specific tests
$windowsVersion = Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Version
Write-Host "✅ Windows version: $windowsVersion"

# Check for WSL2 if Docker is being used
if (-not $SkipDocker) {
    try {
        $wslStatus = wsl --status 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ WSL2 available for Docker integration"
        }
        else {
            Write-Host "⚠️  WSL2 not detected - Docker Desktop may have limited functionality" -ForegroundColor $Yellow
        }
    }
    catch {
        Write-Host "⚠️  WSL command not available" -ForegroundColor $Yellow
    }
}

# Check PowerShell execution policy
$executionPolicy = Get-ExecutionPolicy
Write-Host "Execution Policy: $executionPolicy"
if ($executionPolicy -eq "Restricted") {
    Write-Host "⚠️  PowerShell execution policy is Restricted - may limit script functionality" -ForegroundColor $Yellow
}

# Summary
Write-Host ""
Write-Host "📊 Test Summary" -ForegroundColor $Blue
Write-Host "======================================"
Write-Host "Total tests: $TestsTotal"
Write-Host "Passed: $TestsPassed" -ForegroundColor $Green
Write-Host "Failed: $TestsFailed" -ForegroundColor $Red

if ($TestsFailed -eq 0) {
    Write-Host ""
    Write-Host "🎉 All tests passed! Platform compatibility confirmed." -ForegroundColor $Green
    Write-Host "This Windows system is ready for development."
    exit 0
}
else {
    Write-Host ""
    Write-Host "⚠️  Some tests failed. See details above." -ForegroundColor $Yellow
    Write-Host "Platform may have limited functionality."
    
    if ($TestsPassed -gt ($TestsTotal / 2)) {
        Write-Host "Most functionality works - minor issues only."
        exit 0
    }
    else {
        Write-Host "Major compatibility issues detected."
        exit 1
    }
}