'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { format, addDays, startOfWeek, addWeeks, subWeeks } from 'date-fns';
import { ru } from 'date-fns/locale';

// Mock appointments for calendar view
const mockAppointments = [
  {
    id: '1',
    customer_name: 'Айгуль Асанова',
    staff_name: 'Анна Иванова',
    service: 'Женская стрижка',
    start_time: '10:00',
    duration: 60,
    status: 'CONFIRMED',
    date: format(new Date(), 'yyyy-MM-dd')
  },
  {
    id: '2',
    customer_name: 'Бакыт Токтомов',
    staff_name: 'Елена Петрова',
    service: 'Окрашивание',
    start_time: '14:00',
    duration: 120,
    status: 'PENDING',
    date: format(new Date(), 'yyyy-MM-dd')
  },
];

export default function CalendarPage() {
  const [currentWeek, setCurrentWeek] = useState(new Date());
  const [viewMode, setViewMode] = useState<'day' | 'week'>('week');
  
  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 }); // Monday
  
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));
  const hours = Array.from({ length: 12 }, (_, i) => i + 9); // 9 AM - 8 PM
  
  const goToPrevWeek = () => setCurrentWeek(subWeeks(currentWeek, 1));
  const goToNextWeek = () => setCurrentWeek(addWeeks(currentWeek, 1));
  const goToToday = () => setCurrentWeek(new Date());
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-4 md:p-8">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold mb-2">Календарь записей</h1>
            <p className="text-muted-foreground">
              {format(weekStart, 'd MMMM', { locale: ru })} - {format(addDays(weekStart, 6), 'd MMMM yyyy', { locale: ru })}
            </p>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={goToPrevWeek}>
              ← Пред
            </Button>
            <Button variant="outline" size="sm" onClick={goToToday}>
              Сегодня
            </Button>
            <Button variant="outline" size="sm" onClick={goToNextWeek}>
              След →
            </Button>
          </div>
        </div>
        
        {/* View mode toggle */}
        <div className="mb-4 flex gap-2">
          <Button
            variant={viewMode === 'day' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('day')}
          >
            День
          </Button>
          <Button
            variant={viewMode === 'week' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('week')}
          >
            Неделя
          </Button>
        </div>
        
        {/* Calendar Grid */}
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <div className="min-w-[800px]">
                {/* Header row with days */}
                <div className="grid grid-cols-8 border-b bg-accent/50">
                  <div className="p-2 font-semibold text-sm">Время</div>
                  {days.map((day, idx) => {
                    const isToday = format(day, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');
                    return (
                      <div
                        key={idx}
                        className={`p-2 text-center ${isToday ? 'bg-primary/10' : ''}`}
                      >
                        <div className="font-semibold text-sm">
                          {format(day, 'EEE', { locale: ru })}
                        </div>
                        <div className={`text-xs ${isToday ? 'font-bold text-primary' : 'text-muted-foreground'}`}>
                          {format(day, 'd MMM', { locale: ru })}
                        </div>
                      </div>
                    );
                  })}
                </div>
                
                {/* Time slots */}
                {hours.map((hour) => (
                  <div key={hour} className="grid grid-cols-8 border-b">
                    <div className="p-2 text-sm text-muted-foreground border-r">
                      {hour}:00
                    </div>
                    {days.map((day, dayIdx) => {
                      const dateStr = format(day, 'yyyy-MM-dd');
                      const timeStr = `${hour}:00`;
                      
                      // Find appointments for this slot
                      const appointment = mockAppointments.find(
                        apt => apt.date === dateStr && apt.start_time.startsWith(hour.toString())
                      );
                      
                      return (
                        <div
                          key={dayIdx}
                          className="p-1 border-r hover:bg-accent/30 cursor-pointer min-h-[60px]"
                        >
                          {appointment && (
                            <div className={`
                              p-2 rounded text-xs
                              ${appointment.status === 'CONFIRMED' ? 'bg-green-100 border-green-300' : 'bg-yellow-100 border-yellow-300'}
                              border
                            `}>
                              <div className="font-semibold truncate">{appointment.customer_name}</div>
                              <div className="text-muted-foreground truncate">{appointment.service}</div>
                              <div className="text-muted-foreground">{appointment.start_time}</div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Quick actions */}
        <div className="mt-6 flex gap-3">
          <Button>+ Новая запись</Button>
          <Button variant="outline">Фильтры</Button>
          <Button variant="outline">Экспорт</Button>
        </div>
      </div>
    </div>
  );
}

