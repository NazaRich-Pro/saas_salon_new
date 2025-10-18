import { getRequestConfig } from 'next-intl/server';
import { headers } from 'next/headers';

export default getRequestConfig(async () => {
  // Get locale from tenant settings or browser
  // For now, default to 'ru'
  const locale = 'ru';

  return {
    locale,
    messages: (await import(`./messages/${locale}.json`)).default
  };
});

