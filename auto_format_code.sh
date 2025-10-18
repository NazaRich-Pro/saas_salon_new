#!/bin/bash

echo "🔧 DevOps: Автоматическое форматирование кода..."

# 1. Форматируем ВСЕ Python файлы с Black
echo "📝 Форматируем Python код с Black..."
cd apps/api

# Запускаем Black для форматирования (не проверки)
black . --line-length=88 --quiet

# Запускаем isort для сортировки импортов
isort . --profile black --quiet

# Проверяем результат
echo "🔍 Проверяем результат форматирования..."
black . --check --line-length=88

cd ../..

echo "✅ Код отформатирован!"
echo "🎯 Теперь Black не будет ругаться!"
