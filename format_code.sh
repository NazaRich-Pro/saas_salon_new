#!/bin/bash

echo "🔧 Форматируем код как опытный DevOps..."

# 1. Форматируем Python код с Black
echo "📝 Форматируем Python код..."
cd apps/api
black . --config .black.toml
isort . --profile black
cd ../..

# 2. Форматируем TypeScript/JavaScript код
echo "📝 Форматируем TypeScript код..."
cd apps/web
npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"
cd ../..

# 3. Проверяем линтинг
echo "🔍 Проверяем линтинг..."
cd apps/api
flake8 . --max-line-length=88 --extend-ignore=E203,W503
cd ../..

echo "✅ Код отформатирован!"
