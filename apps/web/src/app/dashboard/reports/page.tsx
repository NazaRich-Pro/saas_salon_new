'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// Mock data for demo
const mockRevenueData = [
  { date: '2025-10-08', revenue: 12500, appointments: 8 },
  { date: '2025-10-09', revenue: 15600, appointments: 10 },
  { date: '2025-10-10', revenue: 9800, appointments: 6 },
  { date: '2025-10-11', revenue: 18400, appointments: 12 },
  { date: '2025-10-12', revenue: 21200, appointments: 14 },
];

const mockStaffRevenue = [
  { name: 'Анна Иванова', revenue: 45600, appointments: 28 },
  { name: 'Елена Петрова', revenue: 38200, appointments: 24 },
  { name: 'Мария Сидорова', revenue: 32100, appointments: 20 },
];

const mockServiceRevenue = [
  { name: 'Окрашивание', revenue: 52000, count: 32 },
  { name: 'Женская стрижка', revenue: 38400, count: 48 },
  { name: 'Укладка', revenue: 24800, count: 62 },
  { name: 'Маникюр', revenue: 18600, count: 31 },
];

export default function ReportsPage() {
  const [dateFrom, setDateFrom] = useState('2025-10-01');
  const [dateTo, setDateTo] = useState('2025-10-12');
  const [groupBy, setGroupBy] = useState<'day' | 'staff' | 'service'>('day');
  
  const totalRevenue = mockRevenueData.reduce((sum, item) => sum + item.revenue, 0);
  const totalAppointments = mockRevenueData.reduce((sum, item) => sum + item.appointments, 0);
  const avgRevenue = totalRevenue / totalAppointments;
  
  const handleExportCSV = () => {
    // In production, would call API endpoint
    alert('Экспорт CSV... В production будет скачивание файла');
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-4 md:p-8">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl md:text-3xl font-bold mb-2">Отчеты и аналитика</h1>
          <p className="text-muted-foreground">
            Анализ выручки, статистика и экспорт данных
          </p>
        </div>
        
        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Период с</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Период по</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
              
              <div>
                <label className="text-sm font-medium mb-2 block">Группировка</label>
                <select
                  className="w-full h-10 px-3 rounded-md border border-input bg-background"
                  value={groupBy}
                  onChange={(e) => setGroupBy(e.target.value as 'day' | 'staff' | 'service')}
                >
                  <option value="day">По дням</option>
                  <option value="week">По неделям</option>
                  <option value="month">По месяцам</option>
                  <option value="staff">По мастерам</option>
                  <option value="service">По услугам</option>
                </select>
              </div>
              
              <div className="flex items-end">
                <Button onClick={handleExportCSV} className="w-full">
                  📥 Экспорт CSV
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Общая выручка</div>
              <div className="text-3xl font-bold">{totalRevenue.toLocaleString()} сом</div>
              <div className="text-xs text-green-600 mt-1">↑ +12.5% vs прошлый месяц</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Записей</div>
              <div className="text-3xl font-bold">{totalAppointments}</div>
              <div className="text-xs text-green-600 mt-1">↑ +8.3%</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Средний чек</div>
              <div className="text-3xl font-bold">{Math.round(avgRevenue).toLocaleString()} сом</div>
              <div className="text-xs text-green-600 mt-1">↑ +3.8%</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Конверсия</div>
              <div className="text-3xl font-bold">87.5%</div>
              <div className="text-xs text-red-600 mt-1">↓ -2.1%</div>
            </CardContent>
          </Card>
        </div>
        
        {/* Revenue Chart (Simple Bar Chart) */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Выручка по дням</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockRevenueData.map((item, idx) => {
                const maxRevenue = Math.max(...mockRevenueData.map(d => d.revenue));
                const widthPercent = (item.revenue / maxRevenue) * 100;
                
                return (
                  <div key={idx}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="font-medium">{new Date(item.date).toLocaleDateString('ru-RU')}</span>
                      <span className="text-muted-foreground">{item.appointments} записей</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-accent rounded-full h-8 overflow-hidden">
                        <div
                          className="bg-primary h-full flex items-center justify-end px-3 text-primary-foreground text-sm font-semibold transition-all"
                          style={{ width: `${widthPercent}%` }}
                        >
                          {item.revenue.toLocaleString()} сом
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Revenue by Staff */}
          <Card>
            <CardHeader>
              <CardTitle>Топ мастера по выручке</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockStaffRevenue.map((staff, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-semibold">{staff.name}</div>
                      <div className="text-sm text-muted-foreground">{staff.appointments} записей</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-lg">{staff.revenue.toLocaleString()}</div>
                      <div className="text-xs text-muted-foreground">сом</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          
          {/* Revenue by Service */}
          <Card>
            <CardHeader>
              <CardTitle>Топ услуги по выручке</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockServiceRevenue.map((service, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <div className="font-semibold">{service.name}</div>
                      <div className="text-sm text-muted-foreground">{service.count} раз</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-lg">{service.revenue.toLocaleString()}</div>
                      <div className="text-xs text-muted-foreground">сом</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* No-show Statistics */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Статистика по no-show</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-3xl font-bold text-red-600">12</div>
                <div className="text-sm text-muted-foreground mt-1">No-show</div>
                <div className="text-xs text-muted-foreground">(8.5% от всех)</div>
              </div>
              
              <div className="text-center p-4 border rounded-lg">
                <div className="text-3xl font-bold text-yellow-600">6</div>
                <div className="text-sm text-muted-foreground mt-1">Отменено</div>
                <div className="text-xs text-muted-foreground">(4.2% от всех)</div>
              </div>
              
              <div className="text-center p-4 border rounded-lg">
                <div className="text-3xl font-bold text-red-600">18,500</div>
                <div className="text-sm text-muted-foreground mt-1">Упущено сом</div>
                <div className="text-xs text-muted-foreground">(потенциальная выручка)</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Quick Actions */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
          <Button variant="outline" onClick={handleExportCSV}>
            📄 Экспорт записей
          </Button>
          <Button variant="outline" onClick={handleExportCSV}>
            💰 Экспорт оплат
          </Button>
          <Button variant="outline">
            📊 PDF отчет
          </Button>
          <Button variant="outline">
            📧 Отправить на почту
          </Button>
        </div>
      </div>
    </div>
  );
}

