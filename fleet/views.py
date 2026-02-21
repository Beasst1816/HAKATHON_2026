from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Sum
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import csv
from .models import Vehicle, Driver, Trip, Expense, MaintenanceLog


# ==================== DASHBOARD ====================
@login_required
def dashboard(request):
    """Command Center - Main dashboard with KPIs"""
    vehicles = Vehicle.objects.all()
    trips = Trip.objects.all()
    drivers = Driver.objects.all()
    
    active_fleet = vehicles.filter(status=Vehicle.Status.ON_TRIP).count()
    maintenance_alerts = vehicles.filter(status=Vehicle.Status.IN_SHOP).count()
    total_vehicles = vehicles.count()
    assigned_vehicles = vehicles.filter(status__in=[Vehicle.Status.ON_TRIP, Vehicle.Status.IN_SHOP]).count()
    utilization_rate = (assigned_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0
    pending_cargo = trips.filter(status=Trip.Status.DRAFT).count()
    
    kpis = {
        'active_fleet': active_fleet,
        'maintenance_alerts': maintenance_alerts,
        'utilization_rate': round(utilization_rate, 2),
        'pending_cargo': pending_cargo,
        'total_vehicles': total_vehicles,
        'total_drivers': drivers.count(),
        'total_trips': trips.count(),
    }
    return render(request, 'fleet/dashboard.html', {'kpis': kpis})


# ==================== VEHICLES ====================
@login_required
def vehicle_list(request):
    """List all vehicles with filters"""
    vehicles = Vehicle.objects.all()
    
    vehicle_type = request.GET.get('vehicle_type')
    status = request.GET.get('status')
    
    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    if status:
        vehicles = vehicles.filter(status=status)
    
    return render(request, 'fleet/vehicle_list.html', {'vehicles': vehicles})


@login_required
def vehicle_create(request):
    """Create new vehicle"""
    if request.method == 'POST':
        name = request.POST.get('name')
        model_name = request.POST.get('model_name')
        license_plate = request.POST.get('license_plate')
        vehicle_type = request.POST.get('vehicle_type')
        max_load_capacity = float(request.POST.get('max_load_capacity', 0))
        odometer = float(request.POST.get('odometer', 0))
        
        Vehicle.objects.create(
            name=name,
            model_name=model_name,
            license_plate=license_plate,
            vehicle_type=vehicle_type,
            max_load_capacity=max_load_capacity,
            odometer=odometer
        )
        messages.success(request, 'Vehicle created successfully.')
        return redirect('fleet:vehicle_list')
    
    return render(request, 'fleet/vehicle_form.html', {'title': 'Add Vehicle'})


@login_required
def vehicle_edit(request, pk):
    """Edit existing vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        vehicle.name = request.POST.get('name')
        vehicle.model_name = request.POST.get('model_name')
        vehicle.license_plate = request.POST.get('license_plate')
        vehicle.vehicle_type = request.POST.get('vehicle_type')
        vehicle.max_load_capacity = float(request.POST.get('max_load_capacity', 0))
        vehicle.odometer = float(request.POST.get('odometer', 0))
        vehicle.status = request.POST.get('status')
        vehicle.is_out_of_service = request.POST.get('is_out_of_service') == 'on'
        vehicle.save()
        
        messages.success(request, 'Vehicle updated successfully.')
        return redirect('fleet:vehicle_list')
    
    return render(request, 'fleet/vehicle_form.html', {'vehicle': vehicle, 'title': 'Edit Vehicle'})


@login_required
def vehicle_delete(request, pk):
    """Delete vehicle"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted successfully.')
        return redirect('fleet:vehicle_list')
    
    return render(request, 'fleet/vehicle_confirm_delete.html', {'vehicle': vehicle})


# ==================== TRIPS ====================
@login_required
def trip_list(request):
    """List all trips"""
    trips = Trip.objects.select_related('vehicle', 'driver').all()
    
    status = request.GET.get('status')
    if status:
        trips = trips.filter(status=status)
    
    return render(request, 'fleet/trip_list.html', {'trips': trips})


@login_required
def trip_create(request):
    """Create new trip with validation"""
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')
        driver_id = request.POST.get('driver_id')
        cargo_weight = float(request.POST.get('cargo_weight', 0))
        origin = request.POST.get('origin')
        destination = request.POST.get('destination')
        
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        driver = get_object_or_404(Driver, pk=driver_id)
        
        # Business Logic: Validate cargo weight
        if cargo_weight > vehicle.max_load_capacity:
            messages.error(request, f'Cargo weight ({cargo_weight}kg) exceeds vehicle capacity ({vehicle.max_load_capacity}kg)')
            return redirect('fleet:trip_create')
        
        if vehicle.status != Vehicle.Status.AVAILABLE:
            messages.error(request, 'Vehicle is not available')
            return redirect('fleet:trip_create')
        
        # Business Logic: Check driver license
        if driver.is_license_expired:
            messages.error(request, 'Driver license has expired')
            return redirect('fleet:trip_create')
        
        if driver.status != Driver.Status.ON_DUTY:
            messages.error(request, 'Driver is not available')
            return redirect('fleet:trip_create')
        
        Trip.objects.create(
            vehicle=vehicle,
            driver=driver,
            cargo_weight=cargo_weight,
            origin=origin,
            destination=destination,
            status=Trip.Status.DRAFT
        )
        messages.success(request, 'Trip created successfully.')
        return redirect('fleet:trip_list')
    
    vehicles = Vehicle.objects.filter(status=Vehicle.Status.AVAILABLE, is_out_of_service=False)
    drivers = Driver.objects.filter(status=Driver.Status.ON_DUTY, license_expiry__gt=timezone.now().date())
    
    return render(request, 'fleet/trip_form.html', {
        'vehicles': vehicles,
        'drivers': drivers,
        'title': 'Create Trip'
    })


@login_required
@transaction.atomic
def trip_dispatch(request, pk):
    """Dispatch trip - update vehicle and driver status"""
    trip = get_object_or_404(Trip, pk=pk)
    
    if trip.status != Trip.Status.DRAFT:
        messages.error(request, 'Only draft trips can be dispatched.')
        return redirect('fleet:trip_list')
    
    if request.method == 'POST':
        start_odometer = float(request.POST.get('start_odometer', 0))
        
        trip.status = Trip.Status.DISPATCHED
        trip.start_odometer = start_odometer
        trip.start_date = timezone.now()
        trip.save()
        
        trip.vehicle.status = Vehicle.Status.ON_TRIP
        trip.vehicle.save()
        
        trip.driver.status = Driver.Status.ON_DUTY
        trip.driver.save()
        
        messages.success(request, 'Trip dispatched successfully.')
        return redirect('fleet:trip_list')
    
    return render(request, 'fleet/trip_dispatch.html', {'trip': trip})


@login_required
@transaction.atomic
def trip_complete(request, pk):
    """Complete trip - update vehicle/driver back to available"""
    trip = get_object_or_404(Trip, pk=pk)
    
    if trip.status != Trip.Status.DISPATCHED:
        messages.error(request, 'Only dispatched trips can be completed.')
        return redirect('fleet:trip_list')
    
    if request.method == 'POST':
        end_odometer = float(request.POST.get('end_odometer', 0))
        
        trip.status = Trip.Status.COMPLETED
        trip.end_odometer = end_odometer
        trip.end_date = timezone.now()
        trip.save()
        
        trip.vehicle.status = Vehicle.Status.AVAILABLE
        trip.vehicle.odometer = end_odometer
        trip.vehicle.save()
        
        trip.driver.status = Driver.Status.OFF_DUTY
        trip.driver.save()
        
        # Update driver completion rate
        all_trips = Trip.objects.filter(driver=trip.driver)
        completed = all_trips.filter(status=Trip.Status.COMPLETED).count()
        trip.driver.trip_completion_rate = (completed / all_trips.count() * 100) if all_trips.exists() else 0
        trip.driver.save()
        
        messages.success(request, 'Trip completed successfully.')
        return redirect('fleet:trip_list')
    
    return render(request, 'fleet/trip_complete.html', {'trip': trip})


@login_required
@transaction.atomic
def trip_cancel(request, pk):
    """Cancel trip"""
    trip = get_object_or_404(Trip, pk=pk)
    
    if request.method == 'POST':
        was_dispatched = trip.status == Trip.Status.DISPATCHED
        trip.status = Trip.Status.CANCELLED
        trip.save()
        
        if was_dispatched:
            trip.vehicle.status = Vehicle.Status.AVAILABLE
            trip.vehicle.save()
            trip.driver.status = Driver.Status.OFF_DUTY
            trip.driver.save()
        
        messages.success(request, 'Trip cancelled successfully.')
        return redirect('fleet:trip_list')
    
    return render(request, 'fleet/trip_confirm_cancel.html', {'trip': trip})


# ==================== MAINTENANCE ====================
@login_required
def maintenance_list(request):
    """List all maintenance logs"""
    logs = MaintenanceLog.objects.select_related('vehicle').all()
    return render(request, 'fleet/maintenance_list.html', {'logs': logs})


@login_required
@transaction.atomic
def maintenance_create(request):
    """Create maintenance log - auto set vehicle to IN_SHOP"""
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')
        service_type = request.POST.get('service_type')
        description = request.POST.get('description')
        cost = float(request.POST.get('cost', 0))
        date_str = request.POST.get('date')
        
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        
        # Business Logic: Set vehicle to IN_SHOP
        vehicle.status = Vehicle.Status.IN_SHOP
        vehicle.save()
        
        from datetime import datetime
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else timezone.now()
        
        MaintenanceLog.objects.create(
            vehicle=vehicle,
            service_type=service_type,
            description=description,
            cost=cost,
            date=date
        )
        
        messages.success(request, 'Maintenance log created. Vehicle set to In Shop.')
        return redirect('fleet:maintenance_list')
    
    vehicles = Vehicle.objects.all()
    return render(request, 'fleet/maintenance_form.html', {'vehicles': vehicles, 'title': 'Add Maintenance Log'})


@login_required
@transaction.atomic
def maintenance_complete(request, pk):
    """Complete maintenance - return vehicle to available if no pending maintenance"""
    log = get_object_or_404(MaintenanceLog, pk=pk)
    
    if request.method == 'POST':
        log.completed_at = timezone.now()
        log.save()
        
        # Check if vehicle has other pending maintenance
        pending = MaintenanceLog.objects.filter(vehicle=log.vehicle, completed_at__isnull=True).exists()
        
        if not pending:
            log.vehicle.status = Vehicle.Status.AVAILABLE
            log.vehicle.save()
        
        messages.success(request, 'Maintenance marked complete.')
        return redirect('fleet:maintenance_list')
    
    return render(request, 'fleet/maintenance_complete.html', {'log': log})


# ==================== DRIVERS ====================
@login_required
def driver_list(request):
    """List all drivers"""
    drivers = Driver.objects.all()
    return render(request, 'fleet/driver_list.html', {'drivers': drivers})


@login_required
def driver_create(request):
    """Create new driver"""
    if request.method == 'POST':
        Driver.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            license_number=request.POST.get('license_number'),
            license_category=request.POST.get('license_category'),
            license_expiry=request.POST.get('license_expiry'),
            status=request.POST.get('status', Driver.Status.OFF_DUTY)
        )
        messages.success(request, 'Driver created successfully.')
        return redirect('fleet:driver_list')
    
    return render(request, 'fleet/driver_form.html', {'title': 'Add Driver'})


