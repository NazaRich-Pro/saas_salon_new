import axios, { AxiosInstance } from 'axios';

export class BeautyHubClient {
  private api: AxiosInstance;

  constructor(baseURL?: string) {
    this.api = axios.create({
      baseURL: baseURL || '/api',
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Auth methods
  async login(email: string, password: string) {
    return this.api.post('/auth/login', { email, password });
  }

  async logout(allDevices = false) {
    return this.api.post('/auth/logout', { all_devices: allDevices });
  }

  async refresh(refreshToken: string) {
    return this.api.post('/auth/refresh', { refresh_token: refreshToken });
  }

  async getProfile() {
    return this.api.get('/auth/profile');
  }

  // Booking methods
  async getServices(filters?: { category?: string }) {
    return this.api.get('/booking/services/', { params: filters });
  }

  async getStaff() {
    return this.api.get('/booking/staff/');
  }

  async getAvailableSlots(params: { 
    service_id: string; 
    date: string; 
    staff_id?: string; 
  }) {
    return this.api.get('/booking/available-slots/', { params });
  }

  async createAppointment(data: {
    customer_name: string;
    customer_phone: string;
    customer_email?: string;
    staff_id: string;
    service_ids: string[];
    start_at: string;
    location_id?: string;
    notes?: string;
    source?: string;
  }) {
    return this.api.post('/booking/create-appointment/', data);
  }

  async getAppointments(filters?: {
    status?: string;
    staff?: string;
    date_from?: string;
    date_to?: string;
  }) {
    return this.api.get('/booking/appointments/', { params: filters });
  }

  async confirmAppointment(id: string) {
    return this.api.patch(`/booking/appointments/${id}/confirm/`);
  }

  async cancelAppointment(id: string, reason?: string) {
    return this.api.patch(`/booking/appointments/${id}/cancel/`, { reason });
  }

  async rescheduleAppointment(id: string, new_start_at: string, new_staff_id?: string) {
    return this.api.patch(`/booking/appointments/${id}/reschedule/`, { 
      new_start_at, 
      new_staff_id 
    });
  }

  async completeAppointment(id: string) {
    return this.api.patch(`/booking/appointments/${id}/complete/`);
  }

  async markNoShow(id: string) {
    return this.api.patch(`/booking/appointments/${id}/no-show/`);
  }

  async downloadICS(id: string) {
    return this.api.get(`/booking/appointments/${id}/ics/`, {
      responseType: 'blob'
    });
  }

  // Customer methods
  async searchCustomers(search: string) {
    return this.api.get('/booking/customers/', { params: { search } });
  }

  async getCustomer(id: string) {
    return this.api.get(`/booking/customers/${id}/`);
  }

  // Payment methods (will be expanded in Stage 6)
  async markCashPaid(appointmentId: string, amount: number) {
    return this.api.post('/payments/mark-cash-paid/', {
      appointment_id: appointmentId,
      amount_kgs: amount
    });
  }
}


