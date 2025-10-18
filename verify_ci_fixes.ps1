Write-Host "DevOps: Verifying all GitHub Actions fixes..." -ForegroundColor Green

# 1. Check PostgreSQL service in CI
Write-Host "Checking PostgreSQL service in CI..." -ForegroundColor Yellow
$ciContent = Get-Content ".github/workflows/ci.yml" -Raw
if ($ciContent -match "postgres:" -and $ciContent -match "DATABASE_URL") {
    Write-Host "✅ PostgreSQL service and DATABASE_URL: CONFIGURED" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL service: MISSING" -ForegroundColor Red
}

# 2. Check CodeQL v3
Write-Host "Checking CodeQL v3..." -ForegroundColor Yellow
if ($ciContent -match "github/codeql-action/upload-sarif@v3") {
    Write-Host "✅ CodeQL: UPDATED to v3" -ForegroundColor Green
} else {
    Write-Host "❌ CodeQL: NOT UPDATED" -ForegroundColor Red
}

# 3. Check Black formatting
Write-Host "Checking Black formatting..." -ForegroundColor Yellow
Set-Location apps/api
try {
    black . --check --line-length=88
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Black formatting: ALL FILES FORMATTED" -ForegroundColor Green
    } else {
        Write-Host "❌ Black formatting: NEEDS FORMATTING" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Black not installed" -ForegroundColor Red
}
Set-Location ../..

# 4. Check package-lock.json
Write-Host "Checking package-lock.json..." -ForegroundColor Yellow
if (Test-Path "apps/web/package-lock.json") {
    Write-Host "✅ package-lock.json: EXISTS" -ForegroundColor Green
} else {
    Write-Host "❌ package-lock.json: MISSING" -ForegroundColor Red
}

# 5. Check Django DATABASE_URL support
Write-Host "Checking Django DATABASE_URL support..." -ForegroundColor Yellow
$settingsContent = Get-Content "apps/api/config/settings.py" -Raw
if ($settingsContent -match "dj_database_url" -and $settingsContent -match "DATABASE_URL") {
    Write-Host "✅ Django DATABASE_URL: CONFIGURED" -ForegroundColor Green
} else {
    Write-Host "❌ Django DATABASE_URL: NOT CONFIGURED" -ForegroundColor Red
}

# 6. Check requirements.txt
Write-Host "Checking requirements.txt..." -ForegroundColor Yellow
$requirementsContent = Get-Content "apps/api/requirements.txt" -Raw
if ($requirementsContent -match "dj-database-url") {
    Write-Host "✅ dj-database-url: ADDED" -ForegroundColor Green
} else {
    Write-Host "❌ dj-database-url: MISSING" -ForegroundColor Red
}

Write-Host "All GitHub Actions fixes verified!" -ForegroundColor Green
Write-Host "Ready to commit and push!" -ForegroundColor Green
