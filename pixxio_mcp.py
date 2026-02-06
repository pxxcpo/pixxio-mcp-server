#!/usr/bin/env python3
"""
pixx.io MCP Server - FastMCP Cloud Compatible
Optimized for FastMCP Cloud deployment
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

# Enums
class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"

class AssetSortBy(str, Enum):
    CREATED_DATE = "created"
    MODIFIED_DATE = "modified"
    FILENAME = "filename"
    FILESIZE = "filesize"
    RELEVANCE = "relevance"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

# Helper functions
def _format_filesize(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def _format_asset_markdown(asset: Dict[str, Any]) -> str:
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

# API Client
class PixxioAPIClient:
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
                    raise Exception("Authentication failed. Check your API key.")
                elif status == 404:
                    raise Exception("Resource not found.")
                else:
                    raise Exception(f"API error: HTTP {status}")
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")

# Input Models
class SearchAssetsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: str = Field(..., min_length=10)
    query: str = Field(..., min_length=1, max_length=500)
    file_types: Optional[List[str]] = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: AssetSortBy = Field(default=AssetSortBy.RELEVANCE)
    sort_order: SortOrder = Field(default=SortOrder.DESC)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)

class GetAssetDetailsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: str = Field(..., min_length=10)
    asset_id: str = Field(..., min_length=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)

# Tools
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
    
    Args:
        params: Search parameters including query, filters, and pagination
        
    Returns:
        Formatted search results with asset details and download links
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
        
        lines = [
            f"# Search Results: \"{params.query}\"",
            f"\nFound {total} assets (showing {len(assets)})\n"
        ]
        
        for asset in assets:
            lines.append(_format_asset_markdown(asset))
            lines.append("\n---\n")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error: {str(e)}"

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
    """Get detailed information about a specific asset."""
    try:
        client = PixxioAPIClient(api_key=params.api_key)
        asset = await client.request(method="GET", endpoint=f"/v1/assets/{params.asset_id}")
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(asset, indent=2)
        
        return _format_asset_markdown(asset)
    
    except Exception as e:
        return f"Error: {str(e)}"

# Export the mcp instance for FastMCP Cloud
__all__ = ['mcp']
