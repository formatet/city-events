#!/bin/bash
# Deploy script for the backend (scrapers)
# Run from the backend/ directory: ./deploy-backend.sh

set -e

# ── Configure these for your server ──────────────────────────────────────────
BACKEND_HOST="${BACKEND_HOST:-user@your-backend-server}"
BACKEND_DIR="${BACKEND_DIR:-/opt/city-events}"
# ─────────────────────────────────────────────────────────────────────────────

echo "🚀 Deploying city-events backend to $BACKEND_HOST..."

# Create directory structure on server
ssh $BACKEND_HOST "mkdir -p $BACKEND_DIR/{scrapers,logs}"

# Sync backend files
echo "📦 Syncing backend files..."
rsync -avz --progress \
    scrape_all.py \
    db_utils.py \
    config.py \
    generate_llm_data.py \
    requirements.txt \
    $BACKEND_HOST:$BACKEND_DIR/

# Sync scrapers
echo "🕷️  Syncing scrapers..."
rsync -avz --progress \
    scrapers/ \
    $BACKEND_HOST:$BACKEND_DIR/scrapers/

# Set up Python environment
echo "🐍 Setting up Python environment..."
ssh $BACKEND_HOST << EOF
cd $BACKEND_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

# Install systemd service and timer
echo "⏰ Installing systemd timer..."
scp city-events-scrape.service $BACKEND_HOST:/etc/systemd/system/
scp city-events-scrape.timer   $BACKEND_HOST:/etc/systemd/system/

ssh $BACKEND_HOST << 'EOF'
systemctl daemon-reload
systemctl enable city-events-scrape.timer
systemctl start city-events-scrape.timer
systemctl status city-events-scrape.timer --no-pager
echo ""
echo "Timer status:"
systemctl list-timers city-events-scrape.timer --no-pager
EOF

echo ""
echo "✅ Backend deployment complete!"
echo "⏰ Scraper timer enabled (runs at 03:00 daily)"
echo "🧪 Test manually: ssh $BACKEND_HOST 'cd $BACKEND_DIR && source venv/bin/activate && python3 scrape_all.py'"
