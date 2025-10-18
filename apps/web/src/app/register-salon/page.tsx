'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function RegisterSalonPage() {
  const [formData, setFormData] = useState({
    salon_name: '',
    owner_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    seats: 1,
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirm_password) {
      setError('Пароли не совпадают');
      return;
    }
    
    if (formData.password.length < 8) {
      setError('Пароль должен содержать минимум 8 символов');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/register-salon/register-salon/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          salon_name: formData.salon_name,
          owner_name: formData.owner_name,
          email: formData.email,
          phone: formData.phone,
          password: formData.password,
          confirm_password: formData.confirm_password,
          seats: parseInt(formData.seats.toString())
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }
      
      // Redirect to tenant URL with auto-login token
      window.location.href = data.tenant_url;
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка при регистрации. Попробуйте еще раз.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-accent/20 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl">Создать салон</CardTitle>
          <CardDescription>
            Начните использовать BeautyHub бесплатно в течение 14 дней
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
                {error}
              </div>
            )}
            
            <div>
              <Label htmlFor="salon_name">Название салона *</Label>
              <Input
                id="salon_name"
                name="salon_name"
                value={formData.salon_name}
                onChange={handleChange}
                placeholder="Мой салон красоты"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="owner_name">Ваше имя *</Label>
              <Input
                id="owner_name"
                name="owner_name"
                value={formData.owner_name}
                onChange={handleChange}
                placeholder="Анна Иванова"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="anna@example.com"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="phone">Телефон *</Label>
              <Input
                id="phone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+996 700 123 456"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="seats">Количество мастеров</Label>
              <Input
                id="seats"
                name="seats"
                type="number"
                min="1"
                max="50"
                value={formData.seats}
                onChange={handleChange}
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                500 сом/месяц за каждого мастера
              </p>
            </div>
            
            <div>
              <Label htmlFor="password">Пароль *</Label>
              <Input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Минимум 8 символов"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="confirm_password">Подтвердите пароль *</Label>
              <Input
                id="confirm_password"
                name="confirm_password"
                type="password"
                value={formData.confirm_password}
                onChange={handleChange}
                required
              />
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              disabled={loading}
              className="w-full"
              size="lg"
            >
              {loading ? 'Создание...' : 'Создать салон'}
            </Button>
            
            <p className="text-xs text-center text-muted-foreground">
              Нажимая кнопку, вы соглашаетесь с условиями использования
            </p>
          </CardFooter>
        </form>
      </Card>
    </main>
  );
}

