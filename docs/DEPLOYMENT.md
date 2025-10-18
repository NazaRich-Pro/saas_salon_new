# Deployment Guide

## Prerequisites

- Ubuntu 20.04+ VPS with root access
- Docker & Docker Compose installed
- Domain name with DNS access
- Ports 80 and 443 open

## Initial Server Setup

### 1. Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then test
docker --version
docker compose version
```

### 2. Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. DNS Configuration

Create the following DNS records pointing to your VPS IP:

- `A` record: `saas.akylman.online` → `YOUR_VPS_IP`
- `A` record: `*.saas.akylman.online` → `YOUR_VPS_IP`

Wait for DNS propagation (check with `dig saas.akylman.online`)

## Application Deployment

### 1. Clone Repository

```bash
cd /opt
git clone <your-repo-url> saas_salon
cd saas_salon
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Update the following values:
- `DJANGO_SECRET_KEY`: Generate with `openssl rand -hex 32`
- `JWT_ACCESS_SECRET`: Generate with `openssl rand -hex 32`
- `JWT_REFRESH_SECRET`: Generate with `openssl rand -hex 32`
- `POSTGRES_PASSWORD`: Strong password
- `SMTP_*`: Your email provider settings
- `SENTRY_DSN`: (optional) Your Sentry DSN

### 3. Build and Start Services

```bash
cd infra
docker compose build
docker compose up -d
```

### 4. Check Logs

```bash
docker compose logs -f
```

Wait for Traefik to obtain TLS certificates (may take a few minutes).

### 5. Run Migrations

```bash
docker compose exec api python manage.py migrate
```

### 6. Create Superuser

```bash
docker compose exec api python manage.py createsuperuser
```

### 7. Collect Static Files

```bash
docker compose exec api python manage.py collectstatic --noinput
```

## Verification

1. **Check services are running**:
```bash
docker compose ps
```

All services should be "Up".

2. **Test HTTPS**:
```bash
curl https://saas.akylman.online
```

Should return the Next.js homepage.

3. **Test API**:
```bash
curl https://saas.akylman.online/api/
```

Should return API response.

## Maintenance

### Update Application

```bash
cd /opt/saas_salon
git pull
cd infra
docker compose build
docker compose up -d
docker compose exec api python manage.py migrate
```

### View Logs

```bash
cd /opt/saas_salon/infra
docker compose logs -f [service_name]
```

### Restart Services

```bash
cd /opt/saas_salon/infra
docker compose restart
```

### Backup Database

```bash
cd /opt/saas_salon/infra
docker compose exec postgres pg_dump -U saas saas | gzip > /opt/backups/saas_$(date +%Y%m%d).sql.gz
```

### Restore Database

```bash
gunzip < /opt/backups/saas_20251011.sql.gz | docker compose exec -T postgres psql -U saas -d saas
```

## Monitoring

### Check Resource Usage

```bash
docker stats
```

### Check Disk Space

```bash
df -h
```

### Clean Old Docker Images

```bash
docker system prune -a
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker compose logs

# Check if ports are in use
sudo netstat -tulpn | grep -E ':(80|443|5432|6379)'

# Restart Docker
sudo systemctl restart docker
```

### TLS Certificate Issues

```bash
# Check Traefik logs
docker compose logs traefik

# Remove old certificates and restart
docker compose down
sudo rm -rf traefik/letsencrypt/acme.json
docker compose up -d
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Test connection
docker compose exec api python manage.py dbshell
```

## Security Checklist

- [ ] Changed all default passwords
- [ ] Generated strong secret keys
- [ ] Configured firewall (UFW)
- [ ] Enabled automatic security updates
- [ ] Set up database backups
- [ ] Configured Sentry for error tracking
- [ ] Reviewed Django settings for production
- [ ] Set up monitoring/alerting

## Changing Domain

To change from `saas.akylman.online` to your own domain:

1. Update `.env`:
```bash
PRIMARY_DOMAIN=yourdomain.com
```

2. Update DNS records for `yourdomain.com` and `*.yourdomain.com`

3. Update `infra/docker-compose.yml` Traefik labels

4. Restart services:
```bash
docker compose down
docker compose up -d
```

Traefik will automatically obtain new TLS certificates.


