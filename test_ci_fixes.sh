#!/bin/bash

echo "🚀 DevOps: Тестируем все исправления CI/CD пайплайна..."

# 1. Проверяем Black форматирование
echo "📝 Проверяем Black форматирование..."
cd apps/api
if black . --check --line-length=88; then
    echo "✅ Black форматирование: OK"
else
    echo "❌ Black форматирование: FAILED"
    exit 1
fi

# 2. Проверяем isort
echo "🔄 Проверяем isort..."
if isort . --check-only --profile black; then
    echo "✅ isort: OK"
else
    echo "❌ isort: FAILED"
    exit 1
fi

cd ../..

# 3. Проверяем Next.js package-lock.json
echo "⚛️ Проверяем Next.js package-lock.json..."
cd apps/web
if [ -f "package-lock.json" ]; then
    echo "✅ package-lock.json: EXISTS"
else
    echo "❌ package-lock.json: MISSING"
    exit 1
fi
cd ../..

# 4. Проверяем .pre-commit-config.yaml
echo "⚙️ Проверяем .pre-commit-config.yaml..."
if [ -f ".pre-commit-config.yaml" ]; then
    echo "✅ .pre-commit-config.yaml: EXISTS"
else
    echo "❌ .pre-commit-config.yaml: MISSING"
    exit 1
fi

# 5. Проверяем CI workflow
echo "🔧 Проверяем CI workflow..."
if grep -q "github/codeql-action/upload-sarif@v3" .github/workflows/ci.yml; then
    echo "✅ Security Scan: UPDATED to v3"
else
    echo "❌ Security Scan: NOT UPDATED"
    exit 1
fi

echo "🎯 ВСЕ ИСПРАВЛЕНИЯ ПРОТЕСТИРОВАНЫ!"
echo "✅ CI/CD пайплайн готов к работе!"
