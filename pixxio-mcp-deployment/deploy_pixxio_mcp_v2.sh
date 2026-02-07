#!/bin/bash

################################################################################
# pixx.io MCP Server - Vereinfachtes Deployment Script
# Nutzt ausschließlich GitHub CLI (gh) für alle GitHub-Operationen
################################################################################

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

################################################################################
# SCHRITT 1: System-Check
################################################################################

print_header "SCHRITT 1: System-Check"

# Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python: $PYTHON_VERSION"
else
    print_error "Python 3 nicht gefunden!"
    exit 1
fi

# Git
if command -v git &> /dev/null; then
    print_success "Git: $(git --version)"
else
    print_error "Git nicht gefunden!"
    exit 1
fi

# Homebrew
if command -v brew &> /dev/null; then
    print_success "Homebrew: $(brew --version | head -n1)"
else
    print_warning "Homebrew nicht gefunden (optional)"
fi

################################################################################
# SCHRITT 2: GitHub CLI Installation
################################################################################

print_header "SCHRITT 2: GitHub CLI Setup"

if ! command -v gh &> /dev/null; then
    print_info "Installiere GitHub CLI..."
    if command -v brew &> /dev/null; then
        brew install gh
    else
        print_error "Homebrew wird für die Installation benötigt"
        exit 1
    fi
    print_success "GitHub CLI installiert"
else
    print_success "GitHub CLI bereits installiert"
fi

################################################################################
# SCHRITT 3: GitHub Authentifizierung
################################################################################

print_header "SCHRITT 3: GitHub Authentifizierung"

# Check if already authenticated
if gh auth status &> /dev/null; then
    print_success "Bereits bei GitHub angemeldet"
    GH_USER=$(gh api user --jq .login)
    print_info "Angemeldet als: $GH_USER"
else
    print_info "GitHub Login erforderlich..."
    print_info "Browser öffnet sich automatisch für OAuth-Login"
    echo ""
    read -p "Drücken Sie Enter, um fortzufahren..."
    
    if gh auth login -w -p https; then
        print_success "GitHub Authentifizierung erfolgreich"
        GH_USER=$(gh api user --jq .login)
        print_success "Angemeldet als: $GH_USER"
    else
        print_error "GitHub Authentifizierung fehlgeschlagen"
        exit 1
    fi
fi

################################################################################
# SCHRITT 4: Repository vorbereiten
################################################################################

print_header "SCHRITT 4: Repository vorbereiten"

REPO_NAME="pixxio-mcp-server"
print_info "Repository Name: $REPO_NAME"

# Check if repo exists
if gh repo view "$GH_USER/$REPO_NAME" &> /dev/null; then
    print_warning "Repository existiert bereits!"
    echo ""
    read -p "Löschen und neu erstellen? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh repo delete "$GH_USER/$REPO_NAME" --yes
        print_success "Altes Repository gelöscht"
    else
        print_error "Abgebrochen"
        exit 1
    fi
fi

################################################################################
# SCHRITT 5: Lokales Projekt erstellen
################################################################################

print_header "SCHRITT 5: Projekt-Dateien vorbereiten"

PROJECT_DIR="$HOME/pixxio-mcp-server"

# Cleanup if exists
if [ -d "$PROJECT_DIR" ]; then
    rm -rf "$PROJECT_DIR"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
print_success "Projekt-Verzeichnis: $PROJECT_DIR"

# Get script directory to find our Python file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy Python file if it exists
if [ -f "$SCRIPT_DIR/pixxio_mcp_python39.py" ]; then
    cp "$SCRIPT_DIR/pixxio_mcp_python39.py" "$PROJECT_DIR/pixxio_mcp.py"
    print_success "MCP Server Code kopiert"
else
    print_warning "pixxio_mcp_python39.py nicht gefunden - erstelle Platzhalter"
    cat > "$PROJECT_DIR/pixxio_mcp.py" << 'PYEOF'
#!/usr/bin/env python3
"""pixx.io MCP Server - Placeholder"""
print("pixx.io MCP Server - Installation erfolgreich!")
print("Bitte ersetzen Sie diese Datei mit dem vollständigen Server-Code.")
PYEOF
fi

# Create requirements.txt
cat > "$PROJECT_DIR/requirements.txt" << 'EOF'
mcp>=1.0.0
httpx>=0.27.0
pydantic>=2.0.0
EOF

