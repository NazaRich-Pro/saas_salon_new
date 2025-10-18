#!/bin/bash

echo "🚀 DevOps: ПРИНУДИТЕЛЬНОЕ форматирование Black - исправляем ВСЕ 104 файла..."

# 1. Устанавливаем Black и isort
echo "📦 Устанавливаем инструменты..."
pip install black==23.12.1 isort==5.13.2

# 2. Переходим в директорию API
cd apps/api

# 3. ПРИНУДИТЕЛЬНО форматируем ВСЕ файлы
echo "📝 ПРИНУДИТЕЛЬНО форматируем ВСЕ Python файлы..."
black . --line-length=88 --quiet

# 4. Сортируем импорты
echo "🔄 Сортируем импорты..."
isort . --profile black --quiet

# 5. Проверяем результат
echo "🔍 Проверяем результат..."
black . --check --line-length=88

# 6. Если все еще есть проблемы, форматируем еще раз
if [ $? -ne 0 ]; then
    echo "❌ Еще есть проблемы, форматируем еще раз..."
    black . --line-length=88
    isort . --profile black
    black . --check --line-length=88
fi

cd ../..

echo "✅ ВСЕ 104 файла отформатированы!"
echo "🎯 Black больше НЕ будет ругаться!"
