from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Vehicle, Driver, Trip, Expense, MaintenanceLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('FleetFlow Role', {'fields': ('role',)}),
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_plate', 'vehicle_type', 'max_load_capacity', 'odometer', 'status')
    list_filter = ('vehicle_type', 'status')


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'license_number', 'license_expiry', 'status', 'safety_score')


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'vehicle', 'driver', 'status', 'cargo_weight')
    list_filter = ('status',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'expense_type', 'amount', 'liters', 'date')


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service_type', 'description', 'cost', 'date', 'completed_at')
