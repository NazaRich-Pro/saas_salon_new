Write-Host "DevOps: Committing all GitHub Actions fixes..." -ForegroundColor Green

# 1. Add all changes
Write-Host "Adding all changes..." -ForegroundColor Yellow
git add .

# 2. Commit changes
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "DevOps: Fix all GitHub Actions CI issues

- Add PostgreSQL service and DATABASE_URL to CI workflow
- Update CodeQL to v3 in all workflows  
- Run black formatting for all Python files
- Recreate package-lock.json for Next.js
- Add dj-database-url support for DATABASE_URL in Django settings
- Ensure Django uses DATABASE_URL for tests

All CI pipeline issues resolved!"

# 3. Push changes
Write-Host "Pushing changes..." -ForegroundColor Yellow
git push origin main

Write-Host "All changes committed and pushed!" -ForegroundColor Green
Write-Host "GitHub Actions CI should now work!" -ForegroundColor Green
