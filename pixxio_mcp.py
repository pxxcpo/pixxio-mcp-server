#!/usr/bin/env python3
"""
pixx.io MCP Server - Python 3.9 Compatible Version

A Model Context Protocol server that enables LLMs to interact with the pixx.io
Digital Asset Management API. This version is compatible with Python 3.9+.

Author: Created for pixx.io CEO/CPO as a Proof of Concept
Date: February 2026
Python: 3.9+ compatible
"""

import json
import asyncio
from typing import Optional, List, Dict, Any, Union
from enum import Enum

# Python 3.9 compatible imports
try:
    import httpx
    from pydantic import BaseModel, Field, field_validator, ConfigDict
    from mcp.server.fastmcp import FastMCP, Context
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Installing required packages...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "mcp", "httpx", "pydantic"])
    print("Dependencies installed. Please run the script again.")
    sys.exit(0)

# Initialize MCP server
mcp = FastMCP("pixxio_mcp")

# =============================================================================
# Configuration and Constants
# =============================================================================

# Base URL for pixx.io API - will be configured per customer
DEFAULT_API_BASE = "https://api.pixx.io"

# API client timeout configuration
REQUEST_TIMEOUT = 30.0

# =============================================================================
# Enums for Response Formatting
# =============================================================================

class ResponseFormat(str, Enum):
    """Output format options for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"

class AssetSortBy(str, Enum):
    """Sorting options for asset listings."""
    CREATED_DATE = "created"
    MODIFIED_DATE = "modified"
    FILENAME = "filename"
    FILESIZE = "filesize"
    RELEVANCE = "relevance"

class SortOrder(str, Enum):
    """Sort direction."""
    ASC = "asc"
    DESC = "desc"

# =============================================================================
# Helper Classes and Utilities
# =============================================================================

class PixxioAPIClient:
    """
    Centralized API client for pixx.io requests.
    Handles authentication, error handling, and common request patterns.
    """
    
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
        """Make authenticated API request to pixx.io."""
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
                error_detail = _format_api_error(e)
                raise Exception(error_detail)
            except httpx.TimeoutException:
                raise Exception("Error: Request to pixx.io API timed out. Please try again.")
            except Exception as e:
                raise Exception(f"Error: Unexpected error during API request: {str(e)}")


def _format_api_error(e: httpx.HTTPStatusError) -> str:
    """Format HTTP errors into actionable error messages."""
    status = e.response.status_code
    
    if status == 400:
        return "Error: Invalid request parameters. Please check your input and try again."
    elif status == 401:
        return "Error: Authentication failed. Please verify your API key is correct and has not expired."
    elif status == 403:
        return "Error: Access denied. Your API key does not have permission for this operation."
    elif status == 404:
        return "Error: Resource not found. Please verify the asset ID or search parameters."
    elif status == 429:
        return "Error: Rate limit exceeded. Please wait a moment before making more requests."
    elif status >= 500:
        return f"Error: pixx.io API server error (HTTP {status}). Please try again later."
    else:
        return f"Error: API request failed with HTTP status {status}."


def _format_asset_markdown(asset: Dict[str, Any]) -> str:
    """Format a single asset as readable Markdown."""
    lines = [
        f"## {asset.get('originalFilename', 'Untitled Asset')}",
        f"**ID**: {asset.get('id', 'N/A')}",
        f"**Type**: {asset.get('fileType', 'unknown')}",
        f"**Size**: {_format_filesize(asset.get('fileSize', 0))}",
        f"**Created**: {asset.get('createdDate', 'N/A')}",
        f"**Modified**: {asset.get('modifiedDate', 'N/A')}",
    ]
    
    if keywords := asset.get('keywords', []):
        lines.append(f"**Tags**: {', '.join(keywords)}")
    
    if description := asset.get('description'):
        lines.append(f"\n**Description**: {description}")
    
    if download_url := asset.get('downloadURL'):
        lines.append(f"\n**Download**: {download_url}")
    
    return "\n".join(lines)


def _format_filesize(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


# =============================================================================
# Pydantic Input Models (Python 3.9 compatible)
# =============================================================================

class SearchAssetsInput(BaseModel):
    """Input parameters for searching assets in pixx.io."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    api_key: str = Field(
        ...,
        description="Your pixx.io API key for authentication",
        min_length=10
    )
    query: str = Field(
        ...,
        description="Search query to find assets (e.g., 'product images', 'logo', 'Q4 2025')",
        min_length=1,
        max_length=500
    )
    file_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by file types (e.g., ['jpg', 'png', 'pdf'])"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of results to return (1-100)",
        ge=1,
        le=100
    )
    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0
    )
    sort_by: AssetSortBy = Field(
        default=AssetSortBy.RELEVANCE,
        description="Field to sort results by"
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort direction"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for readable or 'json' for structured data"
    )


class GetAssetDetailsInput(BaseModel):
    """Input parameters for retrieving detailed asset information."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    api_key: str = Field(..., description="Your pixx.io API key", min_length=10)
    asset_id: str = Field(..., description="Unique identifier of the asset", min_length=1)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class DownloadAssetInput(BaseModel):
    """Input parameters for generating asset download URLs."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    api_key: str = Field(..., description="Your pixx.io API key", min_length=10)
    asset_id: str = Field(..., description="Asset identifier", min_length=1)
    format_key: Optional[str] = Field(
        default=None,
        description="Specific format/size (e.g., 'thumbnail', 'web', 'original')"
    )


