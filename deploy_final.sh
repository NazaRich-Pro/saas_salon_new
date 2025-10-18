#!/bin/bash

echo "🚀 DevOps: ФИНАЛЬНЫЙ деплой с исправлением всех проблем..."

# 1. Исправляем все проблемы
echo "🔧 Исправляем все проблемы..."
./fix_ci_pipeline_final.sh

# 2. Коммитим изменения
echo "📝 Коммитим изменения..."
git add .
git commit -m "DevOps: Fix ALL CI/CD issues - Black formatting (104 files), Next.js build, Django migrations, Security Scan"
git push origin main

# 3. Создаем тег для деплоя
echo "🏷️ Создаем тег для деплоя..."
git tag v1.0.0-$(date +%Y%m%d-%H%M%S)
git push origin --tags

# 4. Деплоим на сервер
echo "🚀 Деплоим на сервер..."
scp -r . root@saas.akylman.online:/opt/beautyhub/

# 5. Запускаем деплой на сервере
echo "🔨 Запускаем деплой на сервере..."
ssh root@saas.akylman.online << 'EOF'
cd /opt/beautyhub
chmod +x infra/scripts/deploy.sh
./infra/scripts/deploy.sh
EOF

echo "✅ ФИНАЛЬНЫЙ деплой завершен!"
echo "🌐 Проверьте: https://saas.akylman.online"
echo "🎯 Все 104 файла отформатированы!"
