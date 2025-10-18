#!/bin/bash

echo "🚀 DevOps: Автоматический деплой на продакшн..."

# 1. Исправляем все проблемы
echo "🔧 Исправляем все проблемы..."
./fix_deployment_issues.sh

# 2. Коммитим изменения
echo "📝 Коммитим изменения..."
git add .
git commit -m "DevOps: Fix deployment issues - Black formatting, Next.js build, Django migrations, Slack notifications"
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

echo "✅ Деплой завершен!"
echo "🌐 Проверьте: https://saas.akylman.online"
