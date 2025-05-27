#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}🚀 Starting production server setup...${NC}"

# 1. Update system packages
echo -e "\n${GREEN}Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# 2. Install required system packages
echo -e "\n${GREEN}Installing system dependencies...${NC}"
apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    redis-server \
    supervisor \
    certbot \
    python3-certbot-nginx

# 3. Set up PostgreSQL
echo -e "\n${GREEN}Setting up PostgreSQL...${NC}"
sudo -u postgres psql -c "CREATE DATABASE electionsproject;"
sudo -u postgres psql -c "CREATE USER electionsuser WITH PASSWORD 'your-secure-password';"
sudo -u postgres psql -c "ALTER ROLE electionsuser SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE electionsuser SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE electionsuser SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE electionsproject TO electionsuser;"

# 4. Set up Python virtual environment
echo -e "\n${GREEN}Setting up Python virtual environment...${NC}
cd /home/fetty/electionsproject
python3 -m venv venv
source venv/bin/activate

# 5. Install Python dependencies
echo -e "\n${GREEN}Installing Python dependencies...${NC}
pip install --upgrade pip
pip install -r requirements/production.txt

# 6. Set up Gunicorn service
echo -e "\n${GREEN}Setting up Gunicorn service...${NC}
cp config/gunicorn.service /etc/systemd/system/electionsproject.service
systemctl daemon-reload
systemctl enable electionsproject
systemctl start electionsproject

# 7. Configure Nginx
echo -e "\n${GREEN}Configuring Nginx...${NC}
cp config/nginx.conf /etc/nginx/sites-available/electionsproject
ln -sf /etc/nginx/sites-available/electionsproject /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# 8. Set permissions
echo -e "\n${GREEN}Setting up permissions...${NC}
chown -R fetty:www-data /home/fetty/electionsproject
chmod -R 755 /home/fetty/electionsproject/static
chmod -R 755 /home/fetty/electionsproject/media

# 9. Restart services
echo -e "\n${GREEN}Restarting services...${NC}
systemctl restart nginx
systemctl restart electionsproject

# 10. Set up SSL with Let's Encrypt
echo -e "\n${YELLOW}Would you like to set up SSL with Let's Encrypt? (y/n)${NC}"
read -r SETUP_SSL

if [ "$SETUP_SSL" = "y" ] || [ "$SETUP_SSL" = "Y" ]; then
    echo -e "\n${GREEN}Setting up SSL with Let's Encrypt...${NC}"
    echo -e "${YELLOW}Please enter your domain name (e.g., example.com):${NC}"
    read -r DOMAIN
    
    # Stop Nginx temporarily
    systemctl stop nginx
    
    # Obtain SSL certificate
    certbot certonly --standalone -d "$DOMAIN" -d "www.$DOMAIN" \
        --non-interactive --agree-tos --email admin@$DOMAIN --expand
    
    # Update Nginx config with the correct domain
    sed -i "s/yourdomain.com/$DOMAIN/g" /etc/nginx/sites-available/electionsproject
    
    # Restart Nginx
    systemctl start nginx
    
    # Set up automatic renewal
    echo "0 0,12 * * * root python -c 'import random; import time; time.sleep(random.random() * 3600)' && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
    
    echo -e "\n${GREEN}SSL certificate has been set up successfully!${NC}
"
fi

# 11. Set up firewall
echo -e "\n${GREEN}Configuring firewall...${NC}
ufw allow 'Nginx Full'
ufw allow 'OpenSSH'
ufw --force enable

# 12. Final instructions
echo -e "\n${GREEN}✅ Production server setup complete!${NC}"
echo -e "\nNext steps:"
echo "1. Edit the .env file with your production settings"
echo "2. Run database migrations: python manage.py migrate"
echo "3. Create a superuser: python manage.py createsuperuser"
echo "4. Collect static files: python manage.py collectstatic --noinput"
echo -e "\nYour application should now be accessible at ${YELLOW}http://yourdomain.com${NC}"
echo -e "Or with SSL at ${YELLOW}https://yourdomain.com${NC} if you set it up"

# Make the script executable
chmod +x setup_production_server.sh