@login_required
def driver_edit(request, pk):
    """Edit driver"""
    driver = get_object_or_404(Driver, pk=pk)
    
    if request.method == 'POST':
        driver.name = request.POST.get('name')
        driver.email = request.POST.get('email')
        driver.phone = request.POST.get('phone')
        driver.license_number = request.POST.get('license_number')
        driver.license_category = request.POST.get('license_category')
        driver.license_expiry = request.POST.get('license_expiry')
        driver.status = request.POST.get('status')
        driver.safety_score = float(request.POST.get('safety_score', 100))
        driver.save()
        
        messages.success(request, 'Driver updated successfully.')
        return redirect('fleet:driver_list')
    
    return render(request, 'fleet/driver_form.html', {'driver': driver, 'title': 'Edit Driver'})


@login_required
def driver_delete(request, pk):
    """Delete driver"""
    driver = get_object_or_404(Driver, pk=pk)
    
    if request.method == 'POST':
        driver.delete()
        messages.success(request, 'Driver deleted successfully.')
        return redirect('fleet:driver_list')
    
    return render(request, 'fleet/driver_confirm_delete.html', {'driver': driver})


# ==================== EXPENSES ====================
@login_required
def expense_list(request):
    """List all expenses with total operational cost per vehicle"""
    expenses = Expense.objects.select_related('vehicle', 'trip').all()
    vehicles = Vehicle.objects.all()
    
    vehicle_costs = {}
    for vehicle in vehicles:
        total = Expense.objects.filter(
            vehicle=vehicle,
            expense_type__in=[Expense.Type.FUEL, Expense.Type.MAINTENANCE, Expense.Type.REPAIR]
        ).aggregate(total=Sum('amount'))['total'] or 0
        vehicle_costs[vehicle.id] = total
    
    vehicle_costs_list = [{'vehicle': v, 'cost': vehicle_costs.get(v.id, 0)} for v in vehicles]
    
    return render(request, 'fleet/expense_list.html', {
        'expenses': expenses,
        'vehicle_costs_list': vehicle_costs_list
    })


