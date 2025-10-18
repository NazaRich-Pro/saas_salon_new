# Domain Migration: beautyhub.kitty → saas.akylman.online

## Дата миграции: 2025-10-12

## ✅ Статус: Завершено

Домен успешно изменен во всем проекте с `beautyhub.kitty` на `saas.akylman.online`.

---

## 📝 Изменения

### Обновленные файлы (52):

#### Configuration Files
- ✅ `.env.example` - PRIMARY_DOMAIN
- ✅ `infra/docker-compose.yml` - Traefik rules, ACME email
- ✅ `apps/api/config/settings.py` - ALLOWED_HOSTS, CORS
- ✅ `apps/web/next.config.js` - Domain configuration

#### Backend Code (Python)
- ✅ `apps/api/apps/tenants/middleware.py` - Tenant resolution
- ✅ `apps/api/apps/tenants/onboarding_service.py` - Auto-login URLs
- ✅ `apps/api/apps/tenants/views.py` - Registration endpoints
- ✅ `apps/api/apps/notifications/email_service.py` - Email templates
- ✅ `apps/api/apps/notifications/telegram_service.py` - Telegram messages
- ✅ `apps/api/apps/bookings/tasks.py` - Daily digest
- ✅ `apps/api/apps/payments/birthday_service.py` - Birthday emails
- ✅ `apps/api/apps/booking/ics_export.py` - Calendar export
- ✅ `apps/api/apps/tenants/management/commands/seed_demo.py` - Demo data
- ✅ `apps/api/apps/tenants/tests/test_onboarding.py` - Tests

#### Frontend Code (Next.js)
- ✅ `apps/web/public/widget.js` - Widget script
- ✅ `apps/web/src/app/page.tsx` - Landing page
- ✅ `apps/web/src/app/layout.tsx` - Layout metadata
- ✅ `apps/web/src/app/widget/page.tsx` - Widget page
- ✅ `apps/web/src/app/book/page.tsx` - Booking page
- ✅ `apps/web/src/app/embed-demo.html` - Demo embed
- ✅ `apps/web/src/app/dashboard/billing/page.tsx` - Billing dashboard
- ✅ `apps/web/src/app/superadmin/page.tsx` - Superadmin dashboard

#### GitHub Actions
- ✅ `.github/workflows/deploy-staging.yml` - staging.saas.akylman.online
- ✅ `.github/workflows/deploy-production.yml` - saas.akylman.online
- ✅ `.github/workflows/cleanup.yml` - Image cleanup

#### Documentation (27 files)
- ✅ `BeautyHub_SaaS_Cursor_MasterPrompt.md` - Master prompt
- ✅ `README.md` - Main documentation
- ✅ `CHANGELOG.md` - Change log
- ✅ `STATUS.md` - Project status
- ✅ `SECURITY.md` - Security documentation
- ✅ `QUICKSTART.md` - Quick start guide
- ✅ `docs/ARCHITECTURE.md` - Architecture
- ✅ `docs/API.md` - API documentation
- ✅ `docs/DEPLOYMENT.md` - Deployment guide
- ✅ `docs/DNS_SETUP.md` - DNS setup
- ✅ `STAGE_0_COMPLETE.md` through `STAGE_15_COMPLETE.md` - All stage docs
- ✅ `SUMMARY_STAGES_0-4.md` - Summary docs
- ✅ `STAGE_3_SUMMARY.md`, `STAGE_5_SUMMARY.md`, `STAGE_9_SUMMARY.md`
- ✅ `MVP_COMPLETE.md` - MVP documentation
- ✅ `FINAL_SUMMARY.md` - Final summary
- ✅ `PROJECT_STATUS_REPORT.md` - Status report

**Total Files Updated:** 52

---

## 🌐 DNS Configuration Required

### Настройте DNS записи для домена `saas.akylman.online`:

```
Type: A
Host: @
Value: <ваш VPS IP>
TTL: 3600

Type: A (wildcard)
Host: *
Value: <ваш VPS IP>
TTL: 3600
```

**Примеры поддоменов:**
- `saas.akylman.online` - главная страница
- `demo.saas.akylman.online` - демо салон
- `staging.saas.akylman.online` - staging environment
- `{tenant-slug}.saas.akylman.online` - каждый салон

---

## 🔧 Что делать дальше:

### 1. Обновить .env файл

```bash
# На production сервере
cd /opt/beautyhub
nano .env

# Изменить:
PRIMARY_DOMAIN=saas.akylman.online
```

### 2. Настроить DNS

В панели управления доменом (где купили akylman.online):
- Создать A запись: `saas` → ваш VPS IP
- Создать A запись: `*.saas` → ваш VPS IP
- Дождаться propagation (5-60 минут)

### 3. Перезапустить сервисы

```bash
# Traefik автоматически получит новые TLS сертификаты
cd /opt/beautyhub
docker compose down
docker compose up -d

# Проверить логи Traefik
docker compose logs traefik | grep acme
```

### 4. Проверить работу

```bash
# Проверить main domain
curl https://saas.akylman.online/

# Проверить subdomain
curl https://demo.saas.akylman.online/

# Проверить API
curl https://saas.akylman.online/api/health/
```

---

## 📋 Checklist

- [x] Заменить во всех Python файлах
- [x] Заменить во всех TypeScript/JavaScript файлах
- [x] Заменить в Docker Compose
- [x] Заменить в GitHub Actions
- [x] Заменить во всей документации
- [x] Обновить .env.example
- [ ] Обновить .env на сервере (вручную)
- [ ] Настроить DNS (вручную)
- [ ] Перезапустить Docker services (вручную)
- [ ] Проверить TLS certificates (автоматически через Traefik)

---

## 🔍 Verification

Проверено grep'ом: **0 вхождений** старого домена в коде! ✅

Все файлы обновлены и готовы к использованию с новым доменом.

---

## 🎉 Ready to Deploy!

После настройки DNS и обновления .env на сервере, платформа будет доступна по адресу:

**Main:** https://saas.akylman.online  
**Demo:** https://demo.saas.akylman.online  
**Staging:** https://staging.saas.akylman.online  

**Wildcard TLS:** Traefik автоматически получит Let's Encrypt сертификаты для всех поддоменов.

---

Last Updated: 2025-10-12

