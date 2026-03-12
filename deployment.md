# ChatBot X - Deployment Guide

## Deployment Target

This guide is for deploying the project on an Ubuntu Linux server with:

- Native Ollama installation
- Django backend served by Gunicorn
- React frontend built with Vite and served by Nginx
- Nginx reverse proxy in front of both frontend and backend

This is the recommended path for your current setup because Ollama is already installed directly on the machine.

---

## Final Production Architecture

```text
Browser
  -> Nginx :80
     -> Frontend static files
     -> /api/ -> Gunicorn/Django :8000
                    -> Ollama :11434
```

---

## 1. Server Requirements

- Ubuntu 22.04 or 24.04
- Python 3.10+
- Node.js 18+
- Nginx
- Ollama installed and running
- At least 8 GB RAM for smaller models
- At least 15 GB free disk space

For CPU-only deployment, use `deepseek-r1:1.5b` first. Larger models need more RAM and will be slower.

---

## 2. Clone the Project

```bash
cd /var/www
sudo git clone <your-repo-url> chatBot_X
sudo chown -R $USER:$USER chatBot_X
cd chatBot_X
```

If the repo is already copied manually, just move into the project directory.

---

## 3. Install System Packages

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv nginx curl
```

If Node.js is not installed:

```bash
sudo apt install -y nodejs npm
```

---

## 4. Install and Start Ollama

If Ollama is not already installed:

```bash
curl -fsSL https://ollama.com/install.sh | sudo sh
```

Verify it is running:

```bash
curl http://localhost:11434/
```

Pull the model:

```bash
ollama pull deepseek-r1:1.5b
ollama list
```

---

## 5. Install Backend Dependencies

Your current project was created without a virtual environment, but for deployment you should use one. Production should not rely on global Python packages.

```bash
cd /var/www/chatBot_X/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

Run migrations:

```bash
python manage.py migrate
```

Optional admin user:

```bash
python manage.py createsuperuser
```

---

## 6. Update Django for Production

Before deployment, update these values in Django settings:

- `DEBUG = False`
- Set `ALLOWED_HOSTS` to your server IP or domain
- Restrict CORS to your real frontend domain

Example values:

```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'your-server-ip']

CORS_ALLOWED_ORIGINS = [
    'http://your-domain.com',
    'https://your-domain.com',
]
```

Your current Ollama settings can stay the same if Ollama runs on the same machine:

```python
OLLAMA_BASE_URL = 'http://localhost:11434'
OLLAMA_MODEL = 'deepseek-r1:1.5b'
```

---

## 7. Build the React Frontend

```bash
cd /var/www/chatBot_X/frontend
npm install
npm run build
```

This creates production files in:

```bash
/var/www/chatBot_X/frontend/dist
```

---

## 8. Create Gunicorn Service

Create the service file:

```bash
sudo nano /etc/systemd/system/chatbotx.service
```

Paste this:

```ini
[Unit]
Description=ChatBot X Django Gunicorn Service
After=network.target ollama.service

[Service]
User=nandha
Group=www-data
WorkingDirectory=/var/www/chatBot_X/backend
Environment="PATH=/var/www/chatBot_X/backend/.venv/bin"
ExecStart=/var/www/chatBot_X/backend/.venv/bin/gunicorn backend.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable chatbotx
sudo systemctl start chatbotx
sudo systemctl status chatbotx
```

---

## 9. Configure Nginx

Create an Nginx config:

```bash
sudo nano /etc/nginx/sites-available/chatbotx
```

Paste this:

```nginx
server {
    listen 80;
    server_name your-domain.com your-server-ip;

    root /var/www/chatBot_X/frontend/dist;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/chatbotx /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

If the default Nginx site conflicts, disable it:

```bash
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

---

## 10. Open Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 11. Verify Deployment

Check services:

```bash
curl http://localhost:11434/
sudo systemctl status ollama
sudo systemctl status chatbotx
sudo systemctl status nginx
```

Test backend directly:

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}'
```

Then open:

```text
http://your-server-ip
```

Or your real domain if DNS is configured.

---

## 12. Optional HTTPS with Certbot

Install Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

Generate SSL config:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## 13. Useful Production Commands

Restart services:

```bash
sudo systemctl restart ollama
sudo systemctl restart chatbotx
sudo systemctl restart nginx
```

View logs:

```bash
journalctl -u ollama -f
journalctl -u chatbotx -f
sudo tail -f /var/log/nginx/error.log
```

Rebuild frontend after changes:

```bash
cd /var/www/chatBot_X/frontend
npm run build
sudo systemctl restart nginx
```

---

## Current Project Constraints Before Production

- Django is currently configured for development defaults and should be hardened before public deployment.
- SQLite is acceptable for small personal use, but PostgreSQL is better for multi-user production.
- The current backend returns full responses and does not stream tokens yet.
- CPU-only Ollama is fine for testing and small traffic, but it will be slow under load.
- For multiple users, use a larger server or a GPU-enabled machine.

---

## Recommended First Deployment

For your first deployment, use this exact stack:

- Native Ollama
- `deepseek-r1:1.5b`
- Django + Gunicorn
- React static build
- Nginx reverse proxy

That is the simplest stable path from your current local setup to a real server.