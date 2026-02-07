#!/usr/bin/env python3
"""
pixx.io MCP Server - Complete Version
Works both locally and on FastMCP Cloud
"""

import json
from typing import Optional, List, Dict, Any
from enum import Enum

import httpx
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("pixxio_mcp")

# Configuration
DEFAULT_API_BASE = "https://api.pixx.io"
REQUEST_TIMEOUT = 30.0

# ============================================================================
# ENUMS
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for responses"""
    MARKDOWN = "markdown"
    JSON = "json"

class AssetSortBy(str, Enum):
    """Fields available for sorting assets"""
    CREATED_DATE = "created"
    MODIFIED_DATE = "modified"
    FILENAME = "filename"
    FILESIZE = "filesize"
    RELEVANCE = "relevance"

class SortOrder(str, Enum):
    """Sort direction"""
    ASC = "asc"
    DESC = "desc"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_filesize(size_bytes: int) -> str:
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def _format_asset_markdown(asset: Dict[str, Any]) -> str:
    """Format a single asset as markdown"""
    lines = [
        f"## {asset.get('originalFilename', 'Untitled Asset')}",
        f"**ID**: {asset.get('id', 'N/A')}",
        f"**Type**: {asset.get('fileType', 'unknown')}",
        f"**Size**: {_format_filesize(asset.get('fileSize', 0))}",
        f"**Created**: {asset.get('createdDate', 'N/A')}",
    ]
    
    if keywords := asset.get('keywords', []):
        lines.append(f"**Tags**: {', '.join(keywords)}")
    
    if download_url := asset.get('downloadURL'):
        lines.append(f"\n**Download**: {download_url}")
    
    return "\n".join(lines)

# ============================================================================
# API CLIENT
# ============================================================================

class PixxioAPIClient:
    """Client for pixx.io API interactions"""
    
    def __init__(self, api_key: str, base_url: str = DEFAULT_API_BASE):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the pixx.io API"""
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 401:
                    raise Exception("Authentication failed. Please check your API key.")
                elif status == 404:
                    raise Exception("Resource not found.")
                elif status == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                else:
                    raise Exception(f"API error: HTTP {status}")
                    
            except httpx.TimeoutException:
                raise Exception("Request timed out. Please try again.")
                
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")

# ============================================================================
# INPUT MODELS
# ============================================================================

