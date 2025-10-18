# Development Guide

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- Git

### Initial Setup

1. **Clone the repository**
```bash
git clone <repo-url> saas_salon
cd saas_salon
```

2. **Set up environment**
```bash
cp .env.example .env
# Edit .env with local development settings
```

3. **Start infrastructure**
```bash
make up
# or
cd infra && docker compose up -d
```

## Frontend Development

### Next.js App (apps/web)

```bash
cd apps/web

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`.

### Working with Components

Components are organized:
- `src/app/`: Next.js App Router pages
- `src/components/`: Reusable React components
- `packages/ui/`: Shared UI components (shadcn/ui)

### Adding New Pages

```bash
# Create a new page
mkdir -p src/app/new-page
touch src/app/new-page/page.tsx
```

### i18n

We use `next-intl` for internationalization. Translation files will be in `src/i18n/`.

## Backend Development

### Django API (apps/api)

```bash
cd apps/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

### Creating New Apps

```bash
cd apps/api
python manage.py startapp myapp apps/myapp
```

Then add to `INSTALLED_APPS` in `config/settings.py`.

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration SQL (without applying)
python manage.py sqlmigrate app_name migration_name
```

### Django Shell

```bash
python manage.py shell

# Or with IPython
pip install ipython
python manage.py shell
```

### Running Tests

```bash
# All tests
pytest

# Specific app
pytest apps/users

# With coverage
pytest --cov=apps --cov-report=html

# Fast (skip slow tests)
pytest -m "not slow"
```

## Celery Workers

### Start Worker

```bash
cd apps/api
celery -A config worker --loglevel=info
```

### Start Beat (Scheduler)

```bash
cd apps/api
celery -A config beat --loglevel=info
```

### Monitor Tasks

```bash
# Flower (Celery monitoring tool)
pip install flower
celery -A config flower
```

Visit `http://localhost:5555`.

## Database

### Access PostgreSQL

```bash
# Via Docker
make dbshell

# Or directly
psql -h localhost -U saas -d saas
```

### Backup/Restore

```bash
# Backup
make backup-db

# Restore
make restore-db FILE=backup.sql
```

## Code Quality

### Python Linting

```bash
cd apps/api

# Format with Black
black .

# Lint with flake8
flake8

# Type checking with mypy
mypy apps
```

### JavaScript/TypeScript Linting

```bash
cd apps/web

# Lint
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix

# Type check
npm run type-check
```

## Docker Development

### Rebuild Containers

```bash
make build
# or
docker compose build --no-cache
```

### View Logs

```bash
make logs
# or
docker compose logs -f [service_name]
```

### Execute Commands in Containers

```bash
# Django shell
docker compose exec api python manage.py shell

# Node shell
docker compose exec web sh
```

## Environment Variables

Key variables for development:

```bash
# .env
DEBUG=True
NODE_ENV=development
PRIMARY_DOMAIN=localhost

# Disable HTTPS in local development
# Update docker-compose.yml to use http entrypoint
```

## Testing Multi-Tenancy Locally

Add to `/etc/hosts` (or `C:\Windows\System32\drivers\etc\hosts` on Windows):

```
127.0.0.1 beautyhub.local
127.0.0.1 demo.beautyhub.local
127.0.0.1 salon1.beautyhub.local
```

Then update `.env`:
```
PRIMARY_DOMAIN=beautyhub.local
```

## Common Tasks

### Add New Dependency

**Frontend:**
```bash
cd apps/web
npm install package-name
```

**Backend:**
```bash
cd apps/api
pip install package-name
pip freeze > requirements.txt
```

### Create New API Endpoint

1. Define view in `apps/myapp/views.py`
2. Add serializer in `apps/myapp/serializers.py`
3. Add URL in `apps/myapp/urls.py`
4. Add tests in `apps/myapp/tests/test_views.py`

### Add New Celery Task

```python
# apps/myapp/tasks.py
from celery import shared_task

@shared_task
def my_task():
    # Task code
    pass
```

## Debugging

### Django Debug Toolbar

```bash
pip install django-debug-toolbar
```

Add to `INSTALLED_APPS` and middleware in settings.

### React DevTools

Install browser extension:
- [Chrome](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
- [Firefox](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/)

### VS Code Setup

Recommended extensions:
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Docker

### Breakpoints

**Python:**
```python
import pdb; pdb.set_trace()
# or
breakpoint()
```

**JavaScript:**
```javascript
debugger;
```

## Git Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -m "feat: add my feature"`
3. Push: `git push origin feature/my-feature`
4. Create Pull Request
5. After review, merge to `main`

### Commit Message Convention

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/config changes

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :3000
# or
netstat -ano | findstr :3000

# Kill process
kill -9 <PID>
```

### Docker Out of Space

```bash
docker system prune -a --volumes
```

### Database Connection Refused

Check if PostgreSQL container is running:
```bash
docker compose ps postgres
docker compose logs postgres
```

### Hot Reload Not Working

Clear Next.js cache:
```bash
rm -rf apps/web/.next
```

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [Django Docs](https://docs.djangoproject.com/)
- [DRF Docs](https://www.django-rest-framework.org/)
- [Tailwind Docs](https://tailwindcss.com/docs)
- [shadcn/ui](https://ui.shadcn.com/)