@login_required
def expense_create(request):
    """Create expense log"""
    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')
        trip_id = request.POST.get('trip_id') or None
        expense_type = request.POST.get('expense_type')
        amount = float(request.POST.get('amount', 0))
        liters = request.POST.get('liters')
        date_str = request.POST.get('date')
        description = request.POST.get('description', '')
        
        vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
        trip = get_object_or_404(Trip, pk=trip_id) if trip_id else None
        
        from datetime import datetime
        date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else timezone.now()
        
        Expense.objects.create(
            vehicle=vehicle,
            trip=trip,
            expense_type=expense_type,
            amount=amount,
            liters=float(liters) if liters else None,
            date=date,
            description=description
        )
        
        messages.success(request, 'Expense logged successfully.')
        return redirect('fleet:expense_list')
    
    vehicles = Vehicle.objects.all()
    trips = Trip.objects.filter(status__in=[Trip.Status.DISPATCHED, Trip.Status.COMPLETED])
    
    return render(request, 'fleet/expense_form.html', {
        'vehicles': vehicles,
        'trips': trips,
        'title': 'Log Expense'
    })


# ==================== REPORTS ====================
@login_required
def reports(request):
    """Analytics and reports dashboard"""
    vehicles = Vehicle.objects.all()
    trips = Trip.objects.all()
    
    analytics = []
    for vehicle in vehicles:
        total_cost = Expense.objects.filter(
            vehicle=vehicle,
            expense_type__in=[Expense.Type.FUEL, Expense.Type.MAINTENANCE, Expense.Type.REPAIR]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        completed_trips = vehicle.trips.filter(status=Trip.Status.COMPLETED).count()
        
        analytics.append({
            'vehicle': vehicle,
            'total_operational_cost': total_cost,
            'completed_trips': completed_trips,
            'odometer': vehicle.odometer,
        })
    
    return render(request, 'fleet/reports.html', {'analytics': analytics})


@login_required
def export_csv(request):
    """Export fleet analytics to CSV"""
    vehicles = Vehicle.objects.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fleet-analytics.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Vehicle', 'Type', 'Status', 'Total Cost', 'Completed Trips', 'Odometer'])
    
    for vehicle in vehicles:
        total_cost = Expense.objects.filter(
            vehicle=vehicle,
            expense_type__in=[Expense.Type.FUEL, Expense.Type.MAINTENANCE, Expense.Type.REPAIR]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        completed = vehicle.trips.filter(status=Trip.Status.COMPLETED).count()
        
        writer.writerow([
            vehicle.name,
            vehicle.get_vehicle_type_display(),
            vehicle.get_status_display(),
            total_cost,
            completed,
            vehicle.odometer
        ])
    
    return response


@login_required
def export_pdf(request):
    """Export fleet analytics to PDF"""
    vehicles = Vehicle.objects.all()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fleet-analytics.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    from reportlab.platypus import Paragraph
    elements.append(Paragraph('FleetFlow Analytics Report', styles['Title']))
    
    data = [['Vehicle', 'Type', 'Status', 'Total Cost', 'Trips', 'Odometer']]
    
    for vehicle in vehicles:
        total_cost = Expense.objects.filter(
            vehicle=vehicle,
            expense_type__in=[Expense.Type.FUEL, Expense.Type.MAINTENANCE, Expense.Type.REPAIR]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        completed = vehicle.trips.filter(status=Trip.Status.COMPLETED).count()
        
        data.append([
            vehicle.name,
            vehicle.get_vehicle_type_display(),
            vehicle.get_status_display(),
            f'${total_cost:.2f}',
            str(completed),
            f'{vehicle.odometer:.0f} km'
        ])
    
    from reportlab.platypus import Table
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    
    elements.append(t)
    doc.build(elements)
    return response


# ==================== AUTHENTICATION ====================
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordResetView


class FleetLoginView(LoginView):
    """Custom login view"""
    template_name = 'fleet/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return '/dashboard/'


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('fleet:login')


class ForgotPasswordView(PasswordResetView):
    """Forgot password view"""
    template_name = 'fleet/forgot_password.html'
    success_url = '/login/'
