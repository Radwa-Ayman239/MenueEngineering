# Menu Engineering Backend

This directory contains the Django-based backend for the Menu Engineering application. It serves as the core API, handling data persistence, business logic (excluding AI generation), and user authentication.

## Service Overview

The backend is built with **Django** and **Django REST Framework (DRF)**. It connects to a **PostgreSQL** database and communicates with the `ml_service` for AI-powered features.

### Key Applications

- **`menu`**:
  - Manages menu items, sections, and categories.
  - Handles the "Menu Engineering Matrix" logic (Stars, Plowhorses, Puzzles, Dogs).
  - Processes orders.
  - Integration layer for ML service (proxying requests).

- **`users`**:
  - Custom user model with role-based access control (Admin, Manager, Staff, Customer).
  - Secure authentication using **Knox** tokens.
  - 2FA/OTP support via **Twilio** (or console fallback).
  - Email services for verification and password resets.

## Setup & Running

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements/base.txt
    ```

2.  **Migrations**:
    ```bash
    python manage.py migrate
    ```

3.  **Run Server**:
    ```bash
    python manage.py runserver
    ```

## Testing

Run the test suite using standard Django commands:

```bash
python manage.py test
```