class SearchAssetsInput(BaseModel):
    """Input parameters for asset search"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: str = Field(..., min_length=10, description="pixx.io API key")
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    file_types: Optional[List[str]] = Field(default=None, description="Filter by file types (e.g., ['jpg', 'png'])")
    limit: int = Field(default=20, ge=1, le=100, description="Number of results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    sort_by: AssetSortBy = Field(default=AssetSortBy.RELEVANCE, description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort direction")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetAssetDetailsInput(BaseModel):
    """Input parameters for getting asset details"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: str = Field(..., min_length=10, description="pixx.io API key")
    asset_id: str = Field(..., min_length=1, description="Asset ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetDownloadURLInput(BaseModel):
    """Input parameters for getting download URL"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: str = Field(..., min_length=10, description="pixx.io API key")
    asset_id: str = Field(..., min_length=1, description="Asset ID")
    format_id: Optional[str] = Field(default=None, description="Optional format ID for specific file version")

class ListCategoriesInput(BaseModel):
    """Input parameters for listing categories"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: str = Field(..., min_length=10, description="pixx.io API key")
    parent_id: Optional[str] = Field(default=None, description="Parent category ID (null for root)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetMetadataInput(BaseModel):
    """Input parameters for getting asset metadata"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: str = Field(..., min_length=10, description="pixx.io API key")
    asset_id: str = Field(..., min_length=1, description="Asset ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool(
    name="pixxio_search_assets",
    annotations={
        "title": "Search Assets in pixx.io",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def search_assets(params: SearchAssetsInput) -> str:
    """
    Search for media assets in pixx.io Digital Asset Management.
    
    Use this tool to find images, videos, documents, and other files stored in pixx.io.
    Supports filtering, sorting, and pagination.
    
    Args:
        params: Search parameters including query, filters, sorting, and pagination options
        
    Returns:
        Formatted search results with asset details and download links
        
    Examples:
        - Search for product images: query="product photos", file_types=["jpg", "png"]
        - Find recent documents: query="Q4 report", sort_by="modified", limit=10
        - Search with pagination: query="logo", offset=20, limit=20
    """
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        
        search_params = {
            "q": params.query,
            "limit": params.limit,
            "offset": params.offset,
            "sortBy": params.sort_by.value,
            "sortOrder": params.sort_order.value
        }
        
        if params.file_types:
            search_params["fileTypes"] = ",".join(params.file_types)
        
        response = await client.request(
            method="GET",
            endpoint="/v1/assets/search",
            params=search_params
        )
        
        assets = response.get("assets", [])
        total = response.get("total", 0)
        
        if params.response_format == ResponseFormat.JSON:
            result = {
                "total": total,
                "count": len(assets),
                "offset": params.offset,
                "assets": assets
            }
            return json.dumps(result, indent=2)
        
        # Markdown format
        lines = [
            f"# Search Results: \"{params.query}\"",
            f"\nFound {total} assets (showing {len(assets)})\n"
        ]
        
        for asset in assets:
            lines.append(_format_asset_markdown(asset))
            lines.append("\n---\n")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error searching assets: {str(e)}"

@mcp.tool(
    name="pixxio_get_asset_details",
    annotations={
        "title": "Get Asset Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def get_asset_details(params: GetAssetDetailsInput) -> str:
    """
    Get detailed information about a specific asset.
    
    Retrieves complete metadata, file information, and available formats for an asset.
    
    Args:
        params: Asset ID and response format
        
    Returns:
        Detailed asset information including metadata, dimensions, formats, and download links
    """
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        asset = await client.request(
            method="GET",
            endpoint=f"/v1/assets/{params.asset_id}"
        )
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(asset, indent=2)
        
        return _format_asset_markdown(asset)
    
    except Exception as e:
        return f"Error getting asset details: {str(e)}"

@mcp.tool(
    name="pixxio_get_download_url",
    annotations={
        "title": "Get Download URL",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def get_download_url(params: GetDownloadURLInput) -> str:
    """
    Generate a secure download URL for an asset.
    
    Creates a temporary, authenticated download link for the specified asset.
    Optionally specify a format ID for a specific file version.
    
    Args:
        params: Asset ID and optional format ID
        
    Returns:
        Secure download URL
    """
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        
        request_data = {"assetId": params.asset_id}
        if params.format_id:
            request_data["formatId"] = params.format_id
        
        response = await client.request(
            method="POST",
            endpoint="/v1/assets/download",
            data=request_data
        )
        
        download_url = response.get("downloadURL")
        if not download_url:
            return "Error: No download URL returned"
        
        return f"Download URL: {download_url}\n\nThis URL is temporary and may expire after a certain time period."
    
    except Exception as e:
        return f"Error generating download URL: {str(e)}"

@mcp.tool(
    name="pixxio_list_categories",
    annotations={
        "title": "List Categories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def list_categories(params: ListCategoriesInput) -> str:
    """
    List available categories in the pixx.io system.
    
    Categories help organize assets hierarchically. Use this to browse the category structure
    or find specific category IDs for filtered searches.
    
    Args:
        params: Optional parent category ID to list subcategories
        
    Returns:
        List of categories with their IDs and names
    """
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        
        request_params = {}
        if params.parent_id:
            request_params["parentId"] = params.parent_id
        
        response = await client.request(
            method="GET",
            endpoint="/v1/categories",
            params=request_params
        )
        
        categories = response.get("categories", [])
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({"categories": categories}, indent=2)
        
        # Markdown format
        lines = ["# Categories\n"]
        for cat in categories:
            lines.append(f"- **{cat.get('name', 'Unnamed')}** (ID: {cat.get('id', 'N/A')})")
            if desc := cat.get('description'):
                lines.append(f"  {desc}")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error listing categories: {str(e)}"

@mcp.tool(
    name="pixxio_get_metadata",
    annotations={
        "title": "Get Asset Metadata",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def get_metadata(params: GetMetadataInput) -> str:
    """
    Get detailed metadata for an asset.
    
    Retrieves EXIF data, custom metadata fields, and technical information.
    
    Args:
        params: Asset ID and response format
        
    Returns:
        Complete metadata including EXIF, custom fields, and technical details
    """
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        
        response = await client.request(
            method="GET",
            endpoint=f"/v1/assets/{params.asset_id}/metadata"
        )
        
        metadata = response.get("metadata", {})
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(metadata, indent=2)
        
        # Markdown format
        lines = [f"# Metadata for Asset {params.asset_id}\n"]
        
        for key, value in metadata.items():
            lines.append(f"**{key}**: {value}")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error getting metadata: {str(e)}"

# ============================================================================
# MAIN - For local development and testing
# ============================================================================

if __name__ == "__main__":
    # This block is used for local development
    # It will be ignored by FastMCP Cloud
    mcp.run()
