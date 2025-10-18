// Type definitions for BeautyHub API
// These will be expanded as we implement the backend

export interface User {
  id: string;
  email: string;
  phone?: string;
  is_superadmin: boolean;
}

export interface Tenant {
  id: string;
  slug: string;
  name: string;
  type: 'SALON' | 'SOLO';
  plan: string;
  status: string;
}

export interface Appointment {
  id: string;
  tenant_id: string;
  customer_name: string;
  staff_name: string;
  start_at: string;
  end_at: string;
  status: string;
  total_price_kgs: number;
}

export interface Service {
  id: string;
  tenant_id: string;
  name: string;
  duration_min: number;
  price_kgs: number;
}

export interface ApiError {
  message: string;
  status_code: number;
  details?: any;
}


