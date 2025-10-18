#!/bin/bash

echo "🚀 DevOps: Принудительное форматирование ВСЕГО кода..."

# 1. Устанавливаем Black и isort если их нет
echo "📦 Устанавливаем инструменты форматирования..."
pip install black isort flake8

# 2. Форматируем ВСЕ Python файлы
echo "📝 Форматируем ВСЕ Python файлы..."
cd apps/api

# Принудительное форматирование всех файлов
find . -name "*.py" -exec black {} --line-length=88 --quiet \;

# Сортируем импорты
find . -name "*.py" -exec isort {} --profile black --quiet \;

# Проверяем результат
echo "🔍 Проверяем результат..."
black . --check --line-length=88 --diff

cd ../..

echo "✅ ВСЕ файлы отформатированы!"
echo "🎯 Black больше не будет ругаться!"
