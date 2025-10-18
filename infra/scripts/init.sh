#!/bin/bash
set -e

# BeautyHub SaaS Initial Setup Script
# Run this script on a fresh installation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================="
echo "BeautyHub SaaS - Initial Setup"
echo "========================================="
echo ""

# Check if running as root (for VPS setup)
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root - will install system dependencies"
    INSTALL_DEPS=true
else
    INSTALL_DEPS=false
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    if [ "$INSTALL_DEPS" = true ]; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        echo "✓ Docker installed"
    else
        echo "✗ Docker is not installed. Please install Docker first."
        exit 1
    fi
else
    echo "✓ Docker is already installed ($(docker --version))"
fi

# Check Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo "✗ Docker Compose plugin is not available"
    echo "Please install Docker Compose"
    exit 1
else
    echo "✓ Docker Compose is available ($(docker compose version))"
fi

# Setup firewall (if root)
if [ "$INSTALL_DEPS" = true ]; then
    if command -v ufw &> /dev/null; then
        echo ""
        echo "Configuring firewall..."
        ufw allow 22/tcp  # SSH
        ufw allow 80/tcp  # HTTP
        ufw allow 443/tcp # HTTPS
        ufw --force enable
        echo "✓ Firewall configured"
    fi
fi

# Setup environment file
cd "$PROJECT_ROOT"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ Created .env from .env.example"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env file and set:"
        echo "  - PRIMARY_DOMAIN"
        echo "  - POSTGRES_PASSWORD"
        echo "  - JWT_ACCESS_SECRET"
        echo "  - JWT_REFRESH_SECRET"
        echo "  - SMTP_* settings"
        echo ""
        read -p "Press Enter after editing .env file..."
    else
        echo "✗ .env.example not found"
        exit 1
    fi
else
    echo "✓ .env file already exists"
fi

# Load environment
set -a
source .env
set +a

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p infra/letsencrypt
mkdir -p apps/api/staticfiles
mkdir -p apps/api/media
chmod +x infra/scripts/*.sh

echo "✓ Directories created"

# Generate secrets if not set
if [ "$JWT_ACCESS_SECRET" = "replace_me_access" ]; then
    echo ""
    echo "⚠️  Generating JWT secrets..."
    JWT_ACCESS=$(openssl rand -hex 32)
    JWT_REFRESH=$(openssl rand -hex 32)
    sed -i "s/JWT_ACCESS_SECRET=replace_me_access/JWT_ACCESS_SECRET=$JWT_ACCESS/" .env
    sed -i "s/JWT_REFRESH_SECRET=replace_me_refresh/JWT_REFRESH_SECRET=$JWT_REFRESH/" .env
    echo "✓ JWT secrets generated"
fi

# Build and start services
echo ""
echo "Building Docker images (this may take a while)..."
cd infra
docker compose build

echo ""
echo "Starting services..."
docker compose up -d

echo ""
echo "Waiting for services to start..."
sleep 15

# Run migrations
echo ""
echo "Running database migrations..."
docker compose exec -T api python manage.py migrate

# Create superuser
echo ""
echo "========================================="
echo "Create superuser account"
echo "========================================="
echo ""
docker compose exec api python manage.py createsuperuser

# Collect static files
echo ""
echo "Collecting static files..."
docker compose exec -T api python manage.py collectstatic --noinput

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Your BeautyHub SaaS is now running!"
echo ""
echo "Service URLs:"
echo "  Frontend: https://${PRIMARY_DOMAIN}"
echo "  Admin Panel: https://${PRIMARY_DOMAIN}/admin"
echo "  API: https://${PRIMARY_DOMAIN}/api"
echo "  Traefik Dashboard: https://traefik.${PRIMARY_DOMAIN}"
echo ""
echo "DNS Configuration Required:"
echo "  Create A record: ${PRIMARY_DOMAIN} → YOUR_VPS_IP"
echo "  Create A record: *.${PRIMARY_DOMAIN} → YOUR_VPS_IP"
echo ""
echo "Useful commands:"
echo "  View logs: docker compose logs -f"
echo "  Restart: docker compose restart"
echo "  Stop: docker compose down"
echo "  Backup: ./scripts/backup.sh"
echo ""
echo "========================================="

