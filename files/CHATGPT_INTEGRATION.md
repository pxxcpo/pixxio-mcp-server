# 🤖 ChatGPT Integration Guide

## Übersicht

Nach dem Railway-Deployment können Sie pixx.io auch für **ChatGPT** bereitstellen!

---

## Architektur

```
ChatGPT → Custom GPT mit Actions → Railway MCP Server → pixx.io API
```

---

## Step-by-Step

### 1. OpenAPI Spec generieren

Der MCP Server muss als REST API exponiert werden für ChatGPT:

```python
# Wird automatisch von FastMCP bereitgestellt
# Endpoint: https://your-server.railway.app/openapi.json
```

### 2. Custom GPT erstellen

1. Gehen Sie zu https://chat.openai.com
2. Klicken Sie auf Ihren Namen → "My GPTs"
3. "Create a GPT" klicken

### 3. GPT konfigurieren

**Name:**
```
pixx.io Asset Manager
```

**Description:**
```
Search and download assets from pixx.io Digital Asset Management
```

**Instructions:**
```
You are a helpful assistant that helps users search and manage their digital assets in pixx.io. You can:

- Search for files by keywords
- Get detailed file information
- Download files in various formats
- Filter by file type

Always ask for clarification if the user's request is ambiguous.
```

### 4. Actions hinzufügen

1. "Create new action" klicken
2. "Import from URL" wählen
3. URL eingeben:
```
https://pixxio-mcp-production.up.railway.app/openapi.json
```

### 5. Authentication konfigurieren

**Authentication Type:** API Key

**API Key:**
```
Header name: Authorization
Value: Bearer YOUR_PIXXIO_API_KEY
```

### 6. Testen

In ChatGPT fragen:
```
Suche nach "Logo" Dateien in pixx.io
```

---

## Alternative: ChatGPT Plugin

Für öffentliche Distribution:

### 1. Plugin Manifest erstellen

```json
{
  "schema_version": "v1",
  "name_for_human": "pixx.io",
  "name_for_model": "pixxio",
  "description_for_human": "Search and manage digital assets in pixx.io",
  "description_for_model": "Search for files, get file details, and download assets from pixx.io Digital Asset Management system.",
  "auth": {
    "type": "user_http",
    "authorization_type": "bearer"
  },
  "api": {
    "type": "openapi",
    "url": "https://pixxio-mcp-production.up.railway.app/openapi.json"
  },
  "logo_url": "https://your-domain.com/logo.png",
  "contact_email": "support@yourcompany.com",
  "legal_info_url": "https://your-domain.com/legal"
}
```

### 2. Plugin einreichen

Bei OpenAI über das Plugin Developer Portal

---

## Für Kunden bereitstellen

### Option 1: Custom GPT teilen
- Sie erstellen Custom GPT
- Kunden fügen ihren API Key hinzu
- Einfachste Lösung

### Option 2: Eigenes Plugin
- Professioneller
- Öffentlich im ChatGPT Plugin Store
- Braucht Review von OpenAI

---

## Kosten

- **Custom GPT:** Kostenlos mit ChatGPT Plus ($20/Monat)
- **Plugin:** Kostenlos nach Approval
- **Server:** Railway Kosten (siehe RAILWAY_DEPLOYMENT.md)

---

## Next Steps

1. ✅ Railway Server läuft
2. ✅ Claude Desktop verbunden
3. 🔄 Custom GPT erstellen
4. 🔄 Testen
5. 🔄 Kunden bereitstellen

---

**Hinweis:** ChatGPT Actions sind aktuell nur für ChatGPT Plus/Team/Enterprise verfügbar.
