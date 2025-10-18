/**
 * Main dashboard page
 * Will be expanded in Stage 11
 */
import Link from 'next/link';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-accent/20 p-8">
      <div className="container mx-auto max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Панель управления</h1>
          <p className="text-muted-foreground">Управление салоном и записями</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link href="/dashboard/appointments">
            <div className="p-6 bg-card rounded-lg border hover:border-primary transition-colors cursor-pointer">
              <div className="text-4xl mb-3">📅</div>
              <h3 className="text-xl font-semibold mb-2">Записи</h3>
              <p className="text-sm text-muted-foreground">
                Просмотр и управление записями клиентов
              </p>
            </div>
          </Link>
          
          <Link href="/dashboard/services">
            <div className="p-6 bg-card rounded-lg border hover:border-primary transition-colors cursor-pointer">
              <div className="text-4xl mb-3">💇</div>
              <h3 className="text-xl font-semibold mb-2">Услуги</h3>
              <p className="text-sm text-muted-foreground">
                Управление услугами и ценами
              </p>
            </div>
          </Link>
          
          <Link href="/dashboard/staff">
            <div className="p-6 bg-card rounded-lg border hover:border-primary transition-colors cursor-pointer">
              <div className="text-4xl mb-3">👥</div>
              <h3 className="text-xl font-semibold mb-2">Мастера</h3>
              <p className="text-sm text-muted-foreground">
                Управление мастерами и расписанием
              </p>
            </div>
          </Link>
          
          <Link href="/dashboard/customers">
            <div className="p-6 bg-card rounded-lg border hover:border-primary transition-colors cursor-pointer">
              <div className="text-4xl mb-3">👤</div>
              <h3 className="text-xl font-semibold mb-2">Клиенты</h3>
              <p className="text-sm text-muted-foreground">
                База клиентов и история посещений
              </p>
            </div>
          </Link>
          
          <Link href="/dashboard/reports">
            <div className="p-6 bg-card rounded-lg border hover:border-primary transition-colors cursor-pointer">
              <div className="text-4xl mb-3">📊</div>
              <h3 className="text-xl font-semibold mb-2">Отчеты</h3>
              <p className="text-sm text-muted-foreground">
                Аналитика и финансовые отчеты
              </p>
            </div>
          </Link>
          
          <Link href="/dashboard/settings">
            <div className="p-6 bg-card rounded-lg border hover:border-primary transition-colors cursor-pointer">
              <div className="text-4xl mb-3">⚙️</div>
              <h3 className="text-xl font-semibold mb-2">Настройки</h3>
              <p className="text-sm text-muted-foreground">
                Настройки салона и виджета
              </p>
            </div>
          </Link>
        </div>
        
        <div className="mt-12 p-6 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
          <h3 className="font-semibold mb-2 flex items-center gap-2">
            <span className="text-blue-600">ℹ️</span>
            Пробный период
          </h3>
          <p className="text-sm text-muted-foreground">
            У вас осталось <strong>14 дней</strong> бесплатного использования. 
            После окончания пробного периода стоимость составит 500 сом/месяц за каждого активного мастера.
          </p>
        </div>
      </div>
    </div>
  );
}

