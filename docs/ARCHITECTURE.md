# BeautyHub SaaS - Architecture Overview

## System Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Traefik (Reverse Proxy)                    │
│              TLS Termination + Routing                       │
└──────┬─────────────────────────────────┬────────────────────┘
       │                                 │
       ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│   Next.js App   │              │  Django API     │
│   (Frontend)    │◄────────────►│  (Backend)      │
└────────┬────────┘              └────────┬────────┘
         │                                │
         │                                │
         │         ┌──────────────────────┤
         │         │                      │
         │         ▼                      ▼
         │  ┌─────────────┐      ┌──────────────┐
         │  │ PostgreSQL  │      │    Redis     │
         │  │  (Database) │      │   (Cache)    │
         │  └─────────────┘      └──────┬───────┘
         │                               │
         │                               ▼
         │                       ┌──────────────┐
         │                       │    Celery    │
         └───────────────────────┤   Workers    │
                                 └──────────────┘
```

### Multi-Tenancy Model

- **Subdomain routing**: `{slug}.saas.akylman.online`
- **Custom domains**: `custom.domain.com` → Tenant lookup
- **Data isolation**: All tables filtered by `tenant_id`
- **Middleware**: Resolves tenant from Host header

### Authentication Flow

```
1. User → Login (email/password)
2. API validates credentials
3. API generates JWT (access + refresh)
4. Tokens stored in httpOnly cookies
5. Every request: middleware validates JWT
6. Refresh token rotation on refresh
7. Device sessions tracked
```

### Request Flow

```
User Request
    ↓
Traefik (TLS + routing)
    ↓
Next.js/Django
    ↓
TenantMiddleware (resolve tenant)
    ↓
AuthMiddleware (validate JWT)
    ↓
Permission Check (role + tenant)
    ↓
Business Logic
    ↓
Response
```

## Technology Choices

### Frontend: Next.js
- **Why**: SSR for SEO, React Server Components, great DX
- **App Router**: Modern routing with layouts
- **TypeScript**: Type safety across the stack

### Backend: Django + DRF
- **Why**: Mature, batteries-included, excellent ORM
- **DRF**: REST API with serializers & viewsets
- **Celery**: Async task processing

### Database: PostgreSQL
- **Why**: JSONB for settings, full-text search, reliability
- **Multi-tenancy**: Row-level filtering via `tenant_id`

### Infrastructure: Docker + Traefik
- **Why**: Easy deployment, automatic TLS, service discovery
- **Traefik**: Dynamic routing based on labels

## Security Considerations

### Authentication
- JWT in httpOnly cookies (XSS protection)
- Refresh token rotation
- 2FA (TOTP) for admin roles

### Authorization
- RBAC with 5 roles
- Tenant isolation enforced at API layer
- Permission classes in DRF

### Data Protection
- All passwords hashed (Django default)
- Sensitive data encrypted at rest
- Audit logs for critical actions

## Scalability

### Horizontal Scaling
- Next.js: Multiple containers behind load balancer
- Django: Gunicorn with multiple workers
- Celery: Add more worker containers
- PostgreSQL: Read replicas for reports

### Caching Strategy
- Redis for session storage
- API response caching (DRF cache)
- Next.js SSR caching

### Database Optimization
- Indices on `(tenant_id, created_at)`
- Separate read replicas for reports
- Connection pooling

## Monitoring & Observability

### Logging
- Structured JSON logs
- Centralized via Docker logs

### Error Tracking
- Sentry integration
- Error grouping by tenant

### Metrics
- Prometheus (planned)
- Custom business metrics

### Tracing
- OpenTelemetry (planned)
- Request tracing across services

## Deployment Strategy

### Development
- Local Docker Compose
- Hot reload for both frontend & backend

### Production
- Docker Compose on VPS
- GitHub Actions CI/CD
- Blue-green deployment (future)

### Backups
- Nightly PostgreSQL dumps
- 14-day retention
- Encrypted backups

## Future Enhancements

1. **Microservices**: Split booking, payments into separate services
2. **Kubernetes**: Migrate from Docker Compose
3. **GraphQL**: Alternative to REST for complex queries
4. **Mobile Apps**: React Native + shared SDK
5. **Analytics**: Real-time dashboard with BI tools


