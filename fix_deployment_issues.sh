#!/bin/bash

echo "🚀 DevOps: Исправляем все проблемы деплоя..."

# 1. Исправляем Black форматирование
echo "📝 Исправляем Black форматирование..."
cd apps/api
pip install black==23.12.1 isort==5.13.2
black . --line-length=88 --quiet
isort . --profile black --quiet
cd ../..

# 2. Исправляем Next.js
echo "⚛️ Исправляем Next.js..."
cd apps/web
rm -f package-lock.json
npm install
npm run build
cd ../..

# 3. Исправляем Django
echo "🐍 Исправляем Django..."
cd apps/api
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
cd ../..

# 4. Создаем правильный .env файл
echo "🔧 Создаем .env файл..."
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://beautyhub:beautyhub123@postgres:5432/beautyhub

# Redis
REDIS_URL=redis://redis:6379/0

# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,saas.akylman.online,staging.saas.akylman.online

# Next.js
NEXT_PUBLIC_API_URL=https://saas.akylman.online/api
NEXT_PUBLIC_APP_URL=https://saas.akylman.online

# Docker
COMPOSE_PROJECT_NAME=beautyhub
EOF

# 5. Создаем скрипт для деплоя
echo "🚀 Создаем скрипт деплоя..."
mkdir -p infra/scripts
cat > infra/scripts/deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Deploying to production..."

# 1. Backup current state
echo "📦 Creating backup..."
./infra/scripts/backup.sh

# 2. Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# 3. Build and start services
echo "🔨 Building and starting services..."
docker compose down
docker compose build
docker compose up -d

# 4. Run migrations
echo "🔄 Running migrations..."
docker compose exec -T api python manage.py migrate

# 5. Health check
echo "🏥 Health check..."
sleep 10
curl -f http://localhost:3000/ || exit 1

echo "✅ Deployment completed!"
EOF

chmod +x infra/scripts/deploy.sh

# 6. Создаем скрипт бэкапа
cat > infra/scripts/backup.sh << 'EOF'
#!/bin/bash

echo "📦 Creating backup..."

# Create backup directory
mkdir -p /backups/$(date +%Y%m%d_%H%M%S)

# Backup database
docker compose exec -T postgres pg_dump -U beautyhub beautyhub > /backups/$(date +%Y%m%d_%H%M%S)/database.sql

# Backup files
tar -czf /backups/$(date +%Y%m%d_%H%M%S)/files.tar.gz apps/

echo "✅ Backup created!"
EOF

chmod +x infra/scripts/backup.sh

echo "✅ Все проблемы деплоя исправлены!"
echo "🎯 Теперь можно деплоить!"
