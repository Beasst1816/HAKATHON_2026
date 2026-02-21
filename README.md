# FleetFlow - Django Fleet Management System

Simple Django-based fleet and logistics management system with clean code structure.

## Project Structure

```
HAKATHON_2026/
├── fleetflow/              # Django project settings
│   ├── settings.py         # Configuration
│   ├── urls.py             # Root URLs
│   └── wsgi.py
├── fleet/                  # Main app (single app)
│   ├── models.py           # All models (User, Vehicle, Driver, Trip, Expense, Maintenance)
│   ├── views.py            # All views (simple, clean code)
│   ├── urls.py             # App URLs
│   ├── admin.py            # Admin configuration
│   └── management/
│       └── commands/
│           └── seed_users.py
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   └── fleet/              # Fleet app templates
│       ├── dashboard.html
│       ├── vehicle_list.html
│       ├── vehicle_form.html
│       ├── trip_list.html
│       ├── trip_form.html
│       ├── maintenance_list.html
│       ├── driver_list.html
│       ├── expense_list.html
│       ├── reports.html
│       └── login.html
├── static/                 # Static files
│   ├── css/
│   │   └── style.css        # All styles
│   └── images/
│       └── fleetflow-logo.png
├── manage.py
├── requirements.txt
└── db.sqlite3              # SQLite database (default)
```

## Features

- **Single App Structure**: Only `fleet` app - simple and clean
- **Clean Models**: All models in `fleet/models.py`
- **Simple Views**: All views in `fleet/views.py` - no complex abstractions
- **HTML Templates**: Simple Django templates in `templates/fleet/`
- **CSS Styling**: All styles in `static/css/style.css`
- **No JavaScript Frameworks**: Pure Django with minimal JavaScript

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Create users:**
   ```bash
   python manage.py seed_users
   ```

4. **Run server:**
   ```bash
   python manage.py runserver
   ```

## Login Credentials

After seeding, login with:
- Email: `manager@fleetflow.com` / Password: `password123`
- Email: `dispatcher@fleetflow.com` / Password: `password123`
- Email: `safety@fleetflow.com` / Password: `password123`
- Email: `finance@fleetflow.com` / Password: `password123`

## Code Structure

- **models.py**: Clean model definitions with comments
- **views.py**: Simple function-based views with business logic
- **Templates**: Plain HTML with Django template tags
- **CSS**: Single style.css file with dark theme

## Business Logic

All business logic is in `views.py`:
- Cargo weight validation
- Vehicle status updates
- Driver license checks
- Trip lifecycle management
- Cost calculations
