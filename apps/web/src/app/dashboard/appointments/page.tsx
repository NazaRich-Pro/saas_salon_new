'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

// Mock appointment data
const mockAppointments = [
  {
    id: '1',
    customer_name: 'Айгуль Асанова',
    customer_phone: '+996700111111',
    staff_name: 'Анна Иванова',
    start_at: '2025-10-15T10:00:00Z',
    status: 'CONFIRMED',
    total_price_kgs: '800.00',
    prepaid_kgs: '0.00',
    services: ['Женская стрижка']
  },
  {
    id: '2',
    customer_name: 'Бакыт Токтомов',
    customer_phone: '+996700222222',
    staff_name: 'Елена Петрова',
    start_at: '2025-10-15T14:00:00Z',
    status: 'PENDING',
    total_price_kgs: '2500.00',
    prepaid_kgs: '0.00',
    services: ['Окрашивание волос']
  },
];

export default function AppointmentsPage() {
  const [selectedAppointment, setSelectedAppointment] = useState<any>(null);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentNotes, setPaymentNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  
  const handleMarkAsPaid = async () => {
    if (!selectedAppointment) return;
    
    setLoading(true);
    setMessage(null);
    
    try {
      const response = await fetch('/api/payments/mark-cash-paid/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          appointment_id: selectedAppointment.id,
          amount_kgs: paymentAmount || selectedAppointment.total_price_kgs,
          notes: paymentNotes
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to mark as paid');
      }
      
      const data = await response.json();
      
      setMessage({
        type: 'success',
        text: 'Оплата успешно зарегистрирована!'
      });
      
      // Reset form
      setSelectedAppointment(null);
      setPaymentAmount('');
      setPaymentNotes('');
      
      // Reload appointments (in production)
      // refreshAppointments();
      
    } catch (err) {
      setMessage({
        type: 'error',
        text: 'Ошибка при регистрации оплаты'
      });
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-8">
      <div className="container mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Записи клиентов</h1>
          <p className="text-muted-foreground">Управление записями и оплатами</p>
        </div>
        
        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' 
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            {message.text}
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Appointments List */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Предстоящие записи</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockAppointments.map((apt) => (
                    <div
                      key={apt.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedAppointment?.id === apt.id
                          ? 'border-primary bg-accent'
                          : 'hover:bg-accent'
                      }`}
                      onClick={() => setSelectedAppointment(apt)}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-semibold">{apt.customer_name}</div>
                          <div className="text-sm text-muted-foreground">{apt.customer_phone}</div>
                          <div className="text-sm mt-1">
                            Мастер: {apt.staff_name}
                          </div>
                          <div className="text-sm">
                            {new Date(apt.start_at).toLocaleString('ru-RU')}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {apt.services.join(', ')}
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className="text-lg font-semibold">
                            {apt.total_price_kgs} сом
                          </div>
                          <div className={`text-xs px-2 py-1 rounded mt-1 ${
                            apt.status === 'CONFIRMED'
                              ? 'bg-blue-100 text-blue-800'
                              : apt.status === 'PENDING'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {apt.status === 'CONFIRMED' ? 'Подтверждена' :
                             apt.status === 'PENDING' ? 'Ожидает' : apt.status}
                          </div>
                          {parseFloat(apt.prepaid_kgs) > 0 && (
                            <div className="text-xs text-green-600 mt-1">
                              Оплачено: {apt.prepaid_kgs} сом
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* Payment Panel */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>💰 Оплата</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedAppointment ? (
                  <div className="space-y-4">
                    <div className="bg-accent/50 p-3 rounded">
                      <div className="font-medium">{selectedAppointment.customer_name}</div>
                      <div className="text-sm text-muted-foreground">
                        {selectedAppointment.services.join(', ')}
                      </div>
                      <div className="text-lg font-semibold mt-2">
                        Итого: {selectedAppointment.total_price_kgs} сом
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="amount">Сумма оплаты</Label>
                      <Input
                        id="amount"
                        type="number"
                        step="0.01"
                        value={paymentAmount}
                        onChange={(e) => setPaymentAmount(e.target.value)}
                        placeholder={selectedAppointment.total_price_kgs}
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Оставьте пустым для полной суммы
                      </p>
                    </div>
                    
                    <div>
                      <Label htmlFor="notes">Примечание</Label>
                      <Input
                        id="notes"
                        value={paymentNotes}
                        onChange={(e) => setPaymentNotes(e.target.value)}
                        placeholder="Например: оплата при визите"
                      />
                    </div>
                    
                    <Button
                      onClick={handleMarkAsPaid}
                      disabled={loading}
                      className="w-full"
                      size="lg"
                    >
                      {loading ? 'Обработка...' : '✓ Оплачено наличными'}
                    </Button>
                    
                    <Button
                      variant="outline"
                      onClick={() => setSelectedAppointment(null)}
                      className="w-full"
                    >
                      Отмена
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Выберите запись для регистрации оплаты
                  </div>
                )}
              </CardContent>
            </Card>
            
            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-sm">💳 Онлайн оплата</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground mb-3">
                  Stripe интеграция будет доступна в следующей версии
                </p>
                <Button variant="outline" disabled className="w-full">
                  Настроить Stripe
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

