# 🚀 Следующие шаги для запуска BeautyHub SaaS

## ✅ Статус: Домен обновлен → saas.akylman.online

Все 52 файла обновлены! Теперь платформа использует **saas.akylman.online** везде.

---

## 📋 Инструкция по запуску (пошагово)

### Шаг 1: Настройка DNS (10 минут)

Зайдите в панель управления доменом `akylman.online` и создайте:

```
Тип | Имя         | Значение (IP вашего VPS) | TTL
----|-------------|--------------------------|-----
A   | saas        | 123.45.67.89            | 3600
A   | *.saas      | 123.45.67.89            | 3600
A   | staging.saas| 123.45.67.89            | 3600
```

**Проверка:**
```bash
nslookup saas.akylman.online
# Должен вернуть ваш IP
```

⏱️ **Ожидайте 5-30 минут для DNS propagation**

---

### Шаг 2: Подготовка VPS сервера (15 минут)

```bash
# 1. Подключитесь к VPS
ssh root@<ваш-vps-ip>

# 2. Установите Docker (если еще нет)
curl -fsSL https://get.docker.com | sh
systemctl start docker
systemctl enable docker

# 3. Установите Docker Compose
apt-get update
apt-get install docker-compose-plugin

# 4. Создайте пользователя для деплоя
adduser deployer
usermod -aG docker deployer
su - deployer

# 5. Создайте директорию проекта
mkdir -p /opt/beautyhub
cd /opt/beautyhub

# 6. Клонируйте репозиторий (или загрузите код)
git clone <ваш-репозиторий> .
# Или: загрузите zip и распакуйте
```

---

### Шаг 3: Настройка окружения (10 минут)

```bash
# В директории /opt/beautyhub

# 1. Создайте .env из примера
cp .env.example .env

# 2. Отредактируйте .env
nano .env

# Обязательно измените:
PRIMARY_DOMAIN=saas.akylman.online  ✅ Уже установлено!

# Сгенерируйте секретные ключи:
JWT_ACCESS_SECRET=$(openssl rand -hex 32)
JWT_REFRESH_SECRET=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
BACKUP_ENCRYPTION_PASSWORD=$(openssl rand -hex 24)

# Настройте SMTP (для email):
SMTP_HOST=smtp.gmail.com  # или ваш SMTP
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# 3. Сохраните (Ctrl+O, Enter, Ctrl+X)
```

---

### Шаг 4: Запуск платформы (5 минут)

```bash
cd /opt/beautyhub

# 1. Запустите сервисы
docker compose -f infra/docker-compose.yml up -d

# 2. Дождитесь запуска (30-60 секунд)
docker compose -f infra/docker-compose.yml ps

# 3. Проверьте логи
docker compose -f infra/docker-compose.yml logs -f traefik
# Ищите: "Obtaining certificate for saas.akylman.online" ✅

# 4. Примените миграции
docker compose -f infra/docker-compose.yml exec api python manage.py migrate

# 5. Создайте демо данные
docker compose -f infra/docker-compose.yml exec api python manage.py seed_demo
```

---

### Шаг 5: Проверка (5 минут)

```bash
# 1. Проверьте health endpoint
curl https://saas.akylman.online/health/
# Ожидается: {"status": "ok"}

# 2. Проверьте главную страницу
curl https://saas.akylman.online/
# Должна вернуть HTML

# 3. Проверьте API
curl https://saas.akylman.online/api/health/
# Ожидается: {"status": "healthy"}

# 4. Проверьте демо салон
curl https://demo.saas.akylman.online/
# Должен открыться booking widget

# 5. Откройте в браузере
# https://saas.akylman.online/
```

---

### Шаг 6: Создание первого салона (2 минуты)

```bash
# В браузере откройте:
https://saas.akylman.online/register-salon

# Заполните форму:
• Название салона: Ваш салон
• Ваше имя: Имя владельца
• Email: your@email.com
• Телефон: +996700111111
• Пароль: Secure123!
• Количество мест: 3

# Нажмите "Создать салон"

# Вас автоматически перенаправит:
https://{ваш-slug}.saas.akylman.online/welcome

# Поздравляю! Салон создан! 🎉
```

