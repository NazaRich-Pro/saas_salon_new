'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { format } from 'date-fns';
import { ru, ky, enUS } from 'date-fns/locale';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Calendar } from '@/components/ui/calendar';

interface Service {
  id: string;
  name: string;
  duration_min: number;
  price_kgs: number;
  category_name?: string;
}

interface TimeSlot {
  time: string;
  datetime: string;
  staff_id: string;
  staff_name: string;
  duration_min: number;
  available: boolean;
}

interface BookingWidgetProps {
  tenantSlug: string;
  apiUrl?: string;
  locale?: 'ru' | 'kg' | 'en';
}

type BookingStep = 'service' | 'date-time' | 'contact' | 'confirmation';

export function BookingWidget({ tenantSlug, apiUrl = '/api', locale = 'ru' }: BookingWidgetProps) {
  const t = useTranslations('booking');
  const [step, setStep] = useState<BookingStep>('service');
  
  // State
  const [services, setServices] = useState<Service[]>([]);
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null);
  
  // Contact form
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [notes, setNotes] = useState('');
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appointmentId, setAppointmentId] = useState<string | null>(null);
  
  // Fetch services on mount
  useEffect(() => {
    fetchServices();
  }, []);
  
  // Fetch slots when date is selected
  useEffect(() => {
    if (selectedService && selectedDate) {
      fetchAvailableSlots();
    }
  }, [selectedService, selectedDate]);
  
  const fetchServices = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/booking/services/`);
      const data = await response.json();
      setServices(data.results || data);
    } catch (err) {
      setError('Failed to load services');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchAvailableSlots = async () => {
    if (!selectedService || !selectedDate) return;
    
    setLoading(true);
    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      const response = await fetch(
        `${apiUrl}/booking/available-slots/?service_id=${selectedService.id}&date=${dateStr}`
      );
      const data = await response.json();
      setAvailableSlots(data.slots || []);
    } catch (err) {
      setError('Failed to load available slots');
    } finally {
      setLoading(false);
    }
  };
  
  const handleServiceSelect = (service: Service) => {
    setSelectedService(service);
    setStep('date-time');
  };
  
  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date);
    setSelectedSlot(null);
  };
  
  const handleSlotSelect = (slot: TimeSlot) => {
    setSelectedSlot(slot);
    setStep('contact');
  };
  
  const handleSubmit = async () => {
    if (!selectedService || !selectedSlot || !customerName || !customerPhone) {
      setError('Please fill in all required fields');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${apiUrl}/booking/create-appointment/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_name: customerName,
          customer_phone: customerPhone,
          customer_email: customerEmail,
          staff_id: selectedSlot.staff_id,
          service_ids: [selectedService.id],
          start_at: selectedSlot.datetime,
          notes: notes,
          source: 'WIDGET'
        })
      });
      
      if (!response.ok) {
        throw new Error('Booking failed');
      }
      
      const data = await response.json();
      setAppointmentId(data.appointment.id);
      setStep('confirmation');
    } catch (err) {
      setError(t('bookingError'));
    } finally {
      setLoading(false);
    }
  };
  
  const getDateLocale = () => {
    switch (locale) {
      case 'kg': return ky;
      case 'en': return enUS;
      default: return ru;
    }
  };
  
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl">{t('title')}</CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        {/* Step 1: Select Service */}
        {step === 'service' && (
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">{t('selectService')}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {services.map((service) => (
                <button
                  key={service.id}
                  onClick={() => handleServiceSelect(service)}
                  className="p-4 border rounded-lg hover:border-primary hover:bg-accent text-left transition-colors"
                >
                  <div className="font-medium">{service.name}</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {service.duration_min} {t('minutes')} • {service.price_kgs} {t('kgs')}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Step 2: Select Date & Time */}
        {step === 'date-time' && selectedService && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">{t('selectDate')}</h3>
              <Button variant="ghost" size="sm" onClick={() => setStep('service')}>
                {t('back')}
              </Button>
            </div>
            
            <div className="bg-accent/50 p-4 rounded-lg">
              <div className="font-medium">{selectedService.name}</div>
              <div className="text-sm text-muted-foreground">
                {selectedService.duration_min} {t('minutes')} • {selectedService.price_kgs} {t('kgs')}
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={handleDateSelect}
                  disabled={(date) => date < new Date()}
                  locale={getDateLocale()}
                  className="rounded-md border"
                />
              </div>
              
              <div>
                {selectedDate && (
                  <>
                    <h4 className="font-medium mb-3">{t('selectTime')}</h4>
                    {loading ? (
                      <div className="text-center py-8 text-muted-foreground">{t('loading')}</div>
                    ) : availableSlots.length === 0 ? (
                      <div className="text-center py-8 text-muted-foreground">
                        {t('noSlotsAvailable')}
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-2 max-h-96 overflow-y-auto">
                        {availableSlots.map((slot) => (
                          <button
                            key={`${slot.datetime}-${slot.staff_id}`}
                            onClick={() => handleSlotSelect(slot)}
                            className="p-2 border rounded hover:border-primary hover:bg-accent text-sm transition-colors"
                          >
                            {slot.time}
                          </button>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* Step 3: Contact Information */}
        {step === 'contact' && selectedService && selectedSlot && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg">{t('contactInfo')}</h3>
              <Button variant="ghost" size="sm" onClick={() => setStep('date-time')}>
                {t('back')}
              </Button>
            </div>
            
            <div className="bg-accent/50 p-4 rounded-lg space-y-2">
              <div><strong>{selectedService.name}</strong></div>
              <div className="text-sm">
                {selectedDate && format(selectedDate, 'd MMMM yyyy', { locale: getDateLocale() })} в {selectedSlot.time}
              </div>
              <div className="text-sm text-muted-foreground">
                {t('master')}: {selectedSlot.staff_name}
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">{t('yourName')} *</Label>
                <Input
                  id="name"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Иван Иванов"
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="phone">{t('phone')} *</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={customerPhone}
                  onChange={(e) => setCustomerPhone(e.target.value)}
                  placeholder="+996 700 123 456"
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="email">{t('email')}</Label>
                <Input
                  id="email"
                  type="email"
                  value={customerEmail}
                  onChange={(e) => setCustomerEmail(e.target.value)}
                  placeholder="ivan@example.com"
                />
              </div>
              
              <div>
                <Label htmlFor="notes">{t('notes')}</Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Например: хочу модную стрижку"
                  rows={3}
                />
              </div>
            </div>
          </div>
        )}
        
        {/* Step 4: Confirmation */}
        {step === 'confirmation' && appointmentId && (
          <div className="text-center space-y-4 py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            
            <h3 className="text-xl font-semibold text-green-800">{t('bookingSuccess')}</h3>
            
            <div className="bg-accent/50 p-4 rounded-lg text-left max-w-md mx-auto space-y-2">
              <div><strong>{selectedService?.name}</strong></div>
              <div className="text-sm">
                {selectedDate && format(selectedDate, 'd MMMM yyyy в HH:mm', { locale: getDateLocale() })}
              </div>
              <div className="text-sm">
                {t('master')}: {selectedSlot?.staff_name}
              </div>
              <div className="text-sm font-semibold mt-3">
                {t('total')}: {selectedService?.price_kgs} {t('kgs')}
              </div>
            </div>
            
            <div className="space-x-2">
              <Button
                onClick={() => window.location.href = `${apiUrl}/booking/appointments/${appointmentId}/ics/`}
              >
                📅 {t('downloadCalendar')}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
      
      {step === 'contact' && (
        <CardFooter>
          <Button
            onClick={handleSubmit}
            disabled={loading || !customerName || !customerPhone}
            className="w-full"
            size="lg"
          >
            {loading ? t('loading') : t('bookNow')}
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}

