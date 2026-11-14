# DevOps Arena Deployment Guide

## AWS EC2 Deployment (Free Tier)

### Prerequisites
- AWS Account
- EC2 instance (t2.micro, Ubuntu 22.04)
- Domain name (optional)

### Step 1: Launch EC2 Instance

1. **Launch Instance:**
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t2.micro (free tier)
   - Storage: 30GB GP2 (free tier)
   - Security Group:
     - SSH (22) - Your IP
     - HTTP (80) - 0.0.0.0/0
     - HTTPS (443) - 0.0.0.0/0
     - Custom TCP (8000) - 0.0.0.0/0 (backend API)

2. **Connect to instance:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

### Step 2: Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Logout and login again for group changes
exit
```

### Step 3: Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-username/devops-arena.git
cd devops-arena

# Create production environment file
cat > .env.production << 'ENVEOF'
# Backend
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:////data/devops_arena.db
ALLOWED_ORIGINS=http://your-domain.com,http://your-ec2-ip

# Frontend
VITE_API_URL=http://your-ec2-ip:8000
ENVEOF

# Update docker-compose.prod.yml with your settings
```

### Step 4: Deploy with Docker Compose

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Verify containers are running
docker ps
```

### Step 5: Configure Nginx Reverse Proxy (Optional)

```bash
# Install Nginx
sudo apt install nginx -y

# Configure reverse proxy
sudo tee /etc/nginx/sites-available/devops-arena << 'NGINXEOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINXEOF

# Enable site
sudo ln -s /etc/nginx/sites-available/devops-arena /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL with Let's Encrypt (Optional)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Step 7: Monitoring and Maintenance

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update application
git pull
docker-compose -f docker-compose.prod.yml up -d --build

# Backup database
docker exec devops-arena-backend cp /data/devops_arena.db /backup/
```

## Automated Deployment Script

Save as `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying DevOps Arena..."

# Pull latest code
git pull origin main

# Build and restart containers
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to start
sleep 10

# Health check
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

if curl -f http://localhost:5173/ > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

echo "✅ Deployment complete!"
```

Make executable: `chmod +x deploy.sh`

## Troubleshooting

### Container Issues
```bash
# Check container status
docker ps -a

# View container logs
docker logs devops-arena-backend
docker logs devops-arena-frontend

# Restart specific container
docker-compose restart backend
```

### Docker Socket Access
```bash
# Verify Docker socket permissions
ls -la /var/run/docker.sock

# Fix permissions if needed
sudo chmod 666 /var/run/docker.sock
```

### Database Issues
```bash
# Access database
docker exec -it devops-arena-backend sqlite3 /data/devops_arena.db

# Create demo user
docker exec -it devops-arena-backend python -c "
from app.database import SessionLocal
from app.services.auth_service import create_user
db = SessionLocal()
create_user(db, 'demo', 'demo123')
db.close()
"
```

## Cost Estimation (AWS Free Tier)

- **EC2 t2.micro:** Free for 750 hours/month (first year)
- **30GB EBS storage:** Free for first year
- **Data transfer:** 15GB/month free
- **Estimated cost after free tier:** $10-15/month

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Enable HTTPS with SSL certificate
- [ ] Configure firewall rules (ufw)
- [ ] Set up automatic security updates
- [ ] Enable CloudWatch monitoring
- [ ] Configure backup strategy
- [ ] Set up log rotation
- [ ] Use strong passwords
- [ ] Restrict SSH access to your IP

## Performance Optimization

1. **Enable caching**
2. **Use CDN for static assets**
3. **Configure Docker resource limits**
4. **Set up database connection pooling**
5. **Enable Nginx gzip compression**

## Next Steps

1. Set up monitoring with CloudWatch or Prometheus
2. Configure automatic backups
3. Set up CI/CD with GitHub Actions
4. Add custom domain and SSL
5. Configure email notifications

---

For issues, see the main README or open a GitHub issue.
