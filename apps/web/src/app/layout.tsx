import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { headers } from "next/headers";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export async function generateMetadata(): Promise<Metadata> {
  const headersList = headers();
  const host = headersList.get('host') || 'saas.akylman.online';
  const subdomain = host.split('.')[0];
  
  const isTenant = subdomain !== 'beautyhub' && subdomain !== 'www';
  
  if (isTenant) {
    return {
      title: `Онлайн запись - ${subdomain}`,
      description: "Запишитесь на услугу онлайн быстро и удобно",
    };
  }
  
  return {
    title: "BeautyHub - Система онлайн-записи для салонов красоты",
    description: "Профессиональная система бронирования для салонов красоты и мастеров. 14 дней бесплатно.",
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const messages = await getMessages();
  
  return (
    <html lang="ru">
      <body className={inter.className}>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
