/**
 * Payments history page
 * Shows all payments for the tenant
 */
'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Mock payment data
const mockPayments = [
  {
    id: '1',
    appointment_id: '1',
    customer_name: 'Айгуль Асанова',
    type: 'CASH',
    provider: 'MANUAL_CASH',
    status: 'SUCCEEDED',
    amount_kgs: '800.00',
    processed_by: 'Администратор',
    created_at: '2025-10-10T14:30:00Z'
  },
  {
    id: '2',
    appointment_id: '2',
    customer_name: 'Бакыт Токтомов',
    type: 'CASH',
    provider: 'MANUAL_CASH',
    status: 'SUCCEEDED',
    amount_kgs: '2500.00',
    processed_by: 'Ресепшн',
    created_at: '2025-10-09T11:15:00Z'
  },
];

export default function PaymentsPage() {
  const [filter, setFilter] = useState<'all' | 'cash' | 'card'>('all');
  
  const filteredPayments = mockPayments.filter(p => {
    if (filter === 'all') return true;
    if (filter === 'cash') return p.type === 'CASH';
    if (filter === 'card') return p.type === 'CARD';
    return true;
  });
  
  const totalAmount = filteredPayments.reduce(
    (sum, p) => sum + parseFloat(p.amount_kgs), 
    0
  );
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-8">
      <div className="container mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">История оплат</h1>
          <p className="text-muted-foreground">Все платежи за услуги</p>
        </div>
        
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Всего оплат</div>
              <div className="text-2xl font-bold">{filteredPayments.length}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Общая сумма</div>
              <div className="text-2xl font-bold">{totalAmount.toFixed(2)} сом</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-muted-foreground mb-1">Наличные</div>
              <div className="text-2xl font-bold">
                {mockPayments.filter(p => p.type === 'CASH').length}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Filters */}
        <div className="flex gap-2 mb-6">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            onClick={() => setFilter('all')}
          >
            Все
          </Button>
          <Button
            variant={filter === 'cash' ? 'default' : 'outline'}
            onClick={() => setFilter('cash')}
          >
            Наличные
          </Button>
          <Button
            variant={filter === 'card' ? 'default' : 'outline'}
            onClick={() => setFilter('card')}
          >
            Картой
          </Button>
        </div>
        
        {/* Payments List */}
        <Card>
          <CardHeader>
            <CardTitle>Список оплат</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredPayments.map((payment) => (
                <div
                  key={payment.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div>
                    <div className="font-semibold">{payment.customer_name}</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(payment.created_at).toLocaleString('ru-RU')}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {payment.type === 'CASH' ? '💵 Наличные' : '💳 Карта'} • 
                      Обработал: {payment.processed_by}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-xl font-semibold">
                      {payment.amount_kgs} сом
                    </div>
                    <div className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded mt-1">
                      {payment.status === 'SUCCEEDED' ? 'Успешно' : payment.status}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        
        <div className="mt-6">
          <Button variant="outline">
            📥 Экспорт в CSV
          </Button>
        </div>
      </div>
    </div>
  );
}

