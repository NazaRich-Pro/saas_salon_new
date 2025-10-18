import Link from 'next/link';
import { headers } from 'next/headers';

export default async function Home() {
  const headersList = headers();
  const host = headersList.get('host') || 'saas.akylman.online';
  const subdomain = host.split('.')[0];
  
  // Check if this is a tenant subdomain
  const isTenantSite = subdomain !== 'beautyhub' && subdomain !== 'www';
  
  if (isTenantSite) {
    // Tenant landing page
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gradient-to-b from-background to-accent/20">
        <div className="z-10 max-w-3xl w-full text-center space-y-8">
          <h1 className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
            Онлайн запись
          </h1>
          <p className="text-xl text-muted-foreground">
            Запишитесь на услугу прямо сейчас
          </p>
          
          <div className="flex gap-4 justify-center">
            <Link href="/book">
              <button className="bg-primary text-primary-foreground px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary/90 transition-colors">
                Записаться онлайн
              </button>
            </Link>
            
            <Link href="/services">
              <button className="border border-primary text-primary px-8 py-4 rounded-lg text-lg font-semibold hover:bg-accent transition-colors">
                Наши услуги
              </button>
            </Link>
          </div>
          
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            <div className="p-6 bg-card rounded-lg border">
              <div className="text-4xl mb-2">⏰</div>
              <h3 className="font-semibold mb-2">Быстро и удобно</h3>
              <p className="text-sm text-muted-foreground">
                Запишитесь онлайн за 2 минуты без звонков
              </p>
            </div>
            
            <div className="p-6 bg-card rounded-lg border">
              <div className="text-4xl mb-2">👨‍🎨</div>
              <h3 className="font-semibold mb-2">Выбор мастера</h3>
              <p className="text-sm text-muted-foreground">
                Выберите удобное время и любимого мастера
              </p>
            </div>
            
            <div className="p-6 bg-card rounded-lg border">
              <div className="text-4xl mb-2">🔔</div>
              <h3 className="font-semibold mb-2">Напоминания</h3>
              <p className="text-sm text-muted-foreground">
                Получайте напоминания о записи
              </p>
            </div>
          </div>
        </div>
      </main>
    );
  }
  
  // Main platform landing page
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-primary/5 via-background to-secondary/5">
      <div className="z-10 max-w-5xl w-full text-center space-y-8">
        <h1 className="text-6xl font-bold mb-4">
          BeautyHub SaaS
        </h1>
        <p className="text-2xl text-muted-foreground mb-8">
          Система онлайн-записи для салонов красоты и мастеров
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link href="/register-salon">
            <button className="bg-primary text-primary-foreground px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary/90 transition-colors">
              Создать салон
            </button>
          </Link>
          
          <Link href="/register-solo">
            <button className="border border-primary text-primary px-8 py-4 rounded-lg text-lg font-semibold hover:bg-accent transition-colors">
              Я мастер
            </button>
          </Link>
        </div>
        
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-8 bg-card rounded-xl border">
            <div className="text-5xl mb-4">📅</div>
            <h3 className="text-xl font-semibold mb-2">Онлайн запись</h3>
            <p className="text-muted-foreground">
              Клиенты записываются сами 24/7 через виджет или мобильное приложение
            </p>
          </div>
          
          <div className="p-8 bg-card rounded-xl border">
            <div className="text-5xl mb-4">💰</div>
            <h3 className="text-xl font-semibold mb-2">500 сом/месяц</h3>
            <p className="text-muted-foreground">
              Простое ценообразование. Для салонов — 500 сом за каждого мастера
            </p>
          </div>
          
          <div className="p-8 bg-card rounded-xl border">
            <div className="text-5xl mb-4">🚀</div>
            <h3 className="text-xl font-semibold mb-2">14 дней бесплатно</h3>
            <p className="text-muted-foreground">
              Начните работу бесплатно. Без привязки карты. Отменить можно в любой момент
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
