#!/usr/bin/env python3
"""
pixx.io MCP Server - Production Ready
Fully integrated with pixx.io REST API v1
"""

import json
import os
from typing import Optional, List, Dict, Any
from enum import Enum

import httpx
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("pixxio_mcp")

# Configuration
DEFAULT_API_KEY = os.environ.get("PIXXIO_API_KEY", "")
DEFAULT_API_BASE = os.environ.get("PIXXIO_BASE_URL", "https://richard.px.media/api")
REQUEST_TIMEOUT = 30.0

# ============================================================================
# ENUMS
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for responses"""
    MARKDOWN = "markdown"
    JSON = "json"

class SortBy(str, Enum):
    """Sort options for file search"""
    UPLOAD_DATE = "uploadDate"
    MODIFY_DATE = "modifyDate"
    CREATE_DATE = "createDate"
    FILE_NAME = "fileName"
    FILE_SIZE = "fileSize"

class SortDirection(str, Enum):
    """Sort direction"""
    ASC = "asc"
    DESC = "desc"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_filesize(size_bytes: int) -> str:
    """Convert bytes to human-readable format"""
    if not size_bytes:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def _get_api_key(provided_key: Optional[str]) -> str:
    """Get API key from provided parameter or environment variable"""
    api_key = provided_key or DEFAULT_API_KEY
    if not api_key:
        raise ValueError(
            "No API key provided. Either pass api_key parameter or set PIXXIO_API_KEY environment variable."
        )
    return api_key

def _format_asset_markdown(file: Dict[str, Any]) -> str:
    """Format a single file/asset as markdown"""
    lines = [
        f"## {file.get('fileName', 'Untitled')}",
        f"**ID**: {file.get('id', 'N/A')}",
    ]
    
    if file_type := file.get('fileType'):
        lines.append(f"**Type**: {file_type}")
    
    if file_size := file.get('fileSize'):
        lines.append(f"**Size**: {_format_filesize(file_size)}")
    
    if upload_date := file.get('uploadDate'):
        lines.append(f"**Uploaded**: {upload_date}")
    
    if description := file.get('description'):
        lines.append(f"**Description**: {description}")
    
    if keywords := file.get('keywords'):
        if isinstance(keywords, list):
            lines.append(f"**Keywords**: {', '.join(keywords)}")
    
    # Download link (using the original file format)
    if file_id := file.get('id'):
        lines.append(f"\n**File ID for download**: {file_id}")
    
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
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('errorMessage', f'HTTP {status}')
                    error_code = error_data.get('errorCode', 'N/A')
                    # Include full error for debugging
                    raise Exception(f"API error (code {error_code}): {error_msg} | Full response: {error_data}")
                except json.JSONDecodeError:
                    raise Exception(f"HTTP {status}: {e.response.text[:200]}")
                
                if status == 401:
                    raise Exception(f"Authentication failed: {error_msg}")
                elif status == 404:
                    raise Exception(f"Resource not found: {error_msg}")
                elif status == 429:
                    raise Exception(f"Rate limit exceeded: {error_msg}")
                else:
                    raise Exception(f"API error: {error_msg}")
                    
            except httpx.TimeoutException:
                raise Exception("Request timed out. Please try again.")
                
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")

# ============================================================================
# INPUT MODELS
# ============================================================================

class SearchFilesInput(BaseModel):
    """Input parameters for file search"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: Optional[str] = Field(default=None, min_length=10, description="pixx.io API key (optional if set in environment)")
    query: str = Field(..., min_length=1, max_length=500, description="Search query - searches in filename, description, and keywords")
    file_types: Optional[List[str]] = Field(default=None, description="Filter by file extensions (e.g., ['jpg', 'png', 'pdf'])")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=500, description="Results per page")
    sort_by: SortBy = Field(default=SortBy.UPLOAD_DATE, description="Sort field")
    sort_direction: SortDirection = Field(default=SortDirection.DESC, description="Sort direction")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

