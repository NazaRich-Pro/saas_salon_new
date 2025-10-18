'use client';

import { useState, ReactNode } from 'react';
import Link from 'link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';

interface NavItem {
  href: string;
  label: string;
  icon: string;
  roles?: string[];
}

const navItems: NavItem[] = [
  { href: '/dashboard', label: 'Главная', icon: '🏠' },
  { href: '/dashboard/appointments', label: 'Записи', icon: '📅' },
  { href: '/dashboard/customers', label: 'Клиенты', icon: '👥', roles: ['SALON_ADMIN', 'RECEPTION'] },
  { href: '/dashboard/services', label: 'Услуги', icon: '💇', roles: ['SALON_ADMIN'] },
  { href: '/dashboard/staff', label: 'Мастера', icon: '👨‍🎨', roles: ['SALON_ADMIN'] },
  { href: '/dashboard/coupons', label: 'Купоны', icon: '🎟️', roles: ['SALON_ADMIN'] },
  { href: '/dashboard/loyalty', label: 'Лояльность', icon: '⭐', roles: ['SALON_ADMIN'] },
  { href: '/dashboard/birthdays', label: 'Дни рождения', icon: '🎂', roles: ['SALON_ADMIN'] },
  { href: '/dashboard/payments', label: 'Оплаты', icon: '💰', roles: ['SALON_ADMIN', 'RECEPTION'] },
  { href: '/dashboard/billing', label: 'Подписка', icon: '💳', roles: ['SALON_ADMIN'] },
  { href: '/dashboard/settings', label: 'Настройки', icon: '⚙️', roles: ['SALON_ADMIN'] },
];

interface DashboardLayoutProps {
  children: ReactNode;
  userRole?: string;
}

export function DashboardLayout({ children, userRole = 'SALON_ADMIN' }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const pathname = usePathname();
  
  // Filter nav items by role
  const filteredNavItems = navItems.filter(item => 
    !item.roles || item.roles.includes(userRole)
  );
  
  return (
    <div className="min-h-screen bg-background">
      {/* Mobile header */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b bg-card">
        <h1 className="text-xl font-bold">BeautyHub</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? '✕' : '☰'}
        </Button>
      </div>
      
      <div className="flex">
        {/* Sidebar */}
        <aside className={`
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
          fixed lg:static
          inset-y-0 left-0
          z-50
          w-64
          bg-card border-r
          transition-transform duration-200
          overflow-y-auto
        `}>
          <div className="p-6">
            <h1 className="text-2xl font-bold mb-6 hidden lg:block">BeautyHub</h1>
            
            <nav className="space-y-2">
              {filteredNavItems.map((item) => {
                const isActive = pathname === item.href;
                
                return (
                  <Link key={item.href} href={item.href}>
                    <a className={`
                      flex items-center gap-3 px-4 py-3 rounded-lg
                      transition-colors
                      ${isActive 
                        ? 'bg-primary text-primary-foreground' 
                        : 'hover:bg-accent'
                      }
                    `}>
                      <span className="text-xl">{item.icon}</span>
                      <span className="font-medium">{item.label}</span>
                    </a>
                  </Link>
                );
              })}
            </nav>
          </div>
          
          {/* User menu */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t bg-card">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                A
              </div>
              <div>
                <div className="font-medium text-sm">Admin</div>
                <div className="text-xs text-muted-foreground">admin@demo.com</div>
              </div>
            </div>
            <Button variant="outline" className="w-full" size="sm">
              Выход
            </Button>
          </div>
        </aside>
        
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div 
            className="lg:hidden fixed inset-0 bg-black/50 z-40"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        
        {/* Main content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

