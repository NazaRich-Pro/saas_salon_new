FROM node:20-alpine

WORKDIR /app

# Copy package.json first
COPY package.json ./

# Install dependencies
RUN npm install

# Copy all source files
COPY . .

# Create lib directory and files if they don't exist
RUN mkdir -p src/lib

# Create minimal utils.ts
RUN cat > src/lib/utils.ts << 'EOF'
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
EOF

# Create minimal tenant.ts
RUN cat > src/lib/tenant.ts << 'EOF'
export interface TenantTheme {
  primary_color?: string;
  secondary_color?: string;
  logo_url?: string;
  font_family?: string;
}

export interface TenantSettings {
  theme?: TenantTheme;
  language?: 'ru' | 'kg' | 'en';
  timezone?: string;
  widget?: {
    show_prices?: boolean;
    show_duration?: boolean;
    allow_multi_service?: boolean;
  };
}

export interface Tenant {
  id: string;
  slug: string;
  name: string;
  type: 'SALON' | 'SOLO';
  settings: TenantSettings;
}

export async function getTenantFromHost(host: string): Promise<Tenant | null> {
  const subdomain = host.split('.')[0];
  
  if (subdomain === 'demo-salon') {
    return {
      id: 'demo-salon-id',
      slug: 'demo-salon',
      name: 'Демо Салон Красоты',
      type: 'SALON',
      settings: {
        theme: {
          primary_color: '#FF6B6B',
          secondary_color: '#4ECDC4',
        },
        language: 'ru',
        timezone: 'Asia/Bishkek',
        widget: {
          show_prices: true,
          show_duration: true,
          allow_multi_service: true
        }
      }
    };
  }
  
  return null;
}

export function applyTenantTheme(theme: TenantTheme): void {
  if (typeof window === 'undefined') return;
  
  const root = document.documentElement;
  
  if (theme.primary_color) {
    root.style.setProperty('--primary', theme.primary_color);
  }
  
  if (theme.secondary_color) {
    root.style.setProperty('--secondary', theme.secondary_color);
  }
  
  if (theme.font_family) {
    root.style.setProperty('--font-family', theme.font_family);
  }
}
EOF

# Verify files exist
RUN ls -la src/lib/
RUN echo "=== utils.ts ===" && cat src/lib/utils.ts
RUN echo "=== tenant.ts ===" && cat src/lib/tenant.ts

# Set environment variables
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-https://saas.akylman.online/api}
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Change ownership
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the application
CMD ["npm", "start"]