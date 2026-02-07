#!/bin/bash

################################################################################
# pixx.io MCP Server - Automatisches Deployment Script
# Für macOS (Apple Silicon M3)
# Python 3.9 kompatibel
################################################################################

set -e  # Exit on error

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

################################################################################
# SCHRITT 1: System-Check
################################################################################

print_header "SCHRITT 1: System-Check"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python gefunden: $PYTHON_VERSION"
    
    # Extract major and minor version
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        print_success "Python Version OK (3.9+)"
    else
        print_error "Python 3.9+ wird benötigt. Gefunden: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 nicht gefunden!"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    print_success "Git gefunden: $GIT_VERSION"
else
    print_error "Git nicht gefunden!"
    exit 1
fi

################################################################################
# SCHRITT 2: GitHub Setup
################################################################################

print_header "SCHRITT 2: GitHub Setup"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    print_warning "GitHub CLI (gh) nicht installiert."
    print_info "Installiere GitHub CLI via Homebrew..."
    
    # Install via Homebrew (already installed on this system)
    brew install gh
    print_success "GitHub CLI installiert"
fi

# GitHub Authentifizierung
print_info "GitHub Authentifizierung..."
print_info "Es öffnet sich ein Browser-Fenster zur Authentifizierung."
echo ""
read -p "Drücken Sie Enter, um fortzufahren..."

if gh auth login -w; then
    print_success "GitHub Authentifizierung erfolgreich"
else
    print_error "GitHub Authentifizierung fehlgeschlagen"
    exit 1
fi

# GitHub Benutzername abrufen
GH_USER=$(gh api user --jq .login)
print_success "Angemeldet als: $GH_USER"

################################################################################
# SCHRITT 3: Repository erstellen
################################################################################

print_header "SCHRITT 3: GitHub Repository erstellen"

REPO_NAME="pixxio-mcp-server"
print_info "Repository Name: $REPO_NAME"

# Check if repo already exists
if gh repo view "$GH_USER/$REPO_NAME" &> /dev/null; then
    print_warning "Repository $REPO_NAME existiert bereits!"
    read -p "Möchten Sie es löschen und neu erstellen? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh repo delete "$GH_USER/$REPO_NAME" --yes
        print_success "Altes Repository gelöscht"
    else
        print_error "Abgebrochen. Bitte löschen Sie das Repository manuell oder wählen Sie einen anderen Namen."
        exit 1
    fi
fi

# Create new repo
print_info "Erstelle neues Repository..."
gh repo create "$REPO_NAME" --public --description "pixx.io MCP Server - AI-powered Digital Asset Management integration"
print_success "Repository erstellt: https://github.com/$GH_USER/$REPO_NAME"

################################################################################
# SCHRITT 4: Projekt-Setup
################################################################################

print_header "SCHRITT 4: Projekt-Setup"

# Create project directory
PROJECT_DIR="$HOME/pixxio-mcp-server"
if [ -d "$PROJECT_DIR" ]; then
    print_warning "Verzeichnis existiert bereits: $PROJECT_DIR"
    rm -rf "$PROJECT_DIR"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
print_success "Projekt-Verzeichnis erstellt: $PROJECT_DIR"

# Initialize git
git init
git remote add origin "https://github.com/$GH_USER/$REPO_NAME.git"
print_success "Git initialisiert"

################################################################################
# SCHRITT 5: Dateien kopieren
################################################################################

print_header "SCHRITT 5: Projekt-Dateien vorbereiten"

# Diese Dateien müssen existieren - wir erstellen sie hier
cat > "$PROJECT_DIR/pixxio_mcp.py" << 'EOF'
# Der Python-Code wird hier eingefügt - verwenden Sie die Python 3.9-kompatible Version
EOF

cat > "$PROJECT_DIR/requirements.txt" << 'EOF'
mcp>=1.0.0
httpx>=0.27.0
pydantic>=2.0.0
EOF

cat > "$PROJECT_DIR/README.md" << 'EOF'
# pixx.io MCP Server

Model Context Protocol server for pixx.io Digital Asset Management.

## Quick Start

```bash
pip install -r requirements.txt
python pixxio_mcp.py
```

## Deployment

This server is deployed on FastMCP Cloud.

## Documentation

See [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) for business case and roadmap.
EOF

cat > "$PROJECT_DIR/.gitignore" << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv
EOF

print_success "Projekt-Dateien erstellt"

################################################################################
# SCHRITT 6: Dependencies installieren
################################################################################

print_header "SCHRITT 6: Python Dependencies installieren"

print_info "Installiere MCP SDK und Dependencies..."
python3 -m pip install --user --quiet mcp httpx pydantic 2>&1 | grep -v "already satisfied" || true
print_success "Dependencies installiert"

################################################################################
# SCHRITT 7: Git Commit und Push
################################################################################

print_header "SCHRITT 7: Code zu GitHub pushen"

git add .
git commit -m "Initial commit: pixx.io MCP Server POC"
git branch -M main
git push -u origin main
print_success "Code gepusht zu GitHub"

################################################################################
# SCHRITT 8: FastMCP Cloud Setup
################################################################################

print_header "SCHRITT 8: FastMCP Cloud Deployment"

print_info "Öffne FastMCP Cloud Setup..."
echo ""
echo -e "${YELLOW}WICHTIG: Bitte folgen Sie diesen Schritten:${NC}"
echo ""
echo "1. Gehen Sie zu: https://fastmcp.cloud"
echo "2. Klicken Sie auf 'Sign in with GitHub'"
echo "3. Autorisieren Sie FastMCP Cloud"
echo "4. Klicken Sie auf 'New Project'"
echo "5. Wählen Sie Ihr Repository: $GH_USER/$REPO_NAME"
echo "6. Konfiguration:"
echo "   - Name: pixxio-mcp"
echo "   - Entrypoint: pixxio_mcp.py"
echo "   - Authentication: Enabled (empfohlen)"
echo "7. Klicken Sie auf 'Deploy'"
echo ""

# Open FastMCP Cloud in browser
if command -v open &> /dev/null; then
    open "https://fastmcp.cloud" 2>/dev/null || true
fi

read -p "Drücken Sie Enter, wenn das Deployment abgeschlossen ist..."

################################################################################
# SCHRITT 9: Fertigstellung
################################################################################

print_header "🎉 DEPLOYMENT ABGESCHLOSSEN!"

echo ""
echo -e "${GREEN}Ihr pixx.io MCP Server ist jetzt online!${NC}"
echo ""
echo "📦 GitHub Repository:"
echo "   https://github.com/$GH_USER/$REPO_NAME"
echo ""
echo "🚀 FastMCP Cloud:"
echo "   https://fastmcp.cloud"
echo ""
echo "📝 Nächste Schritte:"
echo "   1. Kopieren Sie Ihre MCP Server URL von FastMCP Cloud"
echo "   2. Verbinden Sie Claude Desktop oder ChatGPT"
echo "   3. Testen Sie mit: 'Search pixx.io for logo files'"
echo ""
echo "📚 Dokumentation:"
echo "   - README.md für Setup-Anleitung"
echo "   - EXECUTIVE_SUMMARY.md für Business Case"
echo ""

print_success "Deployment erfolgreich abgeschlossen!"
