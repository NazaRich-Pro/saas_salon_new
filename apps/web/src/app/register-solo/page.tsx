'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function RegisterSoloPage() {
  const [formData, setFormData] = useState({
    master_name: '',
    email: '',
    phone: '',
    specialty: '',
    password: '',
    confirm_password: '',
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
      const response = await fetch('/api/register-solo/register-solo/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          master_name: formData.master_name,
          email: formData.email,
          phone: formData.phone,
          specialty: formData.specialty,
          password: formData.password,
          confirm_password: formData.confirm_password
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
          <CardTitle className="text-3xl">Я мастер</CardTitle>
          <CardDescription>
            Создайте свой профиль и начните принимать записи онлайн
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
              <Label htmlFor="master_name">Ваше имя *</Label>
              <Input
                id="master_name"
                name="master_name"
                value={formData.master_name}
                onChange={handleChange}
                placeholder="Алия Нурбекова"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="specialty">Специализация</Label>
              <Input
                id="specialty"
                name="specialty"
                value={formData.specialty}
                onChange={handleChange}
                placeholder="Мастер маникюра"
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
                placeholder="aliya@example.com"
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
            
            <div className="bg-accent/50 p-4 rounded-lg text-sm">
              <strong>500 сом/месяц</strong>
              <p className="text-muted-foreground mt-1">
                14 дней бесплатно. Отменить можно в любой момент.
              </p>
            </div>
          </CardContent>
          
          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              disabled={loading}
              className="w-full"
              size="lg"
            >
              {loading ? 'Создание...' : 'Начать работу'}
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

