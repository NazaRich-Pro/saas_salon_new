Write-Host "DevOps: Testing all CI/CD pipeline fixes..." -ForegroundColor Green

# 1. Check Black formatting
Write-Host "Checking Black formatting..." -ForegroundColor Yellow
Set-Location apps/api
try {
    black . --check --line-length=88
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Black formatting: OK" -ForegroundColor Green
    } else {
        Write-Host "Black formatting: FAILED" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Black not installed" -ForegroundColor Red
    exit 1
}

# 2. Check isort
Write-Host "Checking isort..." -ForegroundColor Yellow
try {
    isort . --check-only --profile black
    if ($LASTEXITCODE -eq 0) {
        Write-Host "isort: OK" -ForegroundColor Green
    } else {
        Write-Host "isort: FAILED" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "isort not installed" -ForegroundColor Red
    exit 1
}

Set-Location ../..

# 3. Check Next.js package-lock.json
Write-Host "Checking Next.js package-lock.json..." -ForegroundColor Yellow
if (Test-Path "apps/web/package-lock.json") {
    Write-Host "package-lock.json: EXISTS" -ForegroundColor Green
} else {
    Write-Host "package-lock.json: MISSING" -ForegroundColor Red
    exit 1
}

# 4. Check .pre-commit-config.yaml
Write-Host "Checking .pre-commit-config.yaml..." -ForegroundColor Yellow
if (Test-Path ".pre-commit-config.yaml") {
    Write-Host ".pre-commit-config.yaml: EXISTS" -ForegroundColor Green
} else {
    Write-Host ".pre-commit-config.yaml: MISSING" -ForegroundColor Red
    exit 1
}

# 5. Check CI workflow
Write-Host "Checking CI workflow..." -ForegroundColor Yellow
$ciContent = Get-Content ".github/workflows/ci.yml" -Raw
if ($ciContent -match "github/codeql-action/upload-sarif@v3") {
    Write-Host "Security Scan: UPDATED to v3" -ForegroundColor Green
} else {
    Write-Host "Security Scan: NOT UPDATED" -ForegroundColor Red
    exit 1
}

Write-Host "ALL FIXES TESTED!" -ForegroundColor Green
Write-Host "CI/CD pipeline ready!" -ForegroundColor Green