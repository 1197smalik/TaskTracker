# TaskTracker - Enterprise Task Management Software

A comprehensive task tracking system for developers and managers, built with Django REST Framework backend and Streamlit frontend.

## Features

- **Project Management**: Create and manage projects with team members
- **Task Tracking**: Assign tasks with status, priority, and due dates
- **User Management**: Role-based access for managers and developers
- **Dashboard**: Real-time insights and reports
- **API-Driven**: RESTful API for integrations

## Tech Stack

- **Backend**: Django 6.0, Django REST Framework
- **Frontend**: Streamlit
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Django Auth

## Setup

1. **Clone and Setup Environment**:
   ```bash
   cd /path/to/TaskTracker
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

4. **Start Django Server**:
   ```bash
   python manage.py runserver 8001
   ```
   Server runs on http://localhost:8001

5. **Start Streamlit App** (in another terminal):
   ```bash
   streamlit run app.py
   ```
   App runs on http://localhost:8501

## API Endpoints

- `GET/POST/PUT/DELETE /api/projects/` - Project CRUD
- `GET/POST/PUT/DELETE /api/tasks/` - Task CRUD
- `GET /admin/` - Django Admin (login required)

## Development

- Add new features to respective Django apps
- Update Streamlit UI in `app.py`
- Run tests: `python manage.py test`

## Deployment

For production, configure PostgreSQL, set DEBUG=False, and use a WSGI server like Gunicorn.