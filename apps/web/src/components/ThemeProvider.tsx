'use client';

import { useEffect } from 'react';
import { applyTenantTheme, getTenantFromHost } from '@/lib/tenant';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Get current host
    const host = window.location.host;
    
    // Fetch tenant and apply theme
    getTenantFromHost(host)
      .then(tenant => {
        if (tenant && tenant.settings?.theme) {
          applyTenantTheme(tenant.settings.theme);
        }
      })
      .catch(error => {
        console.warn('Failed to load tenant theme:', error);
      });
  }, []);
  
  return <>{children}</>;
}

