#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting deployment setup...${NC}"

# 1. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements/production.txt
else
    echo -e "${GREEN}Activating existing virtual environment...${NC}"
    source venv/bin/activate
fi

# 2. Set up environment variables
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    python setup_production.py
    echo -e "${YELLOW}⚠️  Please edit the .env file with your production settings and run this script again.${NC}"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# 3. Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements/production.txt

# 4. Run database migrations
echo -e "${GREEN}Running database migrations...${NC}
python manage.py migrate

# 5. Collect static files
echo -e "${GREEN}Collecting static files...${NC}
python manage.py collectstatic --noinput

# 6. Create superuser if needed
if [ "$1" == "--create-superuser" ]; then
    python manage.py createsuperuser
fi

echo -e "\n${GREEN}✅ Deployment setup complete!${NC}"
echo -e "\nTo start the production server, run:"
echo -e "  source venv/bin/activate"
echo -e "  gunicorn config.wsgi:application --bind 0.0.0.0:8000"

echo -e "\nFor production, it's recommended to use a process manager like systemd or supervisor."
echo -e "See the deployment guide for more details."
