import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { BookingWidget } from '@/components/BookingWidget';
import { headers } from 'next/headers';

export default async function BookPage() {
  const messages = await getMessages();
  const headersList = headers();
  const host = headersList.get('host') || 'saas.akylman.online';
  const subdomain = host.split('.')[0];
  
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-accent/20 py-12 px-4">
      <div className="container mx-auto">
        <NextIntlClientProvider messages={messages}>
          <BookingWidget tenantSlug={subdomain} />
        </NextIntlClientProvider>
      </div>
    </main>
  );
}

