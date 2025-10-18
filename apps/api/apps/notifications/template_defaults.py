"""Default notification templates (RU + KG)"""

# Welcome email templates
WELCOME_TEMPLATES = {
    "RU": {
        "subject": "Добро пожаловать в %salon_name%!",
        "body": """Здравствуйте, %owner_name%!

Ваш салон «%salon_name%» успешно создан: %tenant_url%

Логин: %email%

В течение 14 дней действует бесплатный пробный период.
Начните с добавления мастеров и услуг — это займет 2–3 минуты.

Что дальше:
1. Добавьте услуги и цены
2. Добавьте мастеров и их расписание
3. Встройте виджет записи на ваш сайт

Если возникнут вопросы, пишите: %support_email%

С уважением,
Команда BeautyHub""",
    },
    "KG": {
        "subject": "%salon_name% га кош келиңиз!",
        "body": """Саламатсызбы, %owner_name%!

Сиздин «%salon_name%» салонуңуз ийгиликтүү түзүлдү: %tenant_url%

Логин: %email%

14 күндүк акысыз сыноо мезгили иштейт.
Адегенде мастерлерди жана кызматтарды кошуңуз — 2–3 мүнөт талап кылынат.

Кийинки кадамдар:
1. Кызматтарды жана бааларды кошуңуз
2. Мастерлерди жана алардын графигин кошуңуз
3. Виджетти сайтыңызга орнотуңуз

Суроолор болсо, жазыңыз: %support_email%

Урмат менен,
BeautyHub тобу""",
    },
}

# Reminder 24h templates
REMINDER_24H_TEMPLATES = {
    "RU": {
        "subject": "Напоминание о записи завтра",
        "body": """Здравствуйте, %customer_name%!

Напоминаем о вашей записи:

📅 Дата и время: %date_time%
💇 Услуга: %service%
👤 Мастер: %staff_name%

Салон: %salon_name%
%location%

Если не сможете прийти, пожалуйста, отмените запись заранее.

Ждем вас!
%salon_name%""",
    },
    "KG": {
        "subject": "Эртең жазылуу жөнүндө эскертүү",
        "body": """Саламатсызбы, %customer_name%!

Сиздин жазылууңуз жөнүндө эскертебиз:

📅 Дата жана убакыт: %date_time%
💇 Кызмат: %service%
👤 Уста: %staff_name%

Салон: %salon_name%
%location%

Эгер келе албасаңыз, жазылууну алдын ала жокко чыгарыңыз.

Сизди күтөбүз!
%salon_name%""",
    },
}

# Reminder 2h templates
REMINDER_2H_TEMPLATES = {
    "RU": {
        "subject": "Напоминание: запись через 2 часа",
        "body": """Здравствуйте, %customer_name%!

Напоминаем: через 2 часа у вас запись!

📅 %date_time%
💇 %service%
👤 Мастер: %staff_name%

Адрес: %location%

Ждем вас!
%salon_name%""",
    },
    "KG": {
        "subject": "Эскертүү: 2 сааттан кийин жазылуу",
        "body": """Саламатсызбы, %customer_name%!

Эскертебиз: 2 сааттан кийин жазылууңуз бар!

📅 %date_time%
💇 %service%
👤 Уста: %staff_name%

Дареги: %location%

Сизди күтөбүз!
%salon_name%""",
    },
}

# Follow-up templates
FOLLOWUP_TEMPLATES = {
    "RU": {
        "subject": "Спасибо за визит!",
        "body": """Здравствуйте, %customer_name%!

Спасибо, что посетили %salon_name%!

Мы надеемся, что вам понравилось обслуживание у мастера %staff_name%.

Ваши бонусные баллы: %loyalty_points% 🌟
Вы можете использовать их при следующей записи!

Будем рады видеть вас снова:
%tenant_url%

С уважением,
%salon_name%""",
    },
    "KG": {
        "subject": "Келгениңиз үчүн рахмат!",
        "body": """Саламатсызбы, %customer_name%!

%salon_name% га келгениңиз үчүн рахмат!

Уста %staff_name% тейлөө жакканын үмүттөнөбүз.

Сиздин bonus балларыңыз: %loyalty_points% 🌟
Кийинки жолу аларды колдоно аласыз!

Кайра күтөбүз:
%tenant_url%

Урмат менен,
%salon_name%""",
    },
}

# Birthday templates
BIRTHDAY_TEMPLATES = {
    "RU": {
        "subject": "🎉 С Днем Рождения, %customer_name%!",
        "body": """Здравствуйте, %customer_name%!

Поздравляем вас с Днем Рождения! 🎂🎉

В честь вашего праздника дарим купон на скидку %discount_percent%%:

🎁 Код купона: %coupon_code%
📅 Действителен до: %valid_until%

Запишитесь на любую услугу и получите скидку:
%tenant_url%

Желаем здоровья, красоты и радости!

С наилучшими пожеланиями,
%salon_name%""",
    },
    "KG": {
        "subject": "🎉 Туулган күнүңүз менен, %customer_name%!",
        "body": """Саламатсызбы, %customer_name%!

Сизди туулган күнүңүз менен куттуктайбыз! 🎂🎉

Майрамыңызга арналган %discount_percent%% арзандатуу купону:

🎁 Купон коду: %coupon_code%
📅 Жарактуу: %valid_until% чейин

Каалаган кызматка жазылыңыз жана арзандатуу алыңыз:
%tenant_url%

Ден соолук, сулуулук жана кубанычты каалайбыз!

Урмат менен,
%salon_name%""",
    },
}

# Daily digest template (for salon admins)
DAILY_DIGEST_TEMPLATES = {
    "RU": {
        "subject": "Ежедневный отчет %salon_name% - %date%",
        "body": """Здравствуйте!

Статистика за %date%:

📅 Записей: %appointments_count%
✅ Завершено: %completed_count%
❌ Отменено: %cancelled_count%
🚫 Не явились: %no_show_count%

💰 Выручка: %revenue_kgs% сом
💵 Из них наличными: %cash_revenue_kgs% сом

👥 Новых клиентов: %new_customers%
🌟 Начислено баллов: %points_awarded%

Записи на сегодня: %today_appointments%

Полный отчет: %tenant_url%/dashboard/reports

С уважением,
BeautyHub""",
    },
    "KG": {
        "subject": "%salon_name% - Күндөлүк отчет %date%",
        "body": """Саламатсызбы!

%date% үчүн статистика:

📅 Жазылуулар: %appointments_count%
✅ Аяктады: %completed_count%
❌ Жокко чыгарылды: %cancelled_count%
🚫 Келген жок: %no_show_count%

💰 Киреше: %revenue_kgs% сом
💵 Накталай: %cash_revenue_kgs% сом

👥 Жаңы кардарлар: %new_customers%
🌟 Баллар: %points_awarded%

Бүгүнгү жазылуулар: %today_appointments%

Толук отчет: %tenant_url%/dashboard/reports

Урмат менен,
BeautyHub""",
    },
}

# All default templates
DEFAULT_TEMPLATES = {
    "WELCOME": WELCOME_TEMPLATES,
    "REMINDER_24H": REMINDER_24H_TEMPLATES,
    "REMINDER_2H": REMINDER_2H_TEMPLATES,
    "FOLLOWUP": FOLLOWUP_TEMPLATES,
    "BIRTHDAY": BIRTHDAY_TEMPLATES,
    "DAILY_DIGEST": DAILY_DIGEST_TEMPLATES,
}
