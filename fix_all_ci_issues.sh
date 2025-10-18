#!/bin/bash

echo "🚀 DevOps: Исправляем ВСЕ проблемы CI/CD пайплайна..."

# 1. Исправляем Black форматирование
echo "📝 Исправляем Black форматирование..."
./fix_black_formatting.sh

# 2. Исправляем Next.js
echo "⚛️ Исправляем Next.js..."
./fix_nextjs_build.sh

# 3. Исправляем Django
echo "🐍 Исправляем Django..."
./fix_django_migrations.sh

# 4. Обновляем Security Scan
echo "🔒 Обновляем Security Scan..."
mkdir -p .github/workflows
cat > .github/workflows/security.yml << 'EOF'
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
        
    - name: Upload Trivy results to GitHub Security
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'
EOF

# 5. Создаем .pre-commit-config.yaml
echo "⚙️ Создаем pre-commit конфигурацию..."
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=88]
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black]
EOF

# 6. Добавляем pytz
echo "📦 Добавляем pytz..."
echo "pytz==2024.1" >> apps/api/requirements.txt

echo "✅ ВСЕ проблемы исправлены!"
echo "🎯 CI/CD пайплайн теперь должен работать!"
