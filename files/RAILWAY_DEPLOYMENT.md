# 🚀 Railway Deployment Guide

## Quick Start (5 Minuten)

### Step 1: Railway Account erstellen
1. Gehen Sie zu https://railway.app
2. "Start a New Project" klicken
3. Mit GitHub einloggen

### Step 2: Repository deployen
1. "Deploy from GitHub repo" wählen
2. `pxxcpo/pixxio-mcp-server` Repository wählen
3. "Deploy Now" klicken

Railway erkennt automatisch:
- ✅ Python 3.11
- ✅ requirements.txt
- ✅ Procfile
- ✅ Baut und startet den Server

### Step 3: Environment Variables setzen

Im Railway Dashboard:
1. Klicken Sie auf Ihr Projekt
2. "Variables" Tab öffnen
3. Fügen Sie hinzu:

```
PIXXIO_API_KEY=ihr_pixxio_api_key
PIXXIO_BASE_URL=https://richard.px.media/api
```

4. "Save" klicken
5. Server startet automatisch neu

### Step 4: URL notieren

Railway gibt Ihnen eine URL wie:
```
https://pixxio-mcp-production.up.railway.app
```

Diese URL brauchen Sie für Claude Desktop!

---

## Claude Desktop konfigurieren

### Config-Datei öffnen:
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Server-Verbindung hinzufügen:

**Option A: HTTP-SSE (Empfohlen für Cloud)**
```json
{
  "mcpServers": {
    "pixxio": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-http-sse",
        "https://pixxio-mcp-production.up.railway.app/sse"
      ]
    }
  }
}
```

**Option B: Direct Connect (falls Option A nicht funktioniert)**
```json
{
  "mcpServers": {
    "pixxio": {
      "url": "https://pixxio-mcp-production.up.railway.app",
      "transport": "sse"
    }
  }
}
```

### Claude Desktop neu starten:
```bash
# Cmd + Q (Claude beenden)
# Claude Desktop neu öffnen
```

✅ Fertig! Der Server läuft in der Cloud!

---

## Testen

In Claude Desktop fragen:
```
Suche nach "Neubau" in pixx.io
```

Sollte funktionieren ohne lokalen Server! 🎉

---

## Logs ansehen

### In Railway Dashboard:
1. Projekt öffnen
2. "Deployments" Tab
3. Aktuelles Deployment anklicken
4. **Live Logs** sehen Sie in Echtzeit!

### Nützlich für:
- Debugging
- Performance-Monitoring
- Error-Tracking

---

## Updates deployen

### Automatisch (empfohlen):
```bash
cd ~/pixxio-mcp-server
git add .
git commit -m "Update feature"
git push
```

Railway deployed automatisch! ✅

### Manuell:
Im Railway Dashboard:
1. "Deployments" Tab
2. "Redeploy" klicken

---

## Kosten

### Railway Free Tier:
- $5 Guthaben/Monat kostenlos
- Reicht für ~500,000 Requests
- Perfekt für Testing & kleine Teams

### Wenn Sie mehr brauchen:
- Hobby Plan: $5/Monat
- Pro Plan: $20/Monat
- Transparente Preise, keine Überraschungen

---

## Für Kunden bereitstellen

### Option 1: Shared Instance (einfach)
- Ein Server für alle Kunden
- Kunden bekommen API Key
- Sie verwalten zentral

### Option 2: Pro Kunde (isoliert)
- Jeder Kunde eigener Railway-Deploy
- Volle Isolation
- Kunde verwaltet selbst

### Empfehlung für Start:
**Shared Instance** - einfacher, günstiger, reicht für die meisten

---

## Troubleshooting

### Server startet nicht?
1. Logs in Railway checken
2. Environment Variables prüfen
3. requirements.txt korrekt?

### Claude Desktop verbindet nicht?
1. URL in Config korrekt?
2. `/sse` am Ende?
3. Claude Desktop neugestartet?

### API Errors?
1. PIXXIO_API_KEY korrekt?
2. PIXXIO_BASE_URL mit `/api` am Ende?
3. API Key in pixx.io noch aktiv?

---

## Next Steps

✅ Server läuft in Cloud
✅ Claude Desktop verbunden
✅ Keine lokalen Neustarts mehr

### Jetzt:
1. Features testen
2. Für ChatGPT vorbereiten
3. Kunden-Ready machen

---

## Support

- Railway Docs: https://docs.railway.app
- FastMCP Docs: https://github.com/jlowin/fastmcp
- pixx.io API: https://pixx.io/de/developers

---

**🎉 Geschafft! Ihr MCP Server läuft in der Cloud!**
