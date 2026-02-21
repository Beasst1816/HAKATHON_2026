from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone


class User(AbstractUser):
    """Custom User model with role-based access control"""
    class Role(models.TextChoices):
        FLEET_MANAGER = 'FLEET_MANAGER', 'Fleet Manager'
        DISPATCHER = 'DISPATCHER', 'Dispatcher'
        SAFETY_OFFICER = 'SAFETY_OFFICER', 'Safety Officer'
        FINANCIAL_ANALYST = 'FINANCIAL_ANALYST', 'Financial Analyst'

    role = models.CharField(max_length=32, choices=Role.choices, default=Role.FLEET_MANAGER)

    def __str__(self):
        return self.get_full_name() or self.username


class Vehicle(models.Model):
    """Vehicle/Fleet asset model"""
    class Type(models.TextChoices):
        TRUCK = 'TRUCK', 'Truck'
        VAN = 'VAN', 'Van'
        BIKE = 'BIKE', 'Bike'

    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        ON_TRIP = 'ON_TRIP', 'On Trip'
        IN_SHOP = 'IN_SHOP', 'In Shop'
        OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'

    name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    license_plate = models.CharField(max_length=32, unique=True)
    vehicle_type = models.CharField(max_length=16, choices=Type.choices)
    max_load_capacity = models.FloatField(validators=[MinValueValidator(0)])
    odometer = models.FloatField(default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.AVAILABLE)
    is_out_of_service = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.license_plate})"


class Driver(models.Model):
    """Driver profile with safety and compliance tracking"""
    class Status(models.TextChoices):
        ON_DUTY = 'ON_DUTY', 'On Duty'
        OFF_DUTY = 'OFF_DUTY', 'Off Duty'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32)
    license_number = models.CharField(max_length=64, unique=True)
    license_category = models.CharField(max_length=32)
    license_expiry = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OFF_DUTY)
    safety_score = models.FloatField(default=100)
    trip_completion_rate = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_license_expired(self):
        return self.license_expiry < timezone.now().date()


class Trip(models.Model):
    """Trip lifecycle management"""
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        DISPATCHED = 'DISPATCHED', 'Dispatched'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='trips')
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='trips')
    cargo_weight = models.FloatField(validators=[MinValueValidator(0)])
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    start_odometer = models.FloatField(null=True, blank=True)
    end_odometer = models.FloatField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.origin} → {self.destination}"


class Expense(models.Model):
    """Financial tracking - fuel, maintenance, repairs"""
    class Type(models.TextChoices):
        FUEL = 'FUEL', 'Fuel'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'
        REPAIR = 'REPAIR', 'Repair'
        OTHER = 'OTHER', 'Other'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='expenses')
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    expense_type = models.CharField(max_length=32, choices=Type.choices)
    amount = models.FloatField(validators=[MinValueValidator(0)])
    liters = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    date = models.DateTimeField()
    description = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.vehicle} - {self.expense_type} - {self.amount}"


class MaintenanceLog(models.Model):
    """Vehicle maintenance and service logs"""
    class ServiceType(models.TextChoices):
        PREVENTATIVE = 'PREVENTATIVE', 'Preventative'
        REACTIVE = 'REACTIVE', 'Reactive'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_logs')
    service_type = models.CharField(max_length=32, choices=ServiceType.choices)
    description = models.CharField(max_length=512)
    cost = models.FloatField(validators=[MinValueValidator(0)])
    date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.vehicle} - {self.description}"