---

## 🔒 Security Checklist

Перед продакшн запуском:

```bash
# 1. Сильные пароли
✅ JWT_ACCESS_SECRET - 32+ символов
✅ JWT_REFRESH_SECRET - 32+ символов  
✅ POSTGRES_PASSWORD - 16+ символов
✅ BACKUP_ENCRYPTION_PASSWORD - 24+ символов

# 2. Firewall
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp  # SSH
ufw enable

# 3. SSL/TLS
# Traefik автоматически получит Let's Encrypt сертификаты
# Проверьте: https://www.ssllabs.com/ssltest/

# 4. Backups
# Настроены автоматически (2 AM daily)
# Тестируйте restore:
./infra/scripts/test_backup.sh

# 5. Monitoring
# Настройте Sentry для error tracking (опционально)
```

---

## 📊 Что теперь доступно

### Публичные страницы
```
https://saas.akylman.online/             - Landing page
https://saas.akylman.online/register-salon  - Регистрация салона
https://saas.akylman.online/register-solo   - Регистрация мастера
https://demo.saas.akylman.online/           - Демо салон (booking widget)
```

### Admin панели
```
https://{tenant}.saas.akylman.online/dashboard          - Главная
https://{tenant}.saas.akylman.online/dashboard/calendar - Календарь
https://{tenant}.saas.akylman.online/dashboard/billing  - Подписка
https://{tenant}.saas.akylman.online/dashboard/reports  - Отчеты
```

### API
```
https://saas.akylman.online/api/auth/login              - Вход
https://saas.akylman.online/api/bookings/appointments/  - Записи
https://saas.akylman.online/api/payments/               - Оплаты
https://saas.akylman.online/api/reports/revenue/        - Отчеты
```

### Widget embed
```html
<!-- На любом сайте -->
<script src="https://{tenant}.saas.akylman.online/widget.js"></script>
<div id="booking-widget"></div>
```

---

## 🎯 Быстрый тест после запуска

```bash
# 1. Создайте тестовый салон
https://saas.akylman.online/register-salon
→ Заполните форму
→ Автоматический вход

# 2. Добавьте услугу
Dashboard → Услуги → + Новая
→ Название: Тестовая стрижка
→ Цена: 1000 сом
→ Длительность: 60 мин

# 3. Создайте мастера
Dashboard → Мастера → + Новый
→ Имя: Тестовый мастер
→ Выберите услуги

# 4. Создайте запись
Dashboard → Календарь → + Новая запись
→ Выберите клиента (создайте)
→ Выберите услугу и время
→ Создать

# 5. Отметьте оплату
Dashboard → Записи → Найдите запись
→ Завершить → Оплачено наличными → 1000 сом

# 6. Проверьте отчет
Dashboard → Отчеты
→ Должны увидеть выручку 1000 сом ✅

# Все работает! 🎉
```

---

## 📞 Если что-то не работает

### DNS не резолвится
- Проверьте: `nslookup saas.akylman.online 8.8.8.8`
- Подождите 30-60 минут для propagation
- Проверьте правильность A записей

### Traefik не получает TLS
- Проверьте порты 80/443: `netstat -tulpn | grep :443`
- Проверьте логи: `docker compose logs traefik`
- Убедитесь что DNS уже работает

### 502 Bad Gateway
- Проверьте сервисы: `docker compose ps`
- Перезапустите: `docker compose restart`
- Проверьте логи API: `docker compose logs api`

### Email не отправляются
- Проверьте SMTP настройки в .env
- Проверьте логи: `docker compose logs worker`
- Используйте Gmail App Password (не обычный пароль)

---

## 🎊 Поздравляю!

Ваша платформа готова к работе на домене **saas.akylman.online**!

**Следующий milestone:** Первый реальный клиент! 🚀💰

---

Полная документация:
- [README.md](README.md) - Обзор проекта
- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Деплой
- [DOMAIN_MIGRATION_SUMMARY.md](DOMAIN_MIGRATION_SUMMARY.md) - Миграция домена

**Успехов с запуском! 🎉**

