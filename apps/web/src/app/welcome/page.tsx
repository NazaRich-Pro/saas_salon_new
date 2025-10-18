/**
 * Welcome page after tenant registration
 * Shows onboarding steps and auto-login with token
 */
'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function WelcomePage() {
  const searchParams = useSearchParams();
  const token = searchParams?.get('token');
  const [loggingIn, setLoggingIn] = useState(false);
  
  useEffect(() => {
    // Auto-login with token if provided
    if (token) {
      handleAutoLogin(token);
    }
  }, [token]);
  
  const handleAutoLogin = async (token: string) => {
    setLoggingIn(true);
    try {
      const response = await fetch('/api/tenants/auto-login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ token })
      });
      
      if (!response.ok) {
        throw new Error('Auto-login failed');
      }
      
      const data = await response.json();
      
      // Store refresh token if needed
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }
      
      // Token validated, user is logged in
      setLoggingIn(false);
    } catch (err) {
      console.error('Auto-login failed:', err);
      setLoggingIn(false);
    }
  };
  
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-accent/20 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="text-6xl mb-4">🎉</div>
          <CardTitle className="text-3xl">Добро пожаловать в BeautyHub!</CardTitle>
          <CardDescription className="text-lg">
            Ваш салон успешно создан. Начните настройку за 3 простых шага.
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {loggingIn && (
            <div className="text-center py-4">
              <div className="text-muted-foreground">Выполняется вход...</div>
            </div>
          )}
          
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 bg-accent/50 rounded-lg">
              <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold flex-shrink-0">
                1
              </div>
              <div>
                <h3 className="font-semibold mb-1">Добавьте услуги</h3>
                <p className="text-sm text-muted-foreground">
                  Создайте список услуг с ценами и длительностью
                </p>
                <Link href="/dashboard/services">
                  <Button variant="link" className="px-0 h-auto mt-2">
                    Перейти к услугам →
                  </Button>
                </Link>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-4 bg-accent/50 rounded-lg">
              <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold flex-shrink-0">
                2
              </div>
              <div>
                <h3 className="font-semibold mb-1">Добавьте мастеров</h3>
                <p className="text-sm text-muted-foreground">
                  Создайте профили мастеров и настройте их расписание
                </p>
                <Link href="/dashboard/staff">
                  <Button variant="link" className="px-0 h-auto mt-2">
                    Перейти к мастерам →
                  </Button>
                </Link>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-4 bg-accent/50 rounded-lg">
              <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold flex-shrink-0">
                3
              </div>
              <div>
                <h3 className="font-semibold mb-1">Встройте виджет на сайт</h3>
                <p className="text-sm text-muted-foreground">
                  Разместите виджет записи на вашем сайте
                </p>
                <Link href="/dashboard/widget">
                  <Button variant="link" className="px-0 h-auto mt-2">
                    Получить код виджета →
                  </Button>
                </Link>
              </div>
            </div>
          </div>
          
          <div className="border-t pt-6">
            <h3 className="font-semibold mb-3">Информация о пробном периоде</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>14 дней бесплатного использования</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Полный доступ ко всем функциям</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Никаких скрытых платежей</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-green-600">✓</span>
                <span>Отменить можно в любой момент</span>
              </li>
            </ul>
          </div>
          
          <div className="flex gap-4 pt-4">
            <Link href="/dashboard" className="flex-1">
              <Button className="w-full" size="lg">
                Перейти в панель управления
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

