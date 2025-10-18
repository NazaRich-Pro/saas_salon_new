# BeautyHub API Documentation

## Base URL

```
https://{tenant-slug}.saas.akylman.online/api
```

## Authentication

All authenticated endpoints require JWT token in httpOnly cookie.

### Auth Endpoints

#### POST /api/auth/register
Register new user (tenant-scoped)

#### POST /api/auth/login
```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

Response:
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  },
  "tenant": {
    "id": "uuid",
    "slug": "demo",
    "name": "Demo Salon"
  }
}
```

#### POST /api/auth/logout
Invalidates current session

#### POST /api/auth/refresh
Rotates refresh token

#### POST /api/auth/2fa/setup
Returns TOTP secret and QR code

#### POST /api/auth/2fa/verify
```json
{
  "code": "123456"
}
```

## Tenant Endpoints

#### POST /api/register-salon
```json
{
  "salon_name": "My Salon",
  "owner_name": "John Doe",
  "email": "owner@example.com",
  "phone": "+996700123456",
  "password": "secure_password",
  "seats": 3
}
```

Response:
```json
{
  "tenant_url": "https://my-salon.saas.akylman.online/welcome?token=...",
  "tenant": {
    "id": "uuid",
    "slug": "my-salon",
    "name": "My Salon"
  }
}
```

#### POST /api/register-solo
Similar to register-salon but for solo masters

## Booking Endpoints

#### GET /api/booking/available-slots
Query params:
- `service`: Service ID
- `staff`: Staff ID (optional)
- `date`: YYYY-MM-DD

Response:
```json
{
  "date": "2025-10-15",
  "slots": [
    {
      "time": "10:00",
      "staff_id": "uuid",
      "staff_name": "Jane Smith"
    }
  ]
}
```

#### POST /api/booking/appointments
```json
{
  "customer_name": "Client Name",
  "customer_phone": "+996700123456",
  "staff_id": "uuid",
  "service_ids": ["uuid1", "uuid2"],
  "start_at": "2025-10-15T10:00:00Z",
  "notes": "Optional notes"
}
```

#### PATCH /api/booking/appointments/{id}/confirm
#### PATCH /api/booking/appointments/{id}/cancel
#### PATCH /api/booking/appointments/{id}/complete
#### PATCH /api/booking/appointments/{id}/no-show

## Payment Endpoints

#### POST /api/payments/mark-cash-paid
```json
{
  "appointment_id": "uuid",
  "amount_kgs": 1500
}
```

#### POST /api/payments/stripe/create-intent
(Stub for future card payments)

## Reports Endpoints

#### GET /api/reports/revenue
Query params:
- `from`: YYYY-MM-DD
- `to`: YYYY-MM-DD
- `group`: staff|service|day

#### GET /api/reports/no-show
Query params:
- `from`: YYYY-MM-DD
- `to`: YYYY-MM-DD

#### GET /api/reports/export.csv
Returns CSV file

## Error Responses

All errors follow this format:
```json
{
  "message": "Error description",
  "status_code": 400,
  "details": {}
}
```

Common status codes:
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden (wrong tenant or role)
- `404`: Not Found
- `429`: Rate Limited
- `500`: Internal Server Error

## Rate Limits

- Auth endpoints: 5 requests/minute
- Public endpoints: 100 requests/minute
- Authenticated endpoints: 1000 requests/minute

## Pagination

List endpoints return:
```json
{
  "count": 100,
  "next": "url",
  "previous": "url",
  "results": []
}
```

Default page size: 50


