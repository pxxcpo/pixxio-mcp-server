# ✅ Deployment Checklist

## 🎯 Ziel
pixx.io MCP Server in der Cloud deployen - **keine lokalen Neustarts mehr!**

---

## Phase 1: Railway Setup (10 Minuten)

### ☐ 1.1 Railway Account
- [ ] Gehe zu https://railway.app
- [ ] "Start a New Project"
- [ ] Mit GitHub einloggen

### ☐ 1.2 Repository verbinden
- [ ] "Deploy from GitHub repo"
- [ ] `pxxcpo/pixxio-mcp-server` wählen
- [ ] "Deploy Now"

### ☐ 1.3 Environment Variables setzen
- [ ] Im Dashboard: "Variables" Tab
- [ ] Hinzufügen:
  ```
  PIXXIO_API_KEY=ihr_key_hier
  PIXXIO_BASE_URL=https://richard.px.media/api
  ```
- [ ] "Save" → Server startet neu

### ☐ 1.4 URL notieren
- [ ] Railway URL kopieren (z.B. `https://pixxio-mcp-xxx.up.railway.app`)

**✅ Server läuft jetzt in der Cloud!**

---

## Phase 2: Claude Desktop Verbindung (5 Minuten)

### ☐ 2.1 Config-Datei öffnen
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### ☐ 2.2 Server hinzufügen
```json
{
  "mcpServers": {
    "pixxio": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-http-sse",
        "https://ihre-railway-url.up.railway.app/sse"
      ]
    }
  }
}
```

### ☐ 2.3 Claude Desktop neu starten
- [ ] Cmd + Q (beenden)
- [ ] Claude Desktop neu öffnen

### ☐ 2.4 Testen
- [ ] In Claude fragen: "Suche nach Neubau in pixx.io"
- [ ] Sollte funktionieren! 🎉

**✅ Keine lokalen Neustarts mehr nötig!**

---

## Phase 3: Development Workflow (laufend)

### Wenn ich (Claude) Features hinzufüge:

1. **Code ändern** → Ich pushe zu GitHub
2. **Railway deployed automatisch** → 30 Sekunden
3. **Sie testen sofort** → In Claude Desktop
4. **Kein Neustart nötig** → Server in Cloud

### Workflow-Beispiel:
```
Claude: "Ich füge Batch-Download hinzu"
  ↓
Git Push → Railway Build → Live in 30s
  ↓
Sie: "Lade 10 Bilder herunter" → Funktioniert sofort!
```

**✅ Entwicklung wie Cloud-SaaS!**

---

## Phase 4: Für Kunden vorbereiten (später)

### ☐ 4.1 Multi-Tenancy
- [ ] API Key pro Kunde
- [ ] Rate Limiting
- [ ] Usage Analytics

### ☐ 4.2 ChatGPT Integration
- [ ] OpenAPI Spec generieren
- [ ] Custom GPT erstellen
- [ ] Testen

### ☐ 4.3 Dokumentation
- [ ] Kunden-Onboarding-Guide
- [ ] API-Dokumentation
- [ ] Support-Prozess

---

## Monitoring & Maintenance

### Logs ansehen:
1. Railway Dashboard → "Deployments"
2. Aktuelles Deployment → "View Logs"
3. **Live Logs** in Echtzeit!

### Performance checken:
- Railway zeigt CPU/Memory/Network
- Alerts bei Problemen
- Auto-Restart bei Crashes

### Updates:
- Git push → Auto-Deploy
- Rollback mit 1 Klick
- Zero-Downtime Deployments

---

## Kosten-Übersicht

### Railway:
- **Free Tier:** $5/Monat Guthaben (kostenlos)
- **Hobby:** $5/Monat (für mehr Nutzung)
- **Pro:** $20/Monat (für Production)

### Empfehlung:
- Start: Free Tier (reicht!)
- Production: Hobby Plan

### Ihre MCP Server Nutzung:
- 1000 Requests/Tag = ~$0.50/Monat
- Sehr günstig!

---

## Troubleshooting

### Server startet nicht?
1. [ ] Logs in Railway checken
2. [ ] Environment Variables korrekt?
3. [ ] Python Version = 3.11?

### Claude verbindet nicht?
1. [ ] URL mit `/sse` am Ende?
2. [ ] Claude Desktop neugestartet?
3. [ ] Railway Server läuft (grün)?

### API Fehler?
1. [ ] PIXXIO_API_KEY korrekt?
2. [ ] PIXXIO_BASE_URL mit `/api`?
3. [ ] In pixx.io: API Key aktiv?

---

## Success Criteria

### ✅ Phase 1 erfolgreich wenn:
- [ ] Railway Dashboard zeigt "Running" (grün)
- [ ] Logs zeigen "Server started"
- [ ] URL ist erreichbar

### ✅ Phase 2 erfolgreich wenn:
- [ ] Claude Desktop zeigt pixx.io Tools
- [ ] Suche funktioniert
- [ ] Download funktioniert

### ✅ Phase 3 erfolgreich wenn:
- [ ] Code-Changes live gehen ohne lokale Änderungen
- [ ] Keine Claude Desktop Neustarts nötig
- [ ] Entwicklung schnell & effizient

---

## 🎉 Finale

Nach diesem Setup haben Sie:

✅ **Cloud-hosted MCP Server** - läuft 24/7
✅ **Keine lokalen Probleme** - kein Neustart, keine Permission-Issues
✅ **Schnelle Development** - Code → Push → Live in 30s
✅ **Production-Ready** - bereit für Kunden
✅ **Multi-Client Support** - Claude, ChatGPT, Copilot

**Sie sind bereit für das nächste Level! 🚀**

---

## Next Steps

1. [ ] Phase 1 abschließen (Railway)
2. [ ] Phase 2 abschließen (Claude Desktop)
3. [ ] Basis-Features testen
4. [ ] Neue Features entwickeln (mit mir!)
5. [ ] ChatGPT Integration vorbereiten
6. [ ] Ersten Kunden onboarden

**Los geht's! 💪**
