#!/bin/bash
# Deploy script for the web server (Flask API + static files)
# Run from the web/ directory: ./deploy-web.sh

set -e

# ── Configure these for your server ──────────────────────────────────────────
WEB_HOST="${WEB_HOST:-user@your-web-server}"
WEB_DIR="${WEB_DIR:-/var/www/city-events}"
# ─────────────────────────────────────────────────────────────────────────────

echo "🚀 Deploying city-events web to $WEB_HOST..."

# Create directory structure on server
ssh $WEB_HOST "mkdir -p $WEB_DIR"

# Sync Flask app and requirements
echo "📦 Syncing Flask app..."
rsync -avz --progress \
    app.py \
    requirements.txt \
    $WEB_HOST:$WEB_DIR/

# Sync static files
echo "🎨 Syncing static files..."
rsync -avz --progress --delete \
    static/ \
    $WEB_HOST:$WEB_DIR/static/

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
ssh $WEB_HOST << EOF
cd $WEB_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
chown -R www-data:www-data $WEB_DIR
EOF

# Install systemd service
echo "⚙️  Installing systemd service..."
scp city-events-api.service $WEB_HOST:/etc/systemd/system/
ssh $WEB_HOST << 'EOF'
systemctl daemon-reload
systemctl enable city-events-api
systemctl restart city-events-api
systemctl status city-events-api --no-pager
EOF

echo "✅ Deployment complete!"
