#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start development server with ASGI
uvicorn core.asgi:application --host 0.0.0.0 --port 52511 --reload