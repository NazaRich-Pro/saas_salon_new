'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

// Mock coupon data
const mockCoupons = [
  {
    id: '1',
    code: 'WELCOME20',
    kind: 'PERCENT',
    value: '20.00',
    valid_from: '2025-10-01T00:00:00Z',
    valid_to: '2025-12-31T23:59:59Z',
    max_uses: 100,
    uses_count: 15,
    is_active: true
  },
  {
    id: '2',
    code: 'FIXED500',
    kind: 'FIXED',
    value: '500.00',
    valid_from: '2025-10-01T00:00:00Z',
    valid_to: '2025-10-31T23:59:59Z',
    max_uses: 50,
    uses_count: 8,
    is_active: true
  },
];

export default function CouponsPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    kind: 'PERCENT',
    value: '',
    valid_days: '30',
    max_uses: '100',
  });
  
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Create coupon via API
    console.log('Creating coupon:', formData);
    
    // Reset form
    setFormData({
      code: '',
      kind: 'PERCENT',
      value: '',
      valid_days: '30',
      max_uses: '100',
    });
    setShowCreateForm(false);
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-8">
      <div className="container mx-auto max-w-4xl">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Купоны и скидки</h1>
            <p className="text-muted-foreground">Управление промокодами</p>
          </div>
          <Button onClick={() => setShowCreateForm(!showCreateForm)}>
            + Создать купон
          </Button>
        </div>
        
        {/* Create Form */}
        {showCreateForm && (
          <Card className="mb-6">
            <form onSubmit={handleCreate}>
              <CardHeader>
                <CardTitle>Новый купон</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="code">Код купона *</Label>
                    <Input
                      id="code"
                      value={formData.code}
                      onChange={(e) => setFormData({...formData, code: e.target.value.toUpperCase()})}
                      placeholder="DISCOUNT20"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="kind">Тип скидки *</Label>
                    <select
                      id="kind"
                      value={formData.kind}
                      onChange={(e) => setFormData({...formData, kind: e.target.value})}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      <option value="PERCENT">Процент (%)</option>
                      <option value="FIXED">Фиксированная сумма (сом)</option>
                    </select>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="value">
                      Значение * {formData.kind === 'PERCENT' ? '(%)' : '(сом)'}
                    </Label>
                    <Input
                      id="value"
                      type="number"
                      step="0.01"
                      value={formData.value}
                      onChange={(e) => setFormData({...formData, value: e.target.value})}
                      placeholder={formData.kind === 'PERCENT' ? '20' : '500'}
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="valid_days">Действителен (дней)</Label>
                    <Input
                      id="valid_days"
                      type="number"
                      value={formData.valid_days}
                      onChange={(e) => setFormData({...formData, valid_days: e.target.value})}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="max_uses">Макс. использований</Label>
                    <Input
                      id="max_uses"
                      type="number"
                      value={formData.max_uses}
                      onChange={(e) => setFormData({...formData, max_uses: e.target.value})}
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex gap-2">
                <Button type="submit">Создать купон</Button>
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Отмена
                </Button>
              </CardFooter>
            </form>
          </Card>
        )}
        
        {/* Coupons List */}
        <div className="space-y-4">
          {mockCoupons.map((coupon) => (
            <Card key={coupon.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-3">
                      <div className="text-2xl font-bold font-mono bg-accent px-3 py-1 rounded">
                        {coupon.code}
                      </div>
                      {coupon.is_active ? (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                          Активен
                        </span>
                      ) : (
                        <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                          Неактивен
                        </span>
                      )}
                    </div>
                    
                    <div className="mt-3 space-y-1 text-sm">
                      <div>
                        <strong>Скидка:</strong>{' '}
                        {coupon.kind === 'PERCENT' 
                          ? `${coupon.value}%` 
                          : `${coupon.value} сом`
                        }
                      </div>
                      <div>
                        <strong>Действует до:</strong>{' '}
                        {new Date(coupon.valid_to).toLocaleDateString('ru-RU')}
                      </div>
                      <div>
                        <strong>Использовано:</strong>{' '}
                        {coupon.uses_count} / {coupon.max_uses || '∞'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      Редактировать
                    </Button>
                    <Button variant="destructive" size="sm">
                      Деактивировать
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        
        {mockCoupons.length === 0 && !showCreateForm && (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="text-4xl mb-4">🎟️</div>
              <h3 className="text-lg font-semibold mb-2">Нет активных купонов</h3>
              <p className="text-muted-foreground mb-4">
                Создайте первый купон для привлечения клиентов
              </p>
              <Button onClick={() => setShowCreateForm(true)}>
                Создать купон
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

