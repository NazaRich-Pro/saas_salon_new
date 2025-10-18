#!/bin/bash

echo "🚀 DevOps: Исправляем Black форматирование навсегда..."

# 1. Устанавливаем Black
echo "📦 Устанавливаем Black..."
pip install black==23.12.1 isort==5.13.2

# 2. Переходим в директорию API
cd apps/api

# 3. Форматируем ВСЕ файлы принудительно
echo "📝 Форматируем ВСЕ Python файлы..."
black . --line-length=88 --quiet

# 4. Сортируем импорты
echo "🔄 Сортируем импорты..."
isort . --profile black --quiet

# 5. Проверяем результат
echo "🔍 Проверяем результат..."
if black . --check --line-length=88; then
    echo "✅ ВСЕ файлы отформатированы!"
else
    echo "❌ Еще есть проблемы, форматируем еще раз..."
    black . --line-length=88
    isort . --profile black
fi

cd ../..

echo "🎯 Black больше не будет ругаться!"
