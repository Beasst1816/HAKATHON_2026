# FleetFlow (Django)

Modular Fleet & Logistics Management System built with **Django**, PostgreSQL (or SQLite), and Bootstrap 5.

## Features

- **Command Center** – Dashboard with KPIs (Active Fleet, Maintenance Alerts, Utilization Rate, Pending Cargo)
- **Vehicle Registry** – CRUD, filters by type/status, Out of Service toggle
- **Trip Dispatcher** – Create trips (Draft → Dispatched → Completed/Cancelled), cargo validation
- **Maintenance Logs** – Add logs (vehicle auto-set to In Shop), mark complete to return to Available
- **Expenses & Fuel** – Log fuel/maintenance per vehicle, total operational cost per vehicle
- **Driver Profiles** – CRUD, license expiry warning, status (On Duty / Off Duty / Suspended), safety score
- **Analytics & Reports** – Fleet analytics table, one-click **CSV** and **PDF** exports

## Business logic

- Trip creation blocked if **cargo weight > vehicle max capacity**
- Adding a maintenance log sets vehicle status to **In Shop** and removes it from dispatcher pool
- **License expired** drivers are excluded from trip assignment (available drivers query)
- Trip **Complete** updates vehicle/driver back to Available and recalculates driver completion rate
- **Total operational cost** = sum of Fuel + Maintenance + Repair expenses per vehicle

## Tech stack

- **Backend:** Django 5.x
- **Database:** SQLite (default) or PostgreSQL via `DATABASE_URL`
- **Auth:** Django auth (email as username), RBAC via `User.role`
- **Frontend:** Bootstrap 5 (CDN), server-rendered templates
- **Exports:** `csv`, `reportlab` for PDF

## Setup

1. **Create virtualenv and install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. **Environment**
   - Copy `.env.example` to `.env` (or set `DEBUG=1` and optionally `DATABASE_URL` for PostgreSQL).

3. **Database**
   ```bash
   python manage.py migrate
   python manage.py seed_fleetflow    # optional: creates manager@fleetflow.com / password123, etc.
   python manage.py createsuperuser # for /admin/
   ```

4. **Run**
   ```bash
   python manage.py runserver
   ```
   - App: http://127.0.0.1:8000/ (redirects to dashboard or login)
   - Admin: http://127.0.0.1:8000/admin/

## Default logins (after seed)

| Email                     | Password   | Role              |
|---------------------------|------------|-------------------|
| manager@fleetflow.com     | password123| Fleet Manager     |
| dispatcher@fleetflow.com  | password123| Dispatcher        |
| safety@fleetflow.com     | password123| Safety Officer    |
| finance@fleetflow.com    | password123| Financial Analyst |

Use **username** = email on the login form.

## Project structure

```
fleetflow/           # project settings
accounts/            # custom User (role), login, logout, forgot password
fleet/               # main app
  models.py          # Vehicle, Driver, Trip, Expense, MaintenanceLog
  services.py        # business logic (create_trip, dispatch_trip, complete_trip, etc.)
  views/             # dashboard, vehicles, trips, maintenance, drivers, expenses, reports
  forms.py
  urls.py
templates/           # base, accounts, fleet templates
static/
```

## RBAC

Roles are stored on `User.role`. All fleet views are `@login_required`. Role-based UI or permission checks can be added in templates or view decorators (e.g. only DISPATCHER can create trips) as needed.
