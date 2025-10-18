'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Mock data for staff member
const mockMyAppointments = [
  {
    id: '1',
    customer_name: 'Айгуль Асанова',
    customer_phone: '+996700111111',
    service: 'Женская стрижка',
    start_time: '2025-10-15T10:00:00Z',
    duration: 60,
    status: 'CONFIRMED',
    price: 800
  },
  {
    id: '2',
    customer_name: 'Бакыт Токтомов',
    customer_phone: '+996700222222',
    service: 'Мужская стрижка',
    start_time: '2025-10-15T14:00:00Z',
    duration: 30,
    status: 'PENDING',
    price: 500
  },
];

export default function MySchedulePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-4 md:p-8">
      <div className="container mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold mb-2">Мое расписание</h1>
          <p className="text-muted-foreground">Анна Иванова - Старший стилист</p>
        </div>
        
        {/* Today's Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6 text-center">
              <div className="text-2xl font-bold">8</div>
              <div className="text-sm text-muted-foreground">Сегодня</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6 text-center">
              <div className="text-2xl font-bold">6</div>
              <div className="text-sm text-muted-foreground">Завершено</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6 text-center">
              <div className="text-2xl font-bold">12,500</div>
              <div className="text-sm text-muted-foreground">Выручка (сом)</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6 text-center">
              <div className="text-2xl font-bold">4.8</div>
              <div className="text-sm text-muted-foreground">Рейтинг</div>
            </CardContent>
          </Card>
        </div>
        
        {/* Upcoming Appointments */}
        <Card>
          <CardHeader>
            <CardTitle>Предстоящие записи</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockMyAppointments.map((apt) => (
                <div key={apt.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="font-semibold">{apt.customer_name}</div>
                    <div className="text-sm text-muted-foreground">{apt.customer_phone}</div>
                    <div className="text-sm mt-1">{apt.service} • {apt.duration} минут</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(apt.start_time).toLocaleString('ru-RU')}
                    </div>
                  </div>
                  
                  <div className="flex flex-col gap-2 items-end">
                    <div className="font-semibold">{apt.price} сом</div>
                    <div className="flex gap-2">
                      {apt.status === 'PENDING' && (
                        <Button size="sm" variant="outline">
                          Подтвердить
                        </Button>
                      )}
                      <Button size="sm">
                        Завершить
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        
        {/* Working Hours */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Мой график работы</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-2 border-b">
                <span>Понедельник</span>
                <span className="font-medium">09:00 - 18:00</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>Вторник</span>
                <span className="font-medium">09:00 - 18:00</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>Среда</span>
                <span className="font-medium">09:00 - 18:00</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>Четверг</span>
                <span className="font-medium">09:00 - 18:00</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>Пятница</span>
                <span className="font-medium">09:00 - 20:00</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span>Суббота</span>
                <span className="font-medium">10:00 - 18:00</span>
              </div>
              <div className="flex justify-between py-2 text-muted-foreground">
                <span>Воскресенье</span>
                <span>Выходной</span>
              </div>
            </div>
            
            <Button variant="outline" className="w-full mt-4">
              Изменить график
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

