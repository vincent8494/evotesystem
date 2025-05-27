#!/bin/bash

# Create a virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install --upgrade pip
pip install django django-crispy-forms crispy-bootstrap5 python-dotenv

# Create .env file for environment variables
echo "Creating .env file..."
cat > .env << 'EOL'
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
EOL

# Create requirements.txt
echo "Creating requirements.txt..."
pip freeze > requirements.txt

# Create Django project and apps
echo "Creating Django project and apps..."
django-admin startproject config .
python manage.py startapp accounts
python manage.py startapp voting
python manage.py startapp api

# Create necessary directories
echo "Creating static and media directories..."
mkdir -p static/{css,js,img}
mkdir -p media

echo "Setup complete! Activate the virtual environment with 'source venv/bin/activate'"
