# BeautyHub SaaS — MASTER PROMPT for Cursor (v2)

> **Goal:** Generate a production-grade, multi-tenant booking SaaS for salons and solo masters (minimal Amelia-like feature set), hosted on your Ubuntu VPS with subdomains and white-label support. Include manual cash payments, KGS billing, RU+KG onboarding emails, and one-click self-service onboarding (“Создать салон” / “Я мастер”).
> **Primary domain (temporary):** `saas.akylman.online` (can be changed later via `.env`).

---

## 0) Tech Stack (decided)

- **Frontend:** Next.js (App Router, TypeScript), Tailwind, shadcn/ui, TanStack Query, i18n (RU/KG/EN).
- **Backend:** Python — Django 5 + Django REST Framework, Celery + Redis for background jobs.
- **DB:** PostgreSQL 15+ (Django ORM). Multi-tenant via `tenant_id` and host-based tenant resolution.
- **Cache/Queues:** Redis 7.
- **Auth:** JWT in httpOnly cookies + refresh rotation, device sessions, 2FA (TOTP) for Superadmin/Salon Admin.
- **Payments:** Provider abstraction. MVP providers:
  - `ManualCash` (mark cash payments in UI).
  - `Stripe` **stub** (switchable later to real Stripe or local gateways).
- **Infrastructure:** Docker Compose + Traefik v3 (TLS via ACME, wildcard), GitHub Actions CI/CD.
- **Observability:** Sentry, basic OpenTelemetry, Prometheus + Grafana.
- **Currency:** KGS.

**Monorepo layout** (to generate):
```
saas/
  apps/
    web/        # Next.js (public pages + widget + role-based dashboards)
    api/        # Django + DRF
    worker/     # Celery worker + beat
  infra/
    docker-compose.yml
    traefik/
      traefik.yml
      dynamic.yml
  packages/
    ui/         # shared UI components (React + Tailwind)
    sdk/        # typed client for web → api
  docs/
  .env.example
  README.md
```

**.env.example (generate and use)**
```
NODE_ENV=production
PRIMARY_DOMAIN=saas.akylman.online   # change later to your real domain
CURRENCY=KGS

POSTGRES_USER=saas
POSTGRES_PASSWORD=supersecret
POSTGRES_DB=saas
DATABASE_URL=postgresql://saas:supersecret@postgres:5432/saas

REDIS_URL=redis://redis:6379

JWT_ACCESS_SECRET=replace_me_access
JWT_REFRESH_SECRET=replace_me_refresh

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=

SENTRY_DSN=

TELEGRAM_BOT_TOKEN=
```

---

## 1) Infra + Traefik + DNS

1. Create Docker services: `traefik`, `web`, `api`, `worker`, `postgres`, `redis`.
2. Configure Traefik:
   - EntryPoints `:80` and `:443`.
   - ACME TLS (Let’s Encrypt) with resolver `le` and persistent storage.
   - Docker provider + file provider (`dynamic.yml` for security headers).
3. DNS (to do manually outside): create `A` records pointing to the VPS IP for:
   - `saas.akylman.online`
   - `*.saas.akylman.online` (wildcard)
4. Labels for `web` and `api` should route by host using `HostRegexp({subdomain:.+}.saas.akylman.online) || Host(saas.akylman.online)`.

**Create `infra/docker-compose.yml`**
```yaml
version: "3.9"
services:
  traefik:
    image: traefik:v3.1
    command:
      - --api.dashboard=true
      - --providers.docker=true
      - --providers.file.directory=/etc/traefik/dynamic
      - --providers.file.watch=true
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --certificatesresolvers.le.acme.tlschallenge=true
      - --certificatesresolvers.le.acme.email=admin@saas.akylman.online
      - --certificatesresolvers.le.acme.storage=/letsencrypt/acme.json
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik:/etc/traefik
      - le:/letsencrypt
    restart: unless-stopped

  web:
    build: ../apps/web
    env_file: ../.env
    depends_on: [api]
    labels:
      - traefik.enable=true
      - traefik.http.routers.web.rule=HostRegexp(`{subdomain:.+}.saas.akylman.online`) || Host(`saas.akylman.online`)
      - traefik.http.routers.web.entrypoints=websecure
      - traefik.http.routers.web.tls.certresolver=le
    restart: unless-stopped

  api:
    build: ../apps/api
    env_file: ../.env
    depends_on: [postgres, redis]
    labels:
      - traefik.enable=true
      - traefik.http.routers.api.rule=(HostRegexp(`{subdomain:.+}.saas.akylman.online`) || Host(`saas.akylman.online`)) && PathPrefix(`/api`)
      - traefik.http.routers.api.entrypoints=websecure
      - traefik.http.routers.api.tls.certresolver=le
      - traefik.http.services.api.loadbalancer.server.port=3000
    restart: unless-stopped

  worker:
    build: ../apps/worker
    env_file: ../.env
    depends_on: [api, redis, postgres]
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
  le:
```

