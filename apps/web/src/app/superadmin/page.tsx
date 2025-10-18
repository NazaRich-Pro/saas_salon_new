'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

// Mock data
const mockTenants = [
  {
    id: '1',
    slug: 'demo-salon',
    name: 'Демо Салон Красоты',
    type: 'SALON',
    status: 'TRIAL',
    seats: 3,
    trial_ends: '2025-10-25',
    appointments_count: 45,
    revenue: 12500
  },
  {
    id: '2',
    slug: 'demo-solo',
    name: 'Мастер Алия',
    type: 'SOLO',
    status: 'ACTIVE',
    seats: 1,
    appointments_count: 28,
    revenue: 8400
  },
  {
    id: '3',
    slug: 'beauty-center',
    name: 'Beauty Center',
    type: 'SALON',
    status: 'GRACE',
    seats: 5,
    trial_ends: '2025-10-18',
    appointments_count: 120,
    revenue: 45000
  },
];

export default function SuperadminPage() {
  const totalTenants = mockTenants.length;
  const activeTenants = mockTenants.filter(t => t.status === 'ACTIVE').length;
  const trialTenants = mockTenants.filter(t => t.status === 'TRIAL').length;
  const totalRevenue = mockTenants.reduce((sum, t) => sum + t.revenue, 0);
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-4 md:p-8">
      <div className="container mx-auto max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Superadmin Dashboard</h1>
          <p className="text-muted-foreground">Управление платформой BeautyHub</p>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Всего салонов</div>
              <div className="text-3xl font-bold">{totalTenants}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Активных</div>
              <div className="text-3xl font-bold text-green-600">{activeTenants}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">На пробном</div>
              <div className="text-3xl font-bold text-blue-600">{trialTenants}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Общая выручка</div>
              <div className="text-3xl font-bold">{totalRevenue.toLocaleString()} сом</div>
            </CardContent>
          </Card>
        </div>
        
        {/* Tenants List */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Список салонов</CardTitle>
              <Input
                placeholder="Поиск..."
                className="max-w-xs"
              />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {mockTenants.map((tenant) => (
                <div key={tenant.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <div className="font-semibold text-lg">{tenant.name}</div>
                      <div className={`text-xs px-2 py-1 rounded ${
                        tenant.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                        tenant.status === 'TRIAL' ? 'bg-blue-100 text-blue-800' :
                        tenant.status === 'GRACE' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {tenant.status}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {tenant.type} • {tenant.seats} {tenant.seats === 1 ? 'место' : 'мест'}
                      </div>
                    </div>
                    
                    <div className="text-sm text-muted-foreground mt-1">
                      {tenant.slug}.saas.akylman.online
                    </div>
                    
                    <div className="text-sm mt-2 flex gap-4">
                      <span>📅 Записей: {tenant.appointments_count}</span>
                      <span>💰 Выручка: {tenant.revenue.toLocaleString()} сом</span>
                      {tenant.trial_ends && (
                        <span>⏰ До: {new Date(tenant.trial_ends).toLocaleDateString('ru-RU')}</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      Просмотр
                    </Button>
                    <Button variant="outline" size="sm">
                      Отметить оплату
                    </Button>
                    <Button variant="ghost" size="sm">
                      Impersonate
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        
        {/* Quick actions */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="cursor-pointer hover:border-primary transition-colors">
            <CardContent className="pt-6 text-center">
              <div className="text-4xl mb-2">📊</div>
              <div className="font-semibold">Аналитика</div>
              <div className="text-sm text-muted-foreground">Общая статистика платформы</div>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:border-primary transition-colors">
            <CardContent className="pt-6 text-center">
              <div className="text-4xl mb-2">🔍</div>
              <div className="font-semibold">Audit Log</div>
              <div className="text-sm text-muted-foreground">История всех действий</div>
            </CardContent>
          </Card>
          
          <Card className="cursor-pointer hover:border-primary transition-colors">
            <CardContent className="pt-6 text-center">
              <div className="text-4xl mb-2">🌐</div>
              <div className="font-semibold">Домены</div>
              <div className="text-sm text-muted-foreground">Custom domains для white-label</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

