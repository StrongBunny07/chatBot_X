# ChatBot X - Deployment Guide

## Deployment Target

This guide deploys ChatBot X on Ubuntu using:

- Django backend served by Gunicorn
- React frontend built with Vite and served by Nginx
- Hugging Face Inference API (Qwen) for model responses
- `.env` file for secrets

## Final Production Architecture

```text
Browser
  -> Nginx :80/:443
     -> Frontend static files
     -> /api/ -> Gunicorn/Django :8000
                    -> Hugging Face Inference API (HTTPS)
```

---

## 1. Server Requirements

- Ubuntu 22.04 or 24.04
- Python 3.10+
- Node.js 18+
- Nginx
- Outbound internet access to `api-inference.huggingface.co`
- Hugging Face API token

---

## 2. Clone the Project

```bash
cd /var/www
sudo git clone <your-repo-url> chatBot_X
sudo chown -R $USER:$USER chatBot_X
cd chatBot_X
```

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

## 4. Configure Environment Variables

Create backend env file:

```bash
cd /var/www/chatBot_X/backend
cp .env.example .env
nano .env
```

Set your token:

```env
HF_API_KEY=hf_your_real_token_here
```

---

## 5. Install Backend Dependencies

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

Before deployment, set:

- `DEBUG = False`
- `ALLOWED_HOSTS` to your domain/server IP
- `CORS_ALLOWED_ORIGINS` to your frontend domain only

Example:

```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'your-server-ip']

CORS_ALLOWED_ORIGINS = [
    'https://your-domain.com',
]
```

---

## 7. Build the React Frontend

```bash
cd /var/www/chatBot_X/frontend
npm install
npm run build
```

Build output:

```bash
/var/www/chatBot_X/frontend/dist
```

---

## 8. Create Gunicorn Service

Create service file:

```bash
sudo nano /etc/systemd/system/chatbotx.service
```

Use this config:

```ini
[Unit]
Description=ChatBot X Django Gunicorn Service
After=network.target

[Service]
User=nandha
Group=www-data
WorkingDirectory=/var/www/chatBot_X/backend
Environment="PATH=/var/www/chatBot_X/backend/.venv/bin"
EnvironmentFile=/var/www/chatBot_X/backend/.env
ExecStart=/var/www/chatBot_X/backend/.venv/bin/gunicorn backend.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable chatbotx
sudo systemctl start chatbotx
sudo systemctl status chatbotx
```

---

## 9. Configure Nginx

Create config:

```bash
sudo nano /etc/nginx/sites-available/chatbotx
```

Use:

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
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/chatbotx /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
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
sudo systemctl status chatbotx
sudo systemctl status nginx
```

Test backend directly:

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","useWeb":true,"stream":false}'
```

Open app:

```text
http://your-server-ip
```

---

## 12. Optional HTTPS with Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## 13. Useful Production Commands

Restart services:

```bash
sudo systemctl restart chatbotx
sudo systemctl restart nginx
```

View logs:

```bash
journalctl -u chatbotx -f
sudo tail -f /var/log/nginx/error.log
```

Rebuild frontend:

```bash
cd /var/www/chatBot_X/frontend
npm run build
sudo systemctl restart nginx
```

---

## Current Project Constraints Before Production

- Django still needs production hardening (`DEBUG=False`, secure cookie settings, strict CORS).
- SQLite is fine for light use, but PostgreSQL is better for multi-user production.
- Hugging Face API introduces network dependency and token usage costs.
- Large answers may increase response time and API cost.

---

## Recommended First Deployment

Use this stack for the first production rollout:

- Django + Gunicorn
- React static build
- Nginx reverse proxy
- Hugging Face Inference API via `.env` token

This is the cleanest path for your current codebase (no Ollama dependency).