/**
 * Widget-only page for iframe embedding
 * Minimal layout, just the booking widget
 */
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { BookingWidget } from '@/components/BookingWidget';
import { headers } from 'next/headers';

export default async function WidgetPage() {
  const messages = await getMessages();
  const headersList = headers();
  const host = headersList.get('host') || 'saas.akylman.online';
  const subdomain = host.split('.')[0];
  
  return (
    <div className="p-4">
      <NextIntlClientProvider messages={messages}>
        <BookingWidget tenantSlug={subdomain} />
      </NextIntlClientProvider>
    </div>
  );
}

