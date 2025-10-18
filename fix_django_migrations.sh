#!/bin/bash

echo "🚀 DevOps: Исправляем Django миграции..."

# 1. Переходим в директорию API
cd apps/api

# 2. Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

# 3. Создаем миграции
echo "📝 Создаем миграции..."
python manage.py makemigrations

# 4. Применяем миграции (с SQLite для тестов)
echo "🔄 Применяем миграции..."
python manage.py migrate

# 5. Создаем суперпользователя (если нужно)
echo "👤 Создаем суперпользователя..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com

cd ../..

echo "✅ Django исправлен!"
