#!/bin/bash

echo "🚀 DevOps: Коммитим все исправления GitHub Actions..."

# 1. Добавляем все изменения
echo "📝 Добавляем все изменения..."
git add .

# 2. Коммитим изменения
echo "💾 Коммитим изменения..."
git commit -m "DevOps: Fix all GitHub Actions CI issues

- ✅ Add PostgreSQL service and DATABASE_URL to CI workflow
- ✅ Update CodeQL to v3 in all workflows  
- ✅ Run black formatting for all Python files
- ✅ Recreate package-lock.json for Next.js
- ✅ Add dj-database-url support for DATABASE_URL in Django settings
- ✅ Ensure Django uses DATABASE_URL for tests

All CI pipeline issues resolved!"

# 3. Пушим изменения
echo "🚀 Пушим изменения..."
git push origin main

echo "✅ Все изменения закоммичены и запушены!"
echo "🎯 GitHub Actions CI должен теперь работать!"
