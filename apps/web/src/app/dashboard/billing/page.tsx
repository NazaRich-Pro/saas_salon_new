'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

// Mock data
const mockSubscription = {
  plan: 'SALON',
  seats: 3,
  status: 'TRIAL',
  monthly_price_kgs: '1500.00',
  period_start: '2025-10-01',
  period_end: '2025-10-31',
  days_until_expiry: 10,
};

const mockFeatures = {
  max_seats: 50,
  max_bookings_per_day: 200,
  sms_enabled: true,
  telegram_enabled: true,
  white_label: true,
  api_access: true,
  priority_support: true,
};

export default function BillingPage() {
  const [seats, setSeats] = useState(mockSubscription.seats);
  const [loading, setLoading] = useState(false);
  
  const handleUpdateSeats = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/payments/billing/subscription/update-seats/', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ seats: parseInt(seats.toString()) })
      });
      
      if (response.ok) {
        alert('Количество мест обновлено!');
      } else {
        alert('Ошибка при обновлении');
      }
    } catch (err) {
      alert('Ошибка при обновлении');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-8">
      <div className="container mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Подписка и биллинг</h1>
          <p className="text-muted-foreground">Управление вашей подпиской</p>
        </div>
        
        {/* Current Status */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Текущая подписка</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-muted-foreground mb-1">План</div>
                <div className="text-lg font-semibold">
                  {mockSubscription.plan === 'SOLO' ? 'Solo Master' : 'Salon'}
                </div>
              </div>
              
              <div>
                <div className="text-sm text-muted-foreground mb-1">Статус</div>
                <div className={`text-lg font-semibold ${
                  mockSubscription.status === 'TRIAL' ? 'text-blue-600' :
                  mockSubscription.status === 'ACTIVE' ? 'text-green-600' :
                  mockSubscription.status === 'GRACE' ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {mockSubscription.status === 'TRIAL' ? 'Пробный период' :
                   mockSubscription.status === 'ACTIVE' ? 'Активна' :
                   mockSubscription.status === 'GRACE' ? 'Льготный период' :
                   'Приостановлена'}
                </div>
              </div>
              
              <div>
                <div className="text-sm text-muted-foreground mb-1">Стоимость</div>
                <div className="text-lg font-semibold">
                  {mockSubscription.monthly_price_kgs} сом/мес
                </div>
              </div>
              
              <div>
                <div className="text-sm text-muted-foreground mb-1">Осталось дней</div>
                <div className="text-lg font-semibold">
                  {mockSubscription.days_until_expiry}
                </div>
              </div>
            </div>
            
            {mockSubscription.status === 'TRIAL' && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200">
                <div className="font-semibold mb-1">🎁 Пробный период</div>
                <p className="text-sm text-muted-foreground">
                  Бесплатный доступ ко всем функциям до {new Date(mockSubscription.period_end).toLocaleDateString('ru-RU')}
                </p>
              </div>
            )}
            
            {mockSubscription.status === 'GRACE' && (
              <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-950 rounded-lg border border-yellow-200">
                <div className="font-semibold mb-1">⚠️ Льготный период</div>
                <p className="text-sm text-muted-foreground">
                  Оплатите подписку в течение {mockSubscription.days_until_expiry} дней для продолжения работы
                </p>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Manage Seats */}
        {mockSubscription.plan === 'SALON' && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Управление местами</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="seats">Количество активных мастеров</Label>
                <div className="flex gap-4 items-center mt-2">
                  <Input
                    id="seats"
                    type="number"
                    min="1"
                    max="50"
                    value={seats}
                    onChange={(e) => setSeats(parseInt(e.target.value))}
                    className="max-w-xs"
                  />
                  <Button
                    onClick={handleUpdateSeats}
                    disabled={loading || seats === mockSubscription.seats}
                  >
                    {loading ? 'Обновление...' : 'Обновить'}
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground mt-2">
                  Стоимость: {seats} × 500 = {seats * 500} сом/месяц
                </p>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Features */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Доступные функции</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center gap-2">
                <span className={mockFeatures.sms_enabled ? 'text-green-600' : 'text-gray-400'}>
                  {mockFeatures.sms_enabled ? '✓' : '✗'}
                </span>
                <span>SMS уведомления</span>
              </div>
              
              <div className="flex items-center gap-2">
                <span className={mockFeatures.telegram_enabled ? 'text-green-600' : 'text-gray-400'}>
                  {mockFeatures.telegram_enabled ? '✓' : '✗'}
                </span>
                <span>Telegram интеграция</span>
              </div>
              
              <div className="flex items-center gap-2">
                <span className={mockFeatures.white_label ? 'text-green-600' : 'text-gray-400'}>
                  {mockFeatures.white_label ? '✓' : '✗'}
                </span>
                <span>White-label (свой домен)</span>
              </div>
              
              <div className="flex items-center gap-2">
                <span className={mockFeatures.api_access ? 'text-green-600' : 'text-gray-400'}>
                  {mockFeatures.api_access ? '✓' : '✗'}
                </span>
                <span>API доступ</span>
              </div>
              
              <div className="flex items-center gap-2">
                <span className={mockFeatures.priority_support ? 'text-green-600' : 'text-gray-400'}>
                  {mockFeatures.priority_support ? '✓' : '✗'}
                </span>
                <span>Приоритетная поддержка</span>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>До {mockFeatures.max_bookings_per_day} записей/день</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Payment Info */}
        <Card>
          <CardHeader>
            <CardTitle>Информация об оплате</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-accent/50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Реквизиты для оплаты</h4>
              <div className="text-sm space-y-1">
                <div><strong>Получатель:</strong> ОсОО "BeautyHub"</div>
                <div><strong>ИНН:</strong> 12345678901234</div>
                <div><strong>Счет:</strong> KG123456789012345678901234</div>
                <div><strong>Банк:</strong> ЗАО "Демир Банк"</div>
                <div><strong>Назначение:</strong> Оплата подписки за {new Date().toLocaleString('ru-RU', {month: 'long', year: 'numeric'})}</div>
              </div>
            </div>
            
            <div className="text-sm text-muted-foreground">
              После оплаты свяжитесь с поддержкой: support@saas.akylman.online
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