**Create `infra/traefik/traefik.yml`**
```yaml
api:
  dashboard: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker: {}
  file:
    directory: /etc/traefik/dynamic
    watch: true
```

**Create `infra/traefik/dynamic.yml`**
```yaml
http:
  middlewares:
    security-headers:
      headers:
        frameDeny: true
        contentTypeNosniff: true
        referrerPolicy: no-referrer-when-downgrade
        stsSeconds: 31536000
tls:
  options:
    default:
      minVersion: VersionTLS12
```

**Acceptance**
- `docker compose up -d` starts all services.
- `https://demo.saas.akylman.online` answers once DNS is set.

---

## 2) Multi-Tenancy (subdomain + white-label)

- Resolve tenant by `Host`:
  - `subdomain.primary_domain` → tenant slug = subdomain.
  - custom domain (white-label) → find in `TenantDomain.domain`.
- Store `tenant_id` in all domain tables. Enforce filtering and permissions at the API layer.
- Add `Tenant.settings` (json) to keep theme, language, widget config.

**Core models (Django)**
- `Tenant(id, slug, name, type: 'SALON'|'SOLO', plan, seats, settings jsonb, trial_ends, status)`
- `TenantDomain(id, tenant, domain, verified_at)`
- `User(id, email, phone?, pass_hash, is_superadmin, twofa_secret?)`
- `Membership(id, user, tenant, role)`
- `Location(id, tenant, name, tz, address)`
- `ServiceCategory(id, tenant, name, sort)`
- `Service(id, tenant, category, name, duration_min, price_kgs, buffer_before, buffer_after, allow_combo)`
- `Staff(id, tenant, user?, name, skills jsonb, commission_pct)`
- `StaffService(id, staff, service, duration_override?, price_override_kgs?)`
- `Schedule(id, tenant, staff, rules jsonb, exceptions jsonb)`
- `Customer(id, tenant, name, phone, email?, dob?, tags jsonb, loyalty_points)`
- `Appointment(id, tenant, customer, staff, start_at, end_at, status, source, notes, total_price_kgs, prepaid_kgs)`
- `AppointmentService(id, appointment, service, order, duration_min, price_kgs)`
- `Payment(id, tenant, appointment?, type: 'CASH'|'CARD'|'ONLINE', provider: 'ManualCash'|'Stripe', amount_kgs, status, ext_ref?)`
- `Coupon(id, tenant, code, kind: 'PERCENT'|'FIXED', value, valid_from, valid_to, rules jsonb)`
- `GiftCard(id, tenant, code, balance_kgs, owner_customer?)`
- `LoyaltyRule(id, tenant, earn_per_100_kgs=1, redeem_rate=1)`
- `NotificationTemplate(id, tenant, kind 'email|tg', event, lang, subject, body)`
- `AuditLog(id, tenant, user?, action, entity, entity_id, meta jsonb)`
- `SaaS_Subscription(tenant, plan, seats, status, period_start, period_end, grace_until)`

**Indices**
- Composite on `(tenant_id, created_at)` for large tables.
- Unique constraints per tenant where applicable (e.g., `Coupon.code`).

**Seed**
- Superadmin, `demo` tenant, demo salon (2 staff, 5 services), demo solo master.

---

## 3) Auth & RBAC

- JWT httpOnly access+refresh with rotation and device sessions. Logout-all.
- 2FA TOTP for Superadmin and Salon Admin.
- Roles: `SUPERADMIN`, `SALON_ADMIN`, `RECEPTION`, `STAFF`, `ACCOUNTANT(RO)`.
- DRF permissions must enforce both **role** and **tenant_id**.
- Rate-limit login; CAPTCHA after 5 failures.

**API:**
- `/api/auth/register` (tenant-scoped for staff by admin), `/api/auth/login`, `/api/auth/refresh`, `/api/auth/logout`
- `/api/auth/2fa/setup`, `/api/auth/2fa/verify`

---

## 4) Booking Domain

