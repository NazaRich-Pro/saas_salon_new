'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Mock birthday data
const todaysBirthdays = [
  { name: 'Айгуль Асанова', phone: '+996700111111', email: 'aigul@example.com', dob: '1990-10-12' },
];

const upcomingBirthdays = [
  { name: 'Бакыт Токтомов', phone: '+996700222222', email: 'bakyt@example.com', dob: '1985-10-15', days_until: 3 },
  { name: 'Гульмира Жумабаева', phone: '+996700333333', email: 'gulmira@example.com', dob: '1995-10-18', days_until: 6 },
];

export default function BirthdaysPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-8">
      <div className="container mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">🎂 Дни рождения клиентов</h1>
          <p className="text-muted-foreground">Поздравления и birthday-кампании</p>
        </div>
        
        {/* Today's Birthdays */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>🎉 Сегодня день рождения</span>
              {todaysBirthdays.length > 0 && (
                <Button size="sm">
                  Отправить всем поздравления
                </Button>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {todaysBirthdays.length > 0 ? (
              <div className="space-y-3">
                {todaysBirthdays.map((customer, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 border rounded-lg bg-yellow-50 dark:bg-yellow-950">
                    <div>
                      <div className="font-semibold">{customer.name}</div>
                      <div className="text-sm text-muted-foreground">{customer.phone}</div>
                      <div className="text-sm text-muted-foreground">{customer.email}</div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button size="sm">
                        📧 Отправить поздравление
                      </Button>
                      <Button size="sm" variant="outline">
                        🎟️ Создать купон
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Сегодня нет именинников
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Upcoming Birthdays */}
        <Card>
          <CardHeader>
            <CardTitle>Ближайшие дни рождения (7 дней)</CardTitle>
          </CardHeader>
          <CardContent>
            {upcomingBirthdays.length > 0 ? (
              <div className="space-y-3">
                {upcomingBirthdays.map((customer, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-medium">{customer.name}</div>
                      <div className="text-sm text-muted-foreground">{customer.phone}</div>
                      <div className="text-sm text-muted-foreground">{customer.email}</div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-sm font-semibold text-primary">
                        через {customer.days_until} {customer.days_until === 1 ? 'день' : 'дней'}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(customer.dob).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Нет ближайших дней рождения
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Campaign Settings */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Настройки birthday-кампаний</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Скидка в подарок (%)</Label>
                <Input type="number" defaultValue="20" min="0" max="100" />
              </div>
              
              <div>
                <Label>Срок действия купона (дней)</Label>
                <Input type="number" defaultValue="30" min="1" max="365" />
              </div>
            </div>
            
            <div className="bg-accent/50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Автоматическая отправка</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Каждое утро в 9:00 система автоматически:
              </p>
              <ul className="text-sm space-y-1">
                <li>✓ Находит именинников дня</li>
                <li>✓ Создает персональный купон со скидкой</li>
                <li>✓ Отправляет email с поздравлением</li>
                <li>✓ Купон действует 30 дней</li>
              </ul>
            </div>
            
            <Button>Сохранить настройки</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

