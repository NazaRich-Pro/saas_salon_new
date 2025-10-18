# DNS Setup для saas.akylman.online

## 📋 Инструкция по настройке DNS

### 1. Основной домен

**Type:** A Record  
**Host:** `saas` (или `@` если хотите akylman.online напрямую)  
**Value:** `<IP вашего VPS сервера>`  
**TTL:** 3600 (1 час)

**Результат:** `saas.akylman.online` → VPS IP

---

### 2. Wildcard для поддоменов (Multi-Tenancy)

**Type:** A Record  
**Host:** `*.saas` (wildcard)  
**Value:** `<IP вашего VPS сервера>`  
**TTL:** 3600

**Результат:**
- `demo.saas.akylman.online` → VPS IP
- `salon1.saas.akylman.online` → VPS IP
- `{любой-поддомен}.saas.akylman.online` → VPS IP

---

### 3. Staging (опционально)

**Type:** A Record  
**Host:** `staging.saas`  
**Value:** `<IP staging сервера>` (или тот же VPS)  
**TTL:** 3600

**Результат:** `staging.saas.akylman.online` → VPS IP

---

## 🎯 Пример конфигурации (CloudFlare / Регистратор)

```
Тип   | Имя         | Значение           | TTL  | Proxy
------|-------------|-------------------|------|------
A     | saas        | 123.45.67.89      | 3600 | ❌
A     | *.saas      | 123.45.67.89      | 3600 | ❌
A     | staging.saas| 123.45.67.89      | 3600 | ❌
```

**⚠️ ВАЖНО:** Отключите Cloudflare Proxy (оранжевое облако) для Let's Encrypt!

---

## ✅ Проверка настройки DNS

### Команды для проверки:

```bash
# Проверить основной домен
nslookup saas.akylman.online

# Проверить wildcard
nslookup demo.saas.akylman.online
nslookup test.saas.akylman.online

# Проверить staging
nslookup staging.saas.akylman.online

# Или используйте dig (Linux)
dig saas.akylman.online +short
dig demo.saas.akylman.online +short
```

**Ожидаемый результат:** Все должны вернуть ваш VPS IP

---

## ⏱️ Время propagation

- **Обычно:** 5-30 минут
- **Максимум:** 48 часов (редко)
- **CloudFlare:** 1-5 минут

### Как ускорить:

1. Используйте низкий TTL (300-3600)
2. CloudFlare DNS (быстрый)
3. Flush DNS cache локально:
   ```bash
   # Windows
   ipconfig /flushdns
   
   # Linux/Mac
   sudo systemd-resolve --flush-caches
   ```

---

## 🔒 TLS Сертификаты

### Traefik автоматически получит сертификаты

После настройки DNS и запуска Docker:

```bash
# Traefik использует ACME (Let's Encrypt)
# Логи Traefik покажут процесс:
docker compose logs traefik | grep -i acme

# Ожидаемые сообщения:
✓ Obtaining certificate for saas.akylman.online
✓ Obtaining certificate for *.saas.akylman.online
✓ Certificates stored in /letsencrypt/acme.json
```

**Сертификаты будут валидны для:**
- `saas.akylman.online`
- `*.saas.akylman.online` (wildcard)
- Все поддомены автоматически

---

## 🚨 Troubleshooting

### DNS не резолвится

```bash
# Проверить у разных DNS серверов
nslookup saas.akylman.online 8.8.8.8       # Google DNS
nslookup saas.akylman.online 1.1.1.1       # Cloudflare DNS

# Если работает у одних, но не у других = ждите propagation
```

### Traefik не получает сертификат

```bash
# Проверить логи
docker compose logs traefik

# Частые причины:
# 1. DNS еще не propagated
# 2. Порты 80/443 закрыты
# 3. Cloudflare Proxy включен
# 4. Firewall блокирует Let's Encrypt

# Решение:
# - Дождитесь DNS propagation
# - Откройте порты: ufw allow 80/tcp && ufw allow 443/tcp
# - Отключите Cloudflare Proxy
```

### 502 Bad Gateway

```bash
# Проверить что все сервисы запущены
docker compose ps

# Проверить логи
docker compose logs web
docker compose logs api

# Перезапустить
docker compose restart
```

---

## 📞 Support

Если возникли проблемы с DNS:
- Документация регистратора домена
- Support регистратора
- Cloudflare Help Center (если используете)

---

## ✅ After DNS Setup

После успешной настройки DNS:

```bash
# 1. Обновить .env на сервере
PRIMARY_DOMAIN=saas.akylman.online

# 2. Перезапустить
docker compose down
docker compose up -d

# 3. Дождаться TLS (1-2 минуты)

# 4. Проверить
curl https://saas.akylman.online/
# ✅ Should return 200 OK
```

---

**Готово! DNS настройка завершена!** 🎉

