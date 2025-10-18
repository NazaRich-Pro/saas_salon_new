import { headers } from 'next/headers';
import Link from 'next/link';

// Mock data - in production would fetch from API
const mockServices = [
  {
    category: 'Стрижки',
    items: [
      { name: 'Женская стрижка', duration: 60, price: 800 },
      { name: 'Мужская стрижка', duration: 30, price: 500 },
      { name: 'Детская стрижка', duration: 30, price: 400 },
    ]
  },
  {
    category: 'Окрашивание',
    items: [
      { name: 'Окрашивание волос', duration: 120, price: 2500 },
      { name: 'Мелирование', duration: 180, price: 3500 },
    ]
  },
  {
    category: 'Маникюр/Педикюр',
    items: [
      { name: 'Маникюр', duration: 60, price: 600 },
      { name: 'Педикюр', duration: 90, price: 800 },
    ]
  }
];

export default async function ServicesPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-accent/20 py-12 px-4">
      <div className="container mx-auto max-w-4xl">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Наши услуги</h1>
          <p className="text-muted-foreground text-lg">
            Широкий спектр услуг от профессиональных мастеров
          </p>
        </div>
        
        <div className="space-y-8">
          {mockServices.map((category, idx) => (
            <div key={idx} className="bg-card rounded-lg border p-6">
              <h2 className="text-2xl font-semibold mb-4">{category.category}</h2>
              
              <div className="space-y-3">
                {category.items.map((service, serviceIdx) => (
                  <div
                    key={serviceIdx}
                    className="flex items-center justify-between p-4 hover:bg-accent rounded-lg transition-colors"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-lg">{service.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {service.duration} минут
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-xl font-semibold">{service.price} сом</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-12 text-center">
          <Link href="/book">
            <button className="bg-primary text-primary-foreground px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary/90 transition-colors">
              Записаться на услугу
            </button>
          </Link>
        </div>
      </div>
    </main>
  );
}