class GetFileDetailsInput(BaseModel):
    """Input parameters for getting file details"""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    api_key: Optional[str] = Field(default=None, min_length=10, description="pixx.io API key (optional if set in environment)")
    file_id: int = Field(..., ge=1, description="File ID")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format")

# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool(
    name="pixxio_search_files",
    annotations={
        "title": "Search Files in pixx.io",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def search_files(params: SearchFilesInput) -> str:
    """
    Search for files in pixx.io Digital Asset Management.
    
    Searches across filenames, descriptions, and keywords.
    Supports filtering by file type, pagination, and sorting.
    
    Args:
        params: Search parameters including query, filters, sorting, and pagination
        
    Returns:
        Formatted search results with file details
        
    Examples:
        - Search for images: query="logo", file_types=["jpg", "png"]
        - Find documents: query="report", file_types=["pdf", "docx"]
        - Search by keyword: query="Neubau"
    """
    try:
        api_key = _get_api_key(params.api_key)
        client = PixxioAPIClient(api_key=api_key)
        
        # Build search filter using pixx.io's filter structure
        search_filter = {
            "filterType": "searchTerm",
            "term": params.query,
            "exactMatch": False,
            "useSynonyms": True,
            "inverted": False
        }
        
        # If file types specified, combine with file extension filter
        if params.file_types:
            filters = [search_filter]
            for file_type in params.file_types:
                filters.append({
                    "filterType": "fileExtension",
                    "fileExtension": file_type.lower(),
                    "inverted": False
                })
            
            # Wrap in connector if multiple filters
            if len(filters) > 1:
                search_filter = {
                    "filterType": "connectorAnd",
                    "filters": filters,
                    "inverted": False
                }
        
        # Build request parameters
        request_params = {
            "page": params.page,
            "pageSize": params.page_size,
            "sortBy": params.sort_by.value,
            "sortDirection": params.sort_direction.value,
            "showFiles": True
        }
        
        # Note: httpx will automatically JSON-encode dict values in params
        # pixx.io expects the filter as a JSON string in the query parameter
        request_params["filter"] = json.dumps(search_filter)
        
        response = await client.request(
            method="GET",
            endpoint="/v1/files",
            params=request_params
        )
        
        files = response.get("files", [])
        total = response.get("totalNumberOfFiles", 0)
        
        if params.response_format == ResponseFormat.JSON:
            result = {
                "total": total,
                "count": len(files),
                "page": params.page,
                "page_size": params.page_size,
                "files": files
            }
            return json.dumps(result, indent=2)
        
        # Markdown format
        lines = [
            f"# Search Results: \"{params.query}\"",
            f"\nFound {total} files (showing {len(files)} on page {params.page})\n"
        ]
        
        if not files:
            lines.append("No files found matching your search criteria.")
        else:
            for file in files:
                lines.append(_format_asset_markdown(file))
                lines.append("\n---\n")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error searching files: {str(e)}"

@mcp.tool(
    name="pixxio_get_file_details",
    annotations={
        "title": "Get File Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def get_file_details(params: GetFileDetailsInput) -> str:
    """
    Get detailed information about a specific file.
    
    Retrieves complete metadata, file information, and download links.
    
    Args:
        params: File ID and response format
        
    Returns:
        Detailed file information including metadata and download options
    """
    try:
        api_key = _get_api_key(params.api_key)
        client = PixxioAPIClient(api_key=api_key)
        
        response = await client.request(
            method="GET",
            endpoint=f"/v1/files/{params.file_id}"
        )
        
        file = response.get("file", {})
        
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(file, indent=2)
        
        return _format_asset_markdown(file)
    
    except Exception as e:
        return f"Error getting file details: {str(e)}"

# ============================================================================
# MAIN - For local development and testing
# ============================================================================

if __name__ == "__main__":
    # This block is used for local development
    # It will be ignored by FastMCP Cloud
    mcp.run()
