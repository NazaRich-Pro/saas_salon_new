# BeautyHub SaaS - Quick Start Guide

## For Production Deployment (Ubuntu VPS)

### Step 1: Clone Repository

```bash
cd /opt
git clone <your-repo-url> saas_salon
cd saas_salon
```

### Step 2: Run Initialization

```bash
make init
```

This will:
- Check/install Docker
- Configure firewall
- Create `.env` file
- Generate security secrets
- Build Docker images
- Start all services
- Run database migrations
- Prompt for superuser creation

### Step 3: Configure DNS

Create these DNS records pointing to your VPS IP:

**At your DNS provider (Cloudflare, Namecheap, etc.):**

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | YOUR_VPS_IP | 300 |
| A | * | YOUR_VPS_IP | 300 |

**Verify DNS:**
```bash
dig saas.akylman.online +short
dig demo.saas.akylman.online +short
# Both should return YOUR_VPS_IP
```

**Wait for propagation (5-30 minutes)**

For detailed instructions: [docs/DNS_SETUP.md](docs/DNS_SETUP.md)

### Step 4: Access Your Application

After DNS propagates:

- **Frontend:** https://saas.akylman.online
- **Admin Panel:** https://saas.akylman.online/admin
- **API:** https://saas.akylman.online/api
- **Traefik Dashboard:** https://traefik.saas.akylman.online

TLS certificates will be obtained automatically by Traefik.

## For Local Development

### Step 1: Start Development Services

```bash
# Start PostgreSQL, Redis, MailHog
make dev-up
```

### Step 2: Run Django API

```bash
cd apps/api
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**API will be at:** http://localhost:8000

### Step 3: Run Next.js Frontend

```bash
cd apps/web
npm install
npm run dev
```

**Frontend will be at:** http://localhost:3000

### Step 4: Run Celery Worker (Optional)

```bash
cd apps/api
celery -A config worker --loglevel=info
```

### Local Services

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379
- **MailHog UI:** http://localhost:8025

## Common Commands

### Production

```bash
# View logs
make logs

# Monitor system
make monitor

# Backup database
make backup

# Deploy updates
make deploy

# Restart services
make restart

# Check health
make health
```

### Development

```bash
# Database operations
make migrate
make makemigrations
make dbshell
make shell

# Testing
make test-api
make test-web

# Linting
make lint-api
make lint-web
```

## Next Steps

1. ✅ **Complete:** Infrastructure setup (Stage 0-1)
2. 🚧 **Next:** Implement multi-tenancy (Stage 2)
3. 📋 **Upcoming:** Authentication & RBAC (Stage 3)

## Troubleshooting

### Services won't start
```bash
make logs
# Check for errors in output
```

### TLS certificate issues
```bash
# Delete and regenerate certificates
cd infra
rm -rf letsencrypt/acme.json
make restart
```

### Database connection errors
```bash
# Check PostgreSQL
docker compose exec postgres pg_isready -U saas
make dbshell
```

### DNS not working
```bash
# Check DNS propagation
dig saas.akylman.online +short

# Verify Traefik routing
docker compose logs traefik
```

## Documentation

- **Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Reference:** [docs/API.md](docs/API.md)
- **Deployment Guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Development Guide:** [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **DNS Setup:** [docs/DNS_SETUP.md](docs/DNS_SETUP.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

For issues:
1. Check logs: `make logs`
2. Check monitoring: `make monitor`
3. Review documentation above
4. Open an issue on GitHub

---

**Ready to build the next big beauty booking platform! 💅**

