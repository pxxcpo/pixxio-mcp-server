# pixx.io MCP Server

A Model Context Protocol (MCP) server that enables Large Language Models like Claude and ChatGPT to interact with the pixx.io Digital Asset Management system.

## 🎯 Overview

This MCP server provides LLMs with tools to:
- **Search** for assets using natural language queries
- **Retrieve** detailed asset information and metadata
- **Download** assets in various formats
- **Browse** categories and collections
- **Access** EXIF data and custom metadata fields

## 🚀 Features

### Core Tools

1. **pixxio_search_assets** - Search for media assets
   - Natural language queries
   - File type filtering
   - Sorting and pagination
   - Markdown or JSON output

2. **pixxio_get_asset_details** - Get comprehensive asset information
   - Complete metadata
   - Available formats
   - Usage rights
   - Version history

3. **pixxio_get_download_url** - Generate secure download URLs
   - Original or format-specific downloads
   - Time-limited URLs
   - Multiple format support

4. **pixxio_list_categories** - Browse organization structure
   - Hierarchical category view
   - Asset counts per category
   - Collection management

5. **pixxio_get_metadata** - Extract all metadata fields
   - Standard metadata (title, keywords, description)
   - Custom organizational fields
   - EXIF data for images
   - Rights management information

## 📋 Prerequisites

- Python 3.10 or higher
- pixx.io account with API access
- pixx.io API key (available in your account settings)

## 🔧 Installation

### 1. Clone or Download

```bash
# Download the server files to your local machine
cd ~/pixxio-mcp
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python pixxio_mcp.py --help
```

You should see the MCP server help information.

## 🎮 Usage

### With Claude Desktop

1. **Configure Claude Desktop** to use the MCP server:

Edit your Claude Desktop config file (location varies by OS):
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the pixx.io MCP server:

```json
{
  "mcpServers": {
    "pixxio": {
      "command": "python",
      "args": ["/path/to/pixxio_mcp.py"]
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Start using it!** Just ask Claude:
   - "Search for product images in my pixx.io account"
   - "Find all logos uploaded in the last month"
   - "Get details about asset 12345"
   - "Show me all marketing materials in the Q4 2025 category"

### With ChatGPT (Developer Mode)

1. **Navigate to Settings** → Connectors → Advanced → Developer Mode
2. **Add MCP Server**: Run the server and connect via the URL
3. **Start using** pixx.io tools in your ChatGPT conversations

### With Other MCP Clients

The server uses standard MCP protocol and works with any MCP-compatible client:

```bash
# Run with stdio transport (default)
python pixxio_mcp.py

# Run with HTTP transport for remote access
python pixxio_mcp.py --transport http --port 8000
```

## 📚 Example Use Cases

### Marketing Manager Workflow

**Scenario**: Creating a presentation with brand assets

```
User: "I need to create a slide deck for our Q1 product launch. 
       Find our latest product images and brand logo."

Claude: [Uses pixxio_search_assets with query="product images Q1 2026"]
        [Uses pixxio_search_assets with query="brand logo"]
        
        "I found 45 product images from Q1 2026 and 3 logo variations.
        Here are the top results:
        
        Product Images:
        - product-hero-2026.jpg (2.4 MB, 3000x2000px)
        - product-detail-front.png (1.8 MB, 2500x2000px)
        ...
        
        Logos:
        - brand-logo-primary.svg (245 KB)
        - brand-logo-white.svg (238 KB)
        
        Would you like me to download these or search for specific variations?"
```

### Content Team Workflow

**Scenario**: Finding approved social media assets

```
User: "Show me all Instagram posts tagged 'approved' from the social media team"

Claude: [Uses pixxio_search_assets with query="Instagram approved social"]
        [Filters by file types: jpg, png]
        
        "Found 23 approved Instagram posts. Here are the most recent:
        
        1. instagram-product-reveal.jpg
           - Posted: 2026-02-01
           - Tags: instagram, approved, product, social
           - Size: 1.2 MB (1080x1080px)
           - Download: [link]
        
        2. instagram-team-culture.jpg
           - Posted: 2026-01-28
           ...
        
        Page 1 of 2. Would you like to see more?"
```

### Sales Team Workflow

**Scenario**: Accessing sales materials for client meeting

```
User: "Get me the latest sales presentation and case study PDFs for 
       enterprise clients"

Claude: [Uses pixxio_search_assets with query="sales presentation enterprise"]
        [Filters by file type: pdf]
        [Uses pixxio_list_categories to find sales materials category]
        
        "I found your enterprise sales materials:
        
        Presentations:
        - Enterprise-Solution-Overview-2026.pdf (4.5 MB)
        - ROI-Calculator-Presentation.pdf (2.1 MB)
        
        Case Studies:
        - Enterprise-Case-Study-TechCorp.pdf (1.8 MB)
        - Enterprise-Case-Study-GlobalInc.pdf (1.9 MB)
        
        All materials are approved and up-to-date as of Feb 2026.
        Would you like download links?"
```

## 🔒 Security & Authentication

### API Key Management

Your pixx.io API key is passed with each request and never stored by the MCP server.

**Best Practices:**
- Use environment variables for API keys in production
- Rotate API keys regularly
- Use read-only API keys where possible
- Never commit API keys to version control

### Example: Environment Variable Setup

```python
import os

