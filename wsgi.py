"""WSGI entry point for Render/Gunicorn."""
from app import app, init_db

# Gunicorn imports this module, so ensure PostgreSQL tables exist on startup.
init_db()