- **Schedules:** working hours, breaks, exceptions; buffers before/after service.
- **Slot generator:** compute free slots per service/staff/location/timezone.
- **Create appointment:** transactional, with advisory lock on `(staff_id, timeslot)` to prevent double booking.
- **Statuses:** `PENDING → CONFIRMED → COMPLETED`, plus `CANCELLED`, `NO_SHOW`, `RESCHEDULED`.
- **ICS export** and Reminders (t-24h, t-2h).

**API:**
- `/api/appointments/available-slots?service=&staff=&date=`
- `POST /api/appointments` (create)
- `PATCH /api/appointments/{id}/confirm|cancel|reschedule|complete|no_show`

---

## 5) Public Widget & Pages

- Widget embed:
```html
<script src="https://{TENANT}.saas.akylman.online/widget.js"></script>
<div id="booking-widget"></div>
```
- SSR pages hosted on tenant subdomain or custom domain.
- Theming via `Tenant.settings.theme` (colors, logo, language).

---

## 6) Payments (MVP)

- Provider abstraction: `PaymentProvider` interface.
- **ManualCash:** “Оплачено наличными” action in Reception/Salon Admin UI → creates `Payment` with `type='CASH'`, `provider='ManualCash'`, `status='SUCCEEDED'`.
- **Stripe (stub):** shape endpoints for future card payments.

**API:**
- `/api/payments/mark-cash-paid` (appointment_id, amount)
- (stub) `/api/payments/stripe/create-intent`

---

## 7) Coupons, Loyalty, Birthdays

- Coupons: `%` or `fixed`, validity window, simple rule filters (by service/category/day/time).
- Loyalty: **1 point per 100 KGS**, redeem at 1:1, configurable per tenant by `LoyaltyRule`.
- Birthdays: if `dob` exists → send congrats with a coupon in the morning of the birthday.

---

## 8) Notifications (RU + KG)

- Channels: Email (required), Telegram (optional), SMS (future).
- Reminders: t-24h and t-2h; follow-up after visit.
- RU+KG templates with variables: `%customer_name%`, `%date_time%`, `%service%`, `%salon_name%`, `%tenant_url%`.

**Welcome (RU+KG) — example body to generate and store in `NotificationTemplate`:**
```
RU:
Здравствуйте, %owner_name%!
Ваш салон «%salon_name%» успешно создан: %tenant_url%
Логин: %email%
В течение 14 дней действует бесплатный пробный период.
Начните с добавления мастеров и услуг — это займет 2–3 минуты.

KG:
Саламатсызбы, %owner_name%!
Сиздин «%salon_name%» салонуңуз ийгиликтүү түзүлдү: %tenant_url%
Логин: %email%
14 күндүк акысыз сыноо мезгили иштейт.
Адегенде мастерлерди жана кызматтарды кошуңуз — 2–3 мүнөт талап кылынат.
```

---

## 9) **Auto Onboarding — One-Click Creation (Salon + SOLO)**

### Public pages (Next.js)
- `/register-salon` — button **«Создать салон»** with fields: `salon_name`, `owner_name`, `email`, `phone`, `password`, `seats`.
- `/register-solo` — button **«Я мастер»** (SOLO) with fields: `master_name`, `email`, `phone`, `password`, `specialty?`.

### API (DRF)
- `POST /api/register-salon`
- `POST /api/register-solo`

**Both endpoints must:**
- generate `Tenant` (`type='SALON'` or `type='SOLO'`), slug + subdomain `{slug}.saas.akylman.online`;
- create `User` + `Membership` (`SALON_ADMIN` for salon; for SOLO — admin = master);
- create default `Location`, sample services, set 14-day trial; `seats` (SOLO = 1);
- create **auto-login token** and return `tenant_url` like `https://{slug}.saas.akylman.online/welcome?token=...`;
- send bilingual (RU+KG) welcome email.

**Frontend handler:**
- after `success`, do `window.location.href = data.tenant_url`.

**Security:**
- Rate-limit ≤ 5/hour per IP; email verification; CAPTCHA; auto-archive inactive trials after 14 days.

---

## 10) SaaS Billing in KGS

- Plans:
  - **Solo Master** — 500 KGS/month (1 seat).
  - **Salon** — 500 KGS/month × seats (number of active masters).
- Trial: 14 days; Grace: 7 days; if overdue → block **online booking** but keep admin access.
- Manual invoices: superadmin can mark “paid” for periods.
- Feature flags per plan: seats limits, max bookings/day, SMS/Telegram, white-label, etc.

**API:**
- `/api/billing/subscription` (get/update seats/plan)
- `/api/billing/mark-invoice-paid` (superadmin)
- `/api/billing/status` (trial, grace, locked flags)

---

## 11) Admin Panels (web)