# In your application or wrapper
PIXXIO_API_KEY = os.getenv("PIXXIO_API_KEY")

# Use with Claude
"Search pixx.io using API key from environment: {PIXXIO_API_KEY}"
```

## 🛠️ Development & Extension

### Adding New Tools

To add a new tool to the MCP server:

1. **Define a Pydantic input model**:
```python
class NewToolInput(BaseModel):
    api_key: str = Field(..., description="API key")
    param: str = Field(..., description="Parameter description")
```

2. **Implement the tool function**:
```python
@mcp.tool(
    name="pixxio_new_tool",
    annotations={
        "title": "Tool Title",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def new_tool(params: NewToolInput) -> str:
    """Tool description."""
    # Implementation
    pass
```

3. **Test the tool**:
```bash
python pixxio_mcp.py
# Test with MCP Inspector or your client
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest test_pixxio_mcp.py
```

## 📊 API Reference

### Tool: pixxio_search_assets

Search for assets in pixx.io.

**Parameters:**
- `api_key` (str, required): Your pixx.io API key
- `query` (str, required): Search query (e.g., "product images Q4")
- `file_types` (list, optional): Filter by extensions (e.g., ["jpg", "png"])
- `limit` (int, optional): Results per page (1-100, default 20)
- `offset` (int, optional): Pagination offset (default 0)
- `sort_by` (str, optional): Sort field (relevance, created, modified, filename, filesize)
- `sort_order` (str, optional): Direction (asc, desc)
- `response_format` (str, optional): Output format (markdown, json)

**Returns:** Formatted search results with pagination info

### Tool: pixxio_get_asset_details

Get detailed information about a specific asset.

**Parameters:**
- `api_key` (str, required): Your pixx.io API key
- `asset_id` (str, required): Unique asset identifier
- `response_format` (str, optional): Output format (markdown, json)

**Returns:** Complete asset information including metadata, formats, and usage rights

### Tool: pixxio_get_download_url

Generate a secure download URL for an asset.

**Parameters:**
- `api_key` (str, required): Your pixx.io API key
- `asset_id` (str, required): Unique asset identifier
- `format_key` (str, optional): Specific format (thumbnail, web, original)

**Returns:** JSON with download URL, expiration, and file info

### Tool: pixxio_list_categories

List all categories and collections.

**Parameters:**
- `api_key` (str, required): Your pixx.io API key
- `response_format` (str, optional): Output format (markdown, json)

**Returns:** Hierarchical category structure with asset counts

### Tool: pixxio_get_metadata

Retrieve all metadata fields for an asset.

**Parameters:**
- `api_key` (str, required): Your pixx.io API key
- `asset_id` (str, required): Unique asset identifier

**Returns:** Complete metadata including custom fields, EXIF data, and rights info

## 🚀 Deployment

### Local/Desktop Deployment

For use with Claude Desktop or local MCP clients:

```bash
# Standard stdio transport
python pixxio_mcp.py
```

### Remote/Cloud Deployment

For remote access or multiple clients:

```bash
# HTTP transport
python pixxio_mcp.py --transport streamable_http --port 8000

# Or use with a process manager
# supervisord, systemd, or PM2
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt pixxio_mcp.py ./
RUN pip install -r requirements.txt

CMD ["python", "pixxio_mcp.py", "--transport", "streamable_http", "--port", "8000"]
```

## 📝 Known Limitations

This is a **Proof of Concept** implementation. Some limitations:

1. **Mock API Endpoints**: Uses placeholder API paths that need to be adjusted to match actual pixx.io API
2. **Authentication**: Simplified authentication flow - production should use OAuth or more secure methods
3. **Rate Limiting**: No built-in rate limiting - should be added for production
4. **Caching**: No response caching - could improve performance for frequently accessed data
5. **Batch Operations**: Currently single-asset focused - batch operations would be useful
6. **Write Operations**: Read-only tools - adding upload/edit capabilities would expand functionality

## 🎯 Next Steps for Production

To make this production-ready:

1. **Verify API Endpoints**: Update all endpoint paths to match actual pixx.io API documentation
2. **Add OAuth Support**: Implement secure OAuth 2.0 authentication flow
3. **Implement Caching**: Add response caching for better performance
4. **Add Rate Limiting**: Implement request rate limiting and retry logic
5. **Expand Tools**: Add upload, edit, delete, and batch operations
6. **Add Webhooks**: Support real-time notifications for asset changes
7. **Add Tests**: Comprehensive test suite with mocked API responses
8. **Add Monitoring**: Logging, metrics, and error tracking
9. **Documentation**: API-specific documentation based on actual pixx.io API

## 🤝 Support & Feedback

This MCP server was created as a Proof of Concept for pixx.io.

**For pixx.io-specific questions:**
- Website: https://pixx.io
- API Docs: https://api.pixx.io/docs
- Support: support@pixx.io

**For MCP Protocol questions:**
- MCP Specification: https://modelcontextprotocol.io
- MCP SDK: https://github.com/modelcontextprotocol

## 📄 License

This is a proof-of-concept implementation. License terms to be determined by pixx.io.

## 🙏 Acknowledgments

- Built with the Model Context Protocol (MCP) by Anthropic
- Uses the MCP Python SDK and FastMCP framework
- Designed for pixx.io Digital Asset Management system

---

**Version**: 1.0.0-poc  
**Last Updated**: February 2026  
**Status**: Proof of Concept
