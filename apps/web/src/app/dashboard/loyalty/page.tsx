'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function LoyaltyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-8">
      <div className="container mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Программа лояльности</h1>
          <p className="text-muted-foreground">Настройка системы баллов</p>
        </div>
        
        {/* Settings Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Настройки программы</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="earn_rate">Начисление баллов</Label>
                <Input
                  id="earn_rate"
                  type="number"
                  defaultValue="1"
                  min="0"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  баллов за каждые 100 сом
                </p>
              </div>
              
              <div>
                <Label htmlFor="redeem_rate">Обмен баллов</Label>
                <Input
                  id="redeem_rate"
                  type="number"
                  step="0.01"
                  defaultValue="1.00"
                  min="0"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  1 балл = X сом скидки
                </p>
              </div>
              
              <div>
                <Label htmlFor="min_redeem">Минимум для обмена</Label>
                <Input
                  id="min_redeem"
                  type="number"
                  defaultValue="100"
                  min="0"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  минимум баллов
                </p>
              </div>
            </div>
            
            <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg border border-blue-200">
              <h4 className="font-semibold mb-2">Как это работает</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Клиент тратит 500 сом → получает 5 баллов</li>
                <li>• Клиент накопил 100 баллов → может использовать как скидку 100 сом</li>
                <li>• Баллы начисляются при завершении записи</li>
                <li>• Баллы можно использовать при следующей записи</li>
              </ul>
            </div>
            
            <Button>Сохранить настройки</Button>
          </CardContent>
        </Card>
        
        {/* Top Customers */}
        <Card>
          <CardHeader>
            <CardTitle>Топ клиентов по баллам</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { name: 'Айгуль Асанова', phone: '+996700111111', points: 450, value: 450 },
                { name: 'Бакыт Токтомов', phone: '+996700222222', points: 320, value: 320 },
                { name: 'Гульмира Жумабаева', phone: '+996700333333', points: 280, value: 280 },
              ].map((customer, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <div className="font-medium">{customer.name}</div>
                    <div className="text-sm text-muted-foreground">{customer.phone}</div>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-semibold text-lg">{customer.points} баллов</div>
                    <div className="text-sm text-muted-foreground">
                      ≈ {customer.value} сом
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