- **Superadmin:** tenants list, domains, plans/seats, subscription status, impersonate, audit, manual invoices.
- **Salon Admin:** services/categories, staff, schedules, coupons, finances, widget/theme, birthday campaigns.
- **Reception:** calendar, search customers, create/reschedule/cancel, **mark cash paid**.
- **Staff:** my appointments/schedule, quick statuses.
- All panels mobile-friendly; language switcher RU/KG/EN.

---

## 12) Reports & Exports

- Revenue by day/staff/service, no-show rate, conversion KPIs.
- CSV export for accountant (read-only role).

**API:**
- `/api/reports/revenue?from=&to=&group=staff|service|day`
- `/api/reports/no-show?from=&to=`
- `/api/reports/export.csv?...`

---

## 13) Background Jobs (Celery)

- Reminders (t-24h, t-2h), birthday campaigns (morning), auto-archive > 60 days.
- Retries with backoff for email/telegram deliveries.
- Daily digest to salon admins (yesterday’s KPIs).

---

## 14) Security & Backups

- OWASP practices: DTO validation (pydantic), CSRF on public forms, strict CORS (tenant domains only), security headers, rate-limits.
- JWT httpOnly, refresh rotation, 2FA TOTP (admin roles), audit log for critical actions.
- Postgres backups: nightly `pg_dump` with encryption, 14-day retention; tested restore script.

---

## 15) CI/CD

- GitHub Actions pipelines:
  - `lint → test → build → push images → deploy via SSH (docker compose pull && up -d)`.
- Versioned images for `web`, `api`, `worker`.
- Environment-specific `.env` (prod/stage).

---

## 16) Testing

- **Pytest (DRF):** auth, RBAC, tenant isolation, booking race (double-booking prevention), cash mark-paid, coupons.
- **Playwright (web):** E2E from widget booking to confirmation + email.
- **Load smoke:** 200 parallel bookings in 5 minutes on demo tenant → 0 double bookings.

---

## 17) Acceptance Checklist (must pass)

- [ ] `docker compose up -d` brings HTTPS online on `*.saas.akylman.online`.
- [ ] `/register-salon` and `/register-solo` create subdomains and auto-login to `/welcome`.
- [ ] Public widget embeds on any site and completes a booking.
- [ ] Reception can **mark cash paid**; payment shows in reports.
- [ ] RU+KG emails (welcome, reminders, follow-up) are sent.
- [ ] Trial/grace/lock logic works; Superadmin can mark invoice paid.
- [ ] CSV exports download correctly.
- [ ] No cross-tenant data leakage (tests prove isolation).

---

## 18) Deployment Notes (Ubuntu VPS)

> Prereq: Docker + Docker Compose plugin installed, ports 80/443 open.

```bash
# Clone repo and set up envs
git clone <your_repo> saas && cd saas
cp .env.example .env
# edit .env with real secrets and domain

# Build and run
cd infra
docker compose build
docker compose up -d

# Tail logs for first run
docker compose logs -f traefik api web worker

# (Optional) run initial migrations and seed via api container
docker compose exec api python manage.py migrate
docker compose exec api python manage.py loaddata seed_demo  # implement fixture/seed
```

**Change domain later**
- Update `.env` → `PRIMARY_DOMAIN=yourdomain.tld`
- Update DNS `A` and wildcard `*.yourdomain.tld` to VPS IP
- Restart compose; Traefik will issue fresh certs automatically.

---

## 19) What to Generate (Cursor — do this now)

1. Create the monorepo structure and boilerplates for Next.js, Django+DRF, Celery, and shared packages.
2. Add the provided `docker-compose.yml`, `traefik.yml`, `dynamic.yml` and make them work with `.env`.
3. Implement tenant host middleware, models, migrations, and seed data.
4. Implement Auth (JWT/refresh/2FA), RBAC, and enforce `tenant_id` filtering.
5. Implement booking domain (schedules, slots, appointments with advisory-lock).
6. Implement `ManualCash` provider and Stripe stub; expose REST endpoints.
7. Implement public pages `/register-salon`, `/register-solo` + DRF endpoints; auto-login and redirect to `/welcome`.
8. Implement widget script `widget.js` and SSR booking pages; theming and i18n.
9. Implement RU+KG email templates and NotificationTemplate store; test sending.
10. Implement dashboards for all roles; reports & CSV export.
11. Implement Celery beat jobs; add Prometheus metrics and Sentry hooks.
12. Add CI/CD (GitHub Actions) and backup container + restore script.
13. Add comprehensive tests (pytest + Playwright) and ensure the **Acceptance Checklist** is green.