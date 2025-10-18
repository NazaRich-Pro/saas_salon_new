'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';

interface Appointment {
  id: string;
  customer_name: string;
  total_price_kgs: string;
  services: string[];
}

interface MarkAsPaidDialogProps {
  appointment: Appointment;
  onClose: () => void;
  onSuccess: () => void;
}

export function MarkAsPaidDialog({ appointment, onClose, onSuccess }: MarkAsPaidDialogProps) {
  const [amount, setAmount] = useState(appointment.total_price_kgs);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/payments/mark-cash-paid/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          appointment_id: appointment.id,
          amount_kgs: amount,
          notes: notes
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to mark as paid');
      }
      
      // Success
      onSuccess();
      onClose();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при регистрации оплаты');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>💵 Оплачено наличными</CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}
          
          <div className="bg-accent/50 p-3 rounded">
            <div className="font-medium">{appointment.customer_name}</div>
            <div className="text-sm text-muted-foreground mt-1">
              {appointment.services.join(', ')}
            </div>
            <div className="text-lg font-semibold mt-2">
              К оплате: {appointment.total_price_kgs} сом
            </div>
          </div>
          
          <div>
            <Label htmlFor="amount">Сумма оплаты</Label>
            <Input
              id="amount"
              type="number"
              step="0.01"
              min="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder={appointment.total_price_kgs}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Измените, если клиент оплатил частично
            </p>
          </div>
          
          <div>
            <Label htmlFor="notes">Примечание (необязательно)</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Например: оплата наличными при визите"
              rows={2}
            />
          </div>
        </CardContent>
        
        <CardFooter className="flex gap-2">
          <Button
            onClick={handleSubmit}
            disabled={loading}
            className="flex-1"
          >
            {loading ? 'Сохранение...' : '✓ Подтвердить оплату'}
          </Button>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            Отмена
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