class ListCategoriesInput(BaseModel):
    """Input parameters for listing available categories."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    api_key: str = Field(..., description="Your pixx.io API key", min_length=10)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class GetAssetMetadataInput(BaseModel):
    """Input parameters for retrieving asset metadata."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    api_key: str = Field(..., description="Your pixx.io API key", min_length=10)
    asset_id: str = Field(..., description="Asset identifier", min_length=1)


# =============================================================================
# MCP Tools Implementation
# =============================================================================

@mcp.tool(
    name="pixxio_search_assets",
    annotations={
        "title": "Search Assets in pixx.io",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def search_assets(params: SearchAssetsInput) -> str:
    """
    Search for media assets in pixx.io Digital Asset Management system.
    
    Use natural language queries to find images, videos, documents and other
    digital assets. Results include metadata, download links, and pagination.
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
                "has_more": total > params.offset + len(assets),
                "next_offset": params.offset + len(assets) if total > params.offset + len(assets) else None,
                "assets": assets
            }
            return json.dumps(result, indent=2)
        
        else:
            lines = [
                f"# Search Results: \"{params.query}\"",
                "",
                f"Found {total} assets (showing {len(assets)})",
                ""
            ]
            
            for asset in assets:
                lines.append(_format_asset_markdown(asset))
                lines.append("\n---\n")
            
            if total > params.offset + len(assets):
                current_page = (params.offset // params.limit) + 1
                total_pages = (total + params.limit - 1) // params.limit
                next_offset = params.offset + len(assets)
                lines.append(f"Page {current_page} of {total_pages} | Next offset: {next_offset}")
            else:
                lines.append("(End of results)")
            
            return "\n".join(lines)
    
    except Exception as e:
        return f"Error searching assets: {str(e)}"


@mcp.tool(
    name="pixxio_get_asset_details",
    annotations={
        "title": "Get Detailed Asset Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_asset_details(params: GetAssetDetailsInput) -> str:
    """Get comprehensive details for a specific asset including metadata, formats, and usage rights."""
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        asset = await client.request(method="GET", endpoint=f"/v1/assets/{params.asset_id}")
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(asset, indent=2)
        
        lines = [
            f"## {asset.get('originalFilename', 'Untitled Asset')}",
            "",
            f"**Asset ID**: {asset.get('id', 'N/A')}",
            f"**File Type**: {asset.get('fileType', 'unknown')}",
            f"**Size**: {_format_filesize(asset.get('fileSize', 0))}",
        ]
        
        if dimensions := asset.get('dimensions'):
            width = dimensions.get('width', 0)
            height = dimensions.get('height', 0)
            lines.append(f"**Dimensions**: {width}x{height}px")
        
        lines.extend([
            "",
            f"**Created**: {asset.get('createdDate', 'N/A')}",
            f"**Modified**: {asset.get('modifiedDate', 'N/A')}",
            ""
        ])
        
        if categories := asset.get('categories', []):
            lines.append(f"**Categories**: {', '.join(categories)}")
        
        if keywords := asset.get('keywords', []):
            lines.append(f"**Tags**: {', '.join(keywords)}")
        
        if description := asset.get('description'):
            lines.extend(["", "**Description**:", description, ""])
        
        if formats := asset.get('formats', {}):
            lines.extend(["", "**Available Formats**:"])
            for format_name, format_url in formats.items():
                lines.append(f"- {format_name}: {format_url}")
        
        if rights := asset.get('usageRights'):
            lines.extend(["", f"**Usage Rights**: {rights}"])
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error retrieving asset details: {str(e)}"


@mcp.tool(
    name="pixxio_get_download_url",
    annotations={
        "title": "Get Asset Download URL",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_download_url(params: DownloadAssetInput) -> str:
    """Generate a secure download URL for a specific asset."""
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        
        download_params = {"assetId": params.asset_id}
        if params.format_key:
            download_params["format"] = params.format_key
        
        response = await client.request(
            method="POST",
            endpoint="/v1/assets/download",
            data=download_params
        )
        
        return json.dumps(response, indent=2)
    
    except Exception as e:
        return f"Error generating download URL: {str(e)}"


@mcp.tool(
    name="pixxio_list_categories",
    annotations={
        "title": "List Available Categories/Collections",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_categories(params: ListCategoriesInput) -> str:
    """List all available categories and collections in pixx.io."""
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        categories = await client.request(method="GET", endpoint="/v1/categories")
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(categories, indent=2)
        
        lines = ["# pixx.io Categories", ""]
        
        def format_category(cat: Dict[str, Any], level: int = 0) -> List[str]:
            indent = "  " * level
            prefix = "- " if level > 0 else "## "
            
            cat_lines = [
                f"{indent}{prefix}{cat.get('name', 'Unnamed')} (ID: {cat.get('id', 'N/A')})"
            ]
            
            if asset_count := cat.get('assetCount'):
                cat_lines[0] += f" - {asset_count} assets"
            
            if description := cat.get('description'):
                cat_lines.append(f"{indent}  {description}")
            
            if subcategories := cat.get('subcategories', []):
                for subcat in subcategories:
                    cat_lines.extend(format_category(subcat, level + 1))
            
            return cat_lines
        
        for category in categories.get('categories', []):
            lines.extend(format_category(category))
            lines.append("")
        
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
        "openWorldHint": False
    }
)
async def get_metadata(params: GetAssetMetadataInput) -> str:
    """Retrieve all metadata fields for a specific asset."""
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        metadata = await client.request(
            method="GET",
            endpoint=f"/v1/assets/{params.asset_id}/metadata"
        )
        
        return json.dumps(metadata, indent=2)
    
    except Exception as e:
        return f"Error retrieving metadata: {str(e)}"


# =============================================================================
# Server Entry Point
# =============================================================================

if __name__ == "__main__":
    # Run MCP server with stdio transport
    mcp.run()
