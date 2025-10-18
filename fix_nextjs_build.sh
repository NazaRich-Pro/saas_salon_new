#!/bin/bash

echo "🚀 DevOps: Исправляем Next.js сборку..."

# 1. Переходим в директорию web
cd apps/web

# 2. Удаляем старый package-lock.json
echo "🗑️ Удаляем старый package-lock.json..."
rm -f package-lock.json

# 3. Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
npm install

# 4. Создаем правильный package-lock.json
echo "📝 Создаем правильный package-lock.json..."
npm install --package-lock-only

# 5. Проверяем сборку
echo "🔨 Проверяем сборку..."
npm run build

cd ../..

echo "✅ Next.js исправлен!"
