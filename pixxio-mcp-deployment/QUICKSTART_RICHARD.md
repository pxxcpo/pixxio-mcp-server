# ⚡ SCHNELLSTART - Für Ihr System

**Ihr Setup:**
- ✅ MacBook Air M3
- ✅ Homebrew 5.0.13 (installiert)
- ✅ Git 2.39.5 (installiert)  
- ✅ Python 3.9.6 (installiert)

**Alles bereit! Los geht's in 3 Befehlen:**

---

## 🚀 Los geht's (5 Minuten):

### 1. Terminal öffnen
**Cmd + Space** → "Terminal" → **Enter**

### 2. Diese Befehle kopieren & ausführen:

```bash
# Ins Downloads-Verzeichnis wechseln
cd ~/Downloads

# Script ausführbar machen
chmod +x deploy_pixxio_mcp.sh

# Deployment starten
./deploy_pixxio_mcp.sh
```

---

## 📝 Was passiert dann:

### ✅ Automatisch:
1. System-Check (Python, Git - alles OK bei Ihnen!)
2. GitHub CLI Installation (via Homebrew)
3. Repository erstellen
4. Code hochladen

### 👆 Sie klicken nur hier:

**A. GitHub Login (Browser öffnet sich):**
```
→ Klick: "Authorize GitHub CLI"
→ Ggf. GitHub-Passwort eingeben
→ Fertig!
```

**B. FastMCP Cloud (Browser öffnet sich):**
```
→ Klick: "Sign in with GitHub"
→ Klick: "Authorize FastMCP"
→ Klick: "New Project"
→ Repo wählen: "pixxio-mcp-server"
→ Klick: "Create & Deploy"
```

**C. Zurück ins Terminal:**
```
→ Enter drücken
```

---

## 🎉 Fertig!

Sie sehen dann:
```
✅ Deployment erfolgreich abgeschlossen!

Ihre Server-URL:
https://pixxio-mcp-abc123.fastmcp.cloud
```

---

## 🔗 Nächster Schritt: Mit Claude verbinden

```bash
# Claude Config öffnen
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Fügen Sie ein:
```json
{
  "mcpServers": {
    "pixxio": {
      "type": "mcp",
      "server_url": "https://pixxio-mcp-abc123.fastmcp.cloud"
    }
  }
}
```

**Claude Desktop neu starten** → Fertig!

---

## 🧪 Testen

In Claude Desktop:
```
Search pixx.io for "logo" using API key: [IHR_API_KEY]
```

---

**Geschätzte Gesamtzeit: 5-7 Minuten** ⏱️

**Bereit? Terminal öffnen und los! 🚀**