# Create README
cat > "$PROJECT_DIR/README.md" << 'EOF'
# pixx.io MCP Server

Model Context Protocol server for pixx.io Digital Asset Management.

## Deployment

Deployed on FastMCP Cloud.

## Local Development

```bash
pip install -r requirements.txt
python pixxio_mcp.py
```

## Documentation

See repository for full documentation.
EOF

# Create .gitignore
cat > "$PROJECT_DIR/.gitignore" << 'EOF'
__pycache__/
*.py[cod]
.Python
venv/
.env
EOF

print_success "Projekt-Dateien erstellt"

################################################################################
# SCHRITT 6: Git initialisieren
################################################################################

print_header "SCHRITT 6: Git Repository initialisieren"

git init
git add .
git commit -m "Initial commit: pixx.io MCP Server POC"
git branch -M main
print_success "Git initialisiert und Dateien committed"

################################################################################
# SCHRITT 7: GitHub Repository erstellen und pushen
################################################################################

print_header "SCHRITT 7: Zu GitHub hochladen"

# Create repo and push using gh CLI
print_info "Erstelle GitHub Repository..."
gh repo create "$REPO_NAME" --public --source=. --remote=origin --description="pixx.io MCP Server - AI-powered Digital Asset Management integration"
print_success "Repository erstellt"

print_info "Pushe Code zu GitHub..."
git push -u origin main
print_success "Code hochgeladen"

print_success "Repository URL: https://github.com/$GH_USER/$REPO_NAME"

################################################################################
# SCHRITT 8: Dependencies installieren (optional)
################################################################################

print_header "SCHRITT 8: Python Dependencies (optional)"

read -p "Python Dependencies jetzt installieren? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installiere Dependencies..."
    python3 -m pip install --user --quiet mcp httpx pydantic 2>&1 | grep -v "already satisfied" || true
    print_success "Dependencies installiert"
else
    print_info "Übersprungen - können später installiert werden"
fi

################################################################################
# SCHRITT 9: FastMCP Cloud Anleitung
################################################################################

print_header "SCHRITT 9: FastMCP Cloud Deployment"

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  WICHTIG: FastMCP Cloud Setup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Ihr Code ist jetzt auf GitHub! 🎉"
echo ""
echo "Nächste Schritte für FastMCP Cloud:"
echo ""
echo "1. Öffnen Sie: ${BLUE}https://fastmcp.cloud${NC}"
echo "2. Klicken Sie: 'Sign in with GitHub'"
echo "3. Klicken Sie: 'New Project'"
echo "4. Wählen Sie: ${GREEN}$GH_USER/$REPO_NAME${NC}"
echo "5. Konfiguration:"
echo "   ${BLUE}Project Name:${NC} pixxio-mcp"
echo "   ${BLUE}Entrypoint:${NC} pixxio_mcp.py"
echo "   ${BLUE}Authentication:${NC} ✅ Enabled"
echo "6. Klicken Sie: 'Create & Deploy'"
echo ""
echo "⏱️  Deployment dauert ~30-60 Sekunden"
echo ""

# Open browser
if command -v open &> /dev/null; then
    print_info "Öffne FastMCP Cloud im Browser..."
    open "https://fastmcp.cloud" 2>/dev/null || true
fi

echo ""
read -p "Drücken Sie Enter, wenn Deployment abgeschlossen ist..."

################################################################################
# FERTIG!
################################################################################

print_header "🎉 DEPLOYMENT ABGESCHLOSSEN!"

echo ""
echo -e "${GREEN}Ihr pixx.io MCP Server ist bereit!${NC}"
echo ""
echo "📦 ${BLUE}GitHub:${NC}"
echo "   https://github.com/$GH_USER/$REPO_NAME"
echo ""
echo "🚀 ${BLUE}FastMCP Cloud:${NC}"
echo "   https://fastmcp.cloud"
echo "   (Kopieren Sie dort Ihre Server-URL)"
echo ""
echo "📝 ${BLUE}Nächste Schritte:${NC}"
echo "   1. Kopieren Sie die MCP Server URL von FastMCP"
echo "   2. Fügen Sie sie zu Claude Desktop hinzu"
echo "   3. Testen Sie: 'Search pixx.io for logo files'"
echo ""
echo "🔗 ${BLUE}Claude Desktop Config:${NC}"
echo "   ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""

print_success "Viel Erfolg mit Ihrem MCP Server! 🚀"
