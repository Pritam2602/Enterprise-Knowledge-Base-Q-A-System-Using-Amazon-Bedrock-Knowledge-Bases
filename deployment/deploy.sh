#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Enterprise Knowledge Base Q&A System — EC2 Deployment Script
# For Amazon Linux 2023 / Ubuntu 22.04+
# ═══════════════════════════════════════════════════════════════════

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Enterprise Knowledge Base Q&A System — Deployment Setup     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# ─── Variables ───────────────────────────────────────────────────────
APP_DIR="/home/ec2-user/bedrock-qa-app"
REPO_URL="https://github.com/Pritam2602/Enterprise-Knowledge-Base-Q-A-System-Using-Amazon-Bedrock-Knowledge-Bases.git"
BACKEND_PORT=8000
FRONTEND_PORT=80

# ─── Detect OS ───────────────────────────────────────────────────────
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS="unknown"
fi

echo ""
echo "📦 Step 1: System Update & Dependencies"
echo "────────────────────────────────────────"

if [ "$OS" = "amzn" ]; then
    # Amazon Linux
    sudo yum update -y
    sudo yum install -y python3.11 python3.11-pip git nginx
    PYTHON_CMD="python3.11"
    PIP_CMD="pip3.11"
elif [ "$OS" = "ubuntu" ]; then
    # Ubuntu
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3.11 python3.11-venv python3-pip git nginx
    PYTHON_CMD="python3.11"
    PIP_CMD="pip3"
else
    echo "❌ Unsupported OS: $OS"
    exit 1
fi

# ─── Install Node.js 20 ─────────────────────────────────────────────
echo ""
echo "📦 Step 2: Install Node.js 20"
echo "────────────────────────────────────────"

if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d 'v') -lt 20 ]]; then
    curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash - 2>/dev/null || \
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    if [ "$OS" = "amzn" ]; then
        sudo yum install -y nodejs
    else
        sudo apt install -y nodejs
    fi
fi

echo "   Node.js: $(node -v)"
echo "   npm: $(npm -v)"

# ─── Clone Repository ───────────────────────────────────────────────
echo ""
echo "📦 Step 3: Clone Repository"
echo "────────────────────────────────────────"

if [ -d "$APP_DIR" ]; then
    echo "   Directory exists. Pulling latest changes..."
    cd "$APP_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# ─── Backend Setup ──────────────────────────────────────────────────
echo ""
echo "🐍 Step 4: Backend Setup"
echo "────────────────────────────────────────"

cd "$APP_DIR"
$PYTHON_CMD -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Create .env if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "⚠️  Creating backend/.env from template..."
    cp backend/.env.example backend/.env
    echo ""
    echo "   ╔══════════════════════════════════════════════════════╗"
    echo "   ║  IMPORTANT: Edit backend/.env with your KB ID and   ║"
    echo "   ║  AWS configuration before starting the app!         ║"
    echo "   ║                                                     ║"
    echo "   ║  nano $APP_DIR/backend/.env                         ║"
    echo "   ╚══════════════════════════════════════════════════════╝"
    echo ""
fi

# ─── Frontend Build ─────────────────────────────────────────────────
echo ""
echo "⚛️  Step 5: Frontend Build"
echo "────────────────────────────────────────"

cd "$APP_DIR/frontend"
npm install
node ./node_modules/vite/bin/vite.js build

echo "   Build output: $APP_DIR/frontend/dist"

# ─── Nginx Configuration ────────────────────────────────────────────
echo ""
echo "🌐 Step 6: Nginx Configuration"
echo "────────────────────────────────────────"

sudo cp "$APP_DIR/deployment/nginx.conf" /etc/nginx/conf.d/bedrock-qa.conf

# Remove default config that might conflict
sudo rm -f /etc/nginx/conf.d/default.conf 2>/dev/null
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null

# Update the frontend dist path in nginx config
sudo sed -i "s|/home/ec2-user/bedrock-qa-app|$APP_DIR|g" /etc/nginx/conf.d/bedrock-qa.conf

# Test nginx config
sudo nginx -t

# ─── Systemd Service ────────────────────────────────────────────────
echo ""
echo "🔧 Step 7: Create Systemd Service"
echo "────────────────────────────────────────"

sudo tee /etc/systemd/system/bedrock-qa-backend.service > /dev/null << EOF
[Unit]
Description=Enterprise Knowledge Base Q&A - FastAPI Backend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# ─── Start Services ─────────────────────────────────────────────────
echo ""
echo "🚀 Step 8: Start Services"
echo "────────────────────────────────────────"

sudo systemctl daemon-reload
sudo systemctl enable bedrock-qa-backend
sudo systemctl start bedrock-qa-backend
sudo systemctl enable nginx
sudo systemctl restart nginx

# ─── Firewall ────────────────────────────────────────────────────────
echo ""
echo "🔥 Step 9: Configure Firewall"
echo "────────────────────────────────────────"

# Open ports 80 and 443
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload
elif command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Deployment Complete!                                     ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                             ║"
echo "║  Backend:  http://localhost:$BACKEND_PORT                       ║"
echo "║  Frontend: http://<your-ec2-public-ip>                      ║"
echo "║                                                             ║"
echo "║  Service Commands:                                          ║"
echo "║  • sudo systemctl status bedrock-qa-backend                 ║"
echo "║  • sudo systemctl restart bedrock-qa-backend                ║"
echo "║  • sudo journalctl -u bedrock-qa-backend -f                 ║"
echo "║                                                             ║"
echo "║  ⚠️  Make sure:                                              ║"
echo "║  1. EC2 Security Group allows inbound port 80               ║"
echo "║  2. IAM Role with Bedrock permissions is attached           ║"
echo "║  3. backend/.env has your KNOWLEDGE_BASE_ID                 ║"
echo "║                                                             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
