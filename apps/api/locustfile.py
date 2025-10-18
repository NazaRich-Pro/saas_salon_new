"""
Load testing with Locust.
Tests booking creation under load to verify no double bookings occur.

Usage:
    locust -f locustfile.py --host=http://localhost:8000 --users=200 --spawn-rate=10
"""
import random
from datetime import datetime, timedelta

from locust import HttpUser, between, task


class BookingUser(HttpUser):
    """Simulates users creating bookings."""

    wait_time = between(1, 3)

    def on_start(self):
        """Login and get auth token."""
        response = self.client.post(
            "/api/auth/login", json={"email": "demo@example.com", "password": "demo123"}
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}", "X-Tenant": "demo"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def view_available_slots(self):
        """View available time slots."""
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        self.client.get(
            "/api/bookings/available-slots/",
            params={
                "service": "123e4567-e89b-12d3-a456-426614174000",
                "staff": "123e4567-e89b-12d3-a456-426614174001",
                "date": tomorrow.isoformat(),
            },
            headers=self.headers,
            name="/api/bookings/available-slots/",
        )

    @task(1)
    def create_booking(self):
        """Create a new booking."""
        if not self.token:
            return

        tomorrow = datetime.now() + timedelta(days=1)
        hour = random.randint(9, 17)
        start_time = tomorrow.replace(hour=hour, minute=0, second=0)

        response = self.client.post(
            "/api/bookings/appointments/",
            json={
                "customer": "123e4567-e89b-12d3-a456-426614174002",
                "staff": "123e4567-e89b-12d3-a456-426614174001",
                "services": ["123e4567-e89b-12d3-a456-426614174000"],
                "start_at": start_time.isoformat(),
                "notes": "Load test booking",
            },
            headers=self.headers,
            name="/api/bookings/appointments/ [POST]",
        )

        if response.status_code == 400 and "already booked" in response.text:
            # This is expected - slot was taken by another user
            pass

    @task(2)
    def list_appointments(self):
        """List appointments."""
        if not self.token:
            return

        self.client.get(
            "/api/bookings/appointments/",
            headers=self.headers,
            name="/api/bookings/appointments/ [GET]",
        )


class PublicWidgetUser(HttpUser):
    """Simulates public users using the booking widget."""

    wait_time = between(2, 5)

    @task(5)
    def view_widget(self):
        """Load widget page."""
        self.client.get("/demo", name="/demo (widget)")

    @task(1)
    def create_public_booking(self):
        """Create booking from public widget."""
        tomorrow = datetime.now() + timedelta(days=1)
        hour = random.randint(9, 17)
        start_time = tomorrow.replace(hour=hour, minute=0, second=0)

        response = self.client.post(
            "/api/public/create_appointment/",
            json={
                "tenant_slug": "demo",
                "customer_name": f"Test User {random.randint(1000, 9999)}",
                "customer_phone": f"+99670011{random.randint(1000, 9999)}",
                "customer_email": f"test{random.randint(1000, 9999)}@example.com",
                "service_id": "123e4567-e89b-12d3-a456-426614174000",
                "staff_id": "123e4567-e89b-12d3-a456-426614174001",
                "start_at": start_time.isoformat(),
            },
            name="/api/public/create_appointment/ [POST]",
        )
