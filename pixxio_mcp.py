#!/usr/bin/env python3
"""
pixx.io MCP Server — Production-Ready for Cloud Deployment
Supports: Claude Desktop (stdio), ChatGPT (Streamable HTTP), Microsoft Copilot

Transport modes:
  - stdio:  For local Claude Desktop usage
  - http:   For remote cloud deployment (ChatGPT, Claude Web, Copilot)

Environment variables:
  PIXXIO_API_KEY   — API key for pixx.io authentication
  PIXXIO_BASE_URL  — Base URL of the pixx.io instance (e.g. https://yourspace.px.media)
  TRANSPORT        — "stdio" or "http" (default: "http")
  PORT             — HTTP port (default: 8000)
  HOST             — HTTP host (default: "0.0.0.0")
"""

import os
import json
import logging
from typing import Optional

import httpx
from fastmcp import FastMCP
from mcp.types import ImageContent

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pixxio-mcp")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PIXXIO_API_KEY = os.environ.get("PIXXIO_API_KEY", "")
PIXXIO_BASE_URL = os.environ.get("PIXXIO_BASE_URL", "").rstrip("/")
TRANSPORT = os.environ.get("TRANSPORT", "http").lower()
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "0.0.0.0")

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "pixx.io DAM",
    instructions=(
        "pixx.io is a Digital Asset Management (DAM) system. "
        "Use these tools to search, browse, and manage digital assets "
        "like images, videos, documents, and other media files. "
        "Assets can be organized in directories and collections, "
        "tagged with keywords, and enriched with metadata.\n\n"
        "IMAGE HANDLING STRATEGY:\n"
        "- To SHOW an image inline in the chat: use get_preview(id)\n"
        "- To get a PUBLIC URL for embedding/sharing: use get_download_url(id)\n"
        "- To DOWNLOAD a file for processing (presentations, documents): use download_asset(id)\n"
        "When a user asks to see images, use get_preview. "
        "When building documents or presentations, use download_asset to get local file paths."
    ),
)

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_client() -> httpx.AsyncClient:
    """Create an async HTTP client with pixx.io auth headers."""
    if not PIXXIO_BASE_URL:
        raise ValueError("PIXXIO_BASE_URL is not configured. Set the PIXXIO_BASE_URL environment variable.")
    if not PIXXIO_API_KEY:
        raise ValueError("PIXXIO_API_KEY is not configured. Set the PIXXIO_API_KEY environment variable.")
    return httpx.AsyncClient(
        base_url=PIXXIO_BASE_URL,
        headers={"Authorization": f"Bearer {PIXXIO_API_KEY}"},
        timeout=30.0,
    )


async def _api_get(path: str, params: Optional[dict] = None) -> dict:
    """Make a GET request to the pixx.io API."""
    async with _get_client() as client:
        resp = await client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()


async def _api_post(path: str, data: Optional[dict] = None) -> dict:
    """Make a POST request to the pixx.io API (multipart/form-data)."""
    async with _get_client() as client:
        resp = await client.post(path, data=data or {})
        resp.raise_for_status()
        return resp.json()


async def _api_put(path: str, data: Optional[dict] = None) -> dict:
    """Make a PUT request to the pixx.io API (multipart/form-data)."""
    async with _get_client() as client:
        resp = await client.put(path, data=data or {})
        resp.raise_for_status()
        return resp.json()



# ═══════════════════════════════════════════════════════════════════════════
# TOOL 1: search  (Required for ChatGPT Deep Research)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def search(
    query: str,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "uploadDate",
    sort_direction: str = "desc",
    file_type: Optional[str] = None,
    file_extension: Optional[str] = None,
    directory_id: Optional[int] = None,
    collection_id: Optional[int] = None,
) -> dict:
    """Search for assets in the pixx.io Digital Asset Management system.

    Use this tool to find images, videos, documents and other media files.
    The query searches across file names, descriptions, keywords, and metadata.

    Args:
        query: Search term to find assets (searches names, descriptions, keywords).
        page: Page number for pagination (starts at 1).
        page_size: Number of results per page (max 100).
        sort_by: Sort field — one of: uploadDate, fileName, modifyDate, createDate, rating.
        sort_direction: Sort order — "asc" or "desc".
        file_type: Optional filter by type: "image", "video", "document", "audio".
        file_extension: Optional filter by extension: "jpg", "png", "pdf", "mp4", etc.
        directory_id: Optional filter by directory ID.
        collection_id: Optional filter by collection ID.

    Returns:
        Dictionary with 'ids' (list of asset ID strings) and 'results' (list of asset summaries).
        Use the get_preview tool to view thumbnail images for specific assets.
    """
    params: dict = {
        "showFiles": "true",
        "page": page,
        "pageSize": min(page_size, 100),
        "sortBy": sort_by,
        "sortDirection": sort_direction,
        "responseFields": "id,fileName,fileExtension,fileType,previewFileURL,description,keywords,subject,rating,uploadDate,fileSize,width,height",
    }

    # Build filter
    filters = []

    if query:
        filters.append({
            "filterType": "searchTerm",
            "term": query,
            "useSynonyms": True,
        })

    if file_type:
        filters.append({
            "filterType": "fileType",
            "fileType": file_type,
        })

    if file_extension:
        filters.append({
            "filterType": "fileExtension",
            "fileExtension": file_extension,
        })

    if directory_id:
        filters.append({
            "filterType": "directory",
            "directoryID": directory_id,
            "includeSubdirectories": True,
        })

    if collection_id:
        filters.append({
            "filterType": "collection",
            "collectionID": collection_id,
        })

    if len(filters) == 1:
        params["filter"] = json.dumps(filters[0])
    elif len(filters) > 1:
        params["filter"] = json.dumps({
            "filterType": "connectorAnd",
            "filters": filters,
        })

    data = await _api_get("/api/v1/files", params)

    files = data.get("files", [])
    quantity = data.get("quantity", 0)

    # Build response compatible with ChatGPT Deep Research (ids + results)
    results = []
    ids = []
    for f in files:
        fid = str(f.get("id", ""))
        ids.append(fid)
        results.append({
            "id": fid,
            "title": f.get("fileName", ""),
            "description": f.get("description", "") or f.get("subject", ""),
            "file_type": f.get("fileType", ""),
            "file_extension": f.get("fileExtension", ""),
            "keywords": f.get("keywords", []),
            "rating": f.get("rating"),
            "preview_url": f.get("previewFileURL", ""),
            "upload_date": f.get("uploadDate", ""),
            "file_size": f.get("fileSize"),
            "dimensions": f"{f.get('width', '?')}x{f.get('height', '?')}" if f.get("width") else None,
        })

    return_data = {
        "ids": ids,
        "results": results,
        "total_results": quantity,
        "page": page,
        "page_size": page_size,
    }

    return return_data


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 2: fetch  (Required for ChatGPT Deep Research)
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def fetch(id: str) -> dict:
    """Fetch complete details for a specific asset by its ID.

    Returns all metadata, keywords, preview URLs, and file information.
    Use the get_preview tool to view the asset image inline.

    Args:
        id: The asset ID to retrieve (as returned by the search tool).

    Returns:
        Complete asset record with all available metadata.
    """
    data = await _api_get(f"/api/v1/files/{id}", {
        "responseFields": "id,fileName,fileExtension,fileType,previewFileURL,originalFileURL,description,keywords,subject,rating,uploadDate,createDate,modifyDate,fileSize,width,height,colorspace,orientation,directory,staticCollections,languageCodes,isArchived,isDownloadLocked,metadataFields,creator",
    })

    f = data.get("file", data)

    return {
        "id": str(f.get("id", id)),
        "title": f.get("fileName", ""),
        "file_name": f.get("fileName", ""),
        "file_extension": f.get("fileExtension", ""),
        "file_type": f.get("fileType", ""),
        "file_size": f.get("fileSize"),
        "description": f.get("description", ""),
        "subject": f.get("subject", ""),
        "creator": f.get("creator", ""),
        "keywords": f.get("keywords", []),
        "rating": f.get("rating"),
        "colorspace": f.get("colorspace", ""),
        "width": f.get("width"),
        "height": f.get("height"),
        "orientation": f.get("orientation", ""),
        "preview_url": f.get("previewFileURL", ""),
        "original_file_url": f.get("originalFileURL", ""),
        "create_date": f.get("createDate", ""),
        "modify_date": f.get("modifyDate", ""),
        "upload_date": f.get("uploadDate", ""),
        "directory": f.get("directory"),
        "collections": f.get("staticCollections", []),
        "language_codes": f.get("languageCodes", []),
        "is_archived": f.get("isArchived", False),
        "is_download_locked": f.get("isDownloadLocked", False),
        "metadata_fields": f.get("metadataFields"),
    }


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 3: get_download_url
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def get_download_url(
    id: int,
    download_type: str = "original",
    file_extension: Optional[str] = None,
    max_size: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: int = 90,
) -> dict:
    """Generate a publicly accessible download URL for a specific asset.

    The returned URL requires NO authentication and can be used directly by
    AI agents, embedded in documents, presentations, or shared externally.
    URLs are temporary and generated on demand.

    Supports downloading the original file or converting to different formats/sizes.

    Args:
        id: The asset ID.
        download_type: "original" (unchanged), "preview" (web-optimized), or "custom" (converted).
        file_extension: Target format for custom: "jpg", "png", "pdf", "tiff", "webp".
        max_size: Resize longest side to this pixel value (keeps aspect ratio).
        width: Target width in pixels.
        height: Target height in pixels.
        quality: JPEG quality 1-100 (default 90).

    Returns:
        Dictionary with publicly accessible download URL, file name, and file size.
    """
    params: dict = {
        "downloadType": download_type,
        "responseType": "path",
        "quality": quality,
    }
    if file_extension and download_type == "custom":
        params["fileExtension"] = file_extension
    if max_size:
        params["maxSize"] = max_size
    if width:
        params["width"] = width
    if height:
        params["height"] = height

    data = await _api_get(f"/api/v1/files/{id}/convert", params)

    return {
        "id": str(id),
        "download_url": data.get("downloadURL", data.get("path", "")),
        "file_name": data.get("fileName", ""),
        "file_extension": data.get("fileExtension", file_extension or "original"),
        "file_size": data.get("fileSize"),
        "download_type": download_type,
        "note": "This URL is publicly accessible without authentication.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 3b: get_preview
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def get_preview(
    id: str,
    width: int = 800,
) -> ImageContent:
    """Get the preview image of an asset displayed inline.

    Use this to view an asset's image directly in the chat.
    For downloading the original file, use get_download_url instead.

    Args:
        id: The asset ID.
        width: Preview width in pixels (default: 800).

    Returns:
        The preview image displayed inline.
    """
    import base64

    data = await _api_get(f"/api/v1/files/{id}", {
        "responseFields": "id,fileName,previewFileURL,width,height",
    })
    f = data.get("file", data)
    preview_url = f.get("previewFileURL", "")

    if not preview_url:
        raise ValueError(f"No preview available for asset {id}.")

    # Adjust width parameter in the preview URL
    if "&width=" in preview_url:
        preview_url = preview_url.rsplit("&width=", 1)[0] + f"&width={width}"
    elif "?" in preview_url:
        preview_url += f"&width={width}"

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers={"Authorization": f"Bearer {PIXXIO_API_KEY}"}) as client:
        resp = await client.get(preview_url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
        b64_data = base64.b64encode(resp.content).decode("utf-8")
        return ImageContent(type="image", data=b64_data, mimeType=content_type)


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 3c: download_asset
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def download_asset(
    id: int,
    download_type: str = "preview",
    file_extension: Optional[str] = None,
    max_size: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    quality: int = 90,
) -> dict:
    """Download an asset file to a temporary location for further processing.

    Use this tool when you need the actual file for tasks like:
    - Creating presentations (PPTX) with images
    - Building documents (DOCX, PDF) with embedded images
    - Image analysis or manipulation
    - Any workflow that requires a local file path

    The file is downloaded to a temporary directory and the path is returned.

    Args:
        id: The asset ID.
        download_type: "original" (unchanged), "preview" (web-optimized), or "custom" (converted).
        file_extension: Target format for custom: "jpg", "png", "pdf", "tiff", "webp".
        max_size: Resize longest side to this pixel value (keeps aspect ratio).
        width: Target width in pixels.
        height: Target height in pixels.
        quality: JPEG quality 1-100 (default 90).

    Returns:
        Dictionary with local file path, file name, size, and download URL.
    """
    import tempfile

    # First get the download URL
    params: dict = {
        "downloadType": download_type,
        "responseType": "path",
        "quality": quality,
    }
    if file_extension and download_type == "custom":
        params["fileExtension"] = file_extension
    if max_size:
        params["maxSize"] = max_size
    if width:
        params["width"] = width
    if height:
        params["height"] = height

    data = await _api_get(f"/api/v1/files/{id}/convert", params)
    download_url = data.get("downloadURL", "")
    file_name = data.get("fileName", f"asset_{id}")
    ext = data.get("fileExtension", "jpg")

    if not download_url:
        raise ValueError(f"Could not generate download URL for asset {id}.")

    # Download the file
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(download_url)
        resp.raise_for_status()

        # Save to temp directory
        tmp_dir = tempfile.mkdtemp(prefix="pixxio_")
        file_path = os.path.join(tmp_dir, f"{file_name}.{ext}")
        with open(file_path, "wb") as f:
            f.write(resp.content)

    return {
        "id": str(id),
        "file_path": file_path,
        "file_name": f"{file_name}.{ext}",
        "file_size": len(resp.content),
        "download_url": download_url,
        "note": "File downloaded to temporary location. Use file_path for further processing.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 4: list_directories
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def list_directories(
    parent_id: Optional[int] = None,
    show_tree: bool = False,
) -> dict:
    """List directories (folders) in the pixx.io DAM.

    Browse the folder structure or find a specific directory
    before searching for files within it.

    Args:
        parent_id: ID of the parent directory. Omit for root level.
        show_tree: If True, returns the full directory tree.

    Returns:
        List of directories with IDs, names, paths, and file counts.
    """
    if show_tree:
        data = await _api_get("/api/v1/directories/tree")
    else:
        params: dict = {}
        if parent_id:
            params["parentID"] = parent_id
        data = await _api_get("/api/v1/directories", params)

    dirs = data.get("directories", data.get("tree", []))

    def _format_dir(d: dict) -> dict:
        result = {
            "id": d.get("id"),
            "name": d.get("name", ""),
            "path": d.get("path", ""),
            "has_children": d.get("hasChildren", False),
            "file_count": d.get("quantity", 0),
        }
        if d.get("children"):
            result["children"] = [_format_dir(c) for c in d["children"]]
        return result

    return {
        "directories": [_format_dir(d) for d in dirs] if isinstance(dirs, list) else dirs,
    }


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 5: list_collections
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def list_collections(
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """List all collections in the pixx.io DAM.

    Collections are curated groups of assets (like albums or lightboxes).

    Args:
        page: Page number (starts at 1).
        page_size: Results per page (max 100).

    Returns:
        List of collections with IDs, names, descriptions, and file counts.
    """
    params = {
        "page": page,
        "pageSize": min(page_size, 100),
    }
    data = await _api_get("/api/v1/collections", params)

    collections = data.get("collections", [])

    return {
        "collections": [
            {
                "id": c.get("id"),
                "name": c.get("name", ""),
                "description": c.get("description", ""),
                "is_dynamic": c.get("isDynamic", False),
                "file_count": c.get("filesQuantity", 0),
                "create_date": c.get("createDate", ""),
            }
            for c in collections
        ],
        "total": data.get("quantity", len(collections)),
    }


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 6: get_keywords
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def get_keywords(
    query: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> dict:
    """List keywords (tags) used across assets in the DAM.

    Args:
        query: Optional search term to filter keywords.
        page: Page number.
        page_size: Results per page.

    Returns:
        List of keywords with usage counts.
    """
    params: dict = {
        "page": page,
        "pageSize": min(page_size, 100),
    }
    if query:
        params["filter"] = query

    data = await _api_get("/api/v1/keywords", params)

    return {
        "keywords": data.get("keywords", []),
        "total": data.get("quantity", 0),
    }


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 7: update_asset
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def update_asset(
    ids: list[int],
    description: Optional[str] = None,
    subject: Optional[str] = None,
    rating: Optional[int] = None,
    keywords_to_add: Optional[list[str]] = None,
    keywords_to_remove: Optional[list[str]] = None,
    directory_id: Optional[int] = None,
) -> dict:
    """Update metadata for one or more assets.

    Args:
        ids: List of asset IDs to update.
        description: New description text.
        subject: New subject/title text.
        rating: Rating value (0-5).
        keywords_to_add: Keywords to add.
        keywords_to_remove: Keywords to remove.
        directory_id: Move asset(s) to this directory.

    Returns:
        Confirmation of the update.
    """
    form_data: dict = {
        "ids": json.dumps(ids),
    }
    if description is not None:
        form_data["description"] = description
    if subject is not None:
        form_data["subject"] = subject
    if rating is not None:
        form_data["rating"] = str(rating)
    if keywords_to_add:
        form_data["keywordsToAdd"] = json.dumps(keywords_to_add)
    if keywords_to_remove:
        form_data["keywordsToRemove"] = json.dumps(keywords_to_remove)
    if directory_id:
        form_data["directoryID"] = str(directory_id)

    data = await _api_put("/api/v1/files", form_data)

    return {
        "success": data.get("success", False),
        "updated_ids": ids,
        "message": f"Successfully updated {len(ids)} asset(s).",
    }


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 8: get_metadata_fields
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def get_metadata_fields() -> dict:
    """List all available metadata fields configured in the DAM.

    Returns:
        Dictionary of metadata field definitions.
    """
    fields = await _api_get("/api/v1/metadataFields")
    return {"metadata_fields": fields.get("metadataFields", fields)}


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 9: get_download_formats
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool(annotations={"readOnlyHint": True})
async def get_download_formats() -> dict:
    """List configured download formats (conversion presets).

    Download formats are pre-configured conversion settings like
    "Web JPG 1200px" or "Print TIFF CMYK".

    Returns:
        List of download formats with their settings.
    """
    data = await _api_get("/api/v1/downloadFormats")
    return {"download_formats": data.get("downloadFormats", [])}


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 10: create_collection
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_collection(
    name: str,
    description: str = "",
    file_ids: Optional[list[int]] = None,
) -> dict:
    """Create a new static collection (album/lightbox) in the DAM.

    Args:
        name: Name of the new collection.
        description: Optional description.
        file_ids: Optional list of asset IDs to include.

    Returns:
        The ID of the newly created collection.
    """
    form_data: dict = {"name": name, "description": description}
    if file_ids:
        form_data["fileIDs"] = json.dumps(file_ids)

    data = await _api_post("/api/v1/collections", form_data)

    return {
        "success": data.get("success", False),
        "collection_id": data.get("id"),
        "name": name,
    }


# ═══════════════════════════════════════════════════════════════════════════
# TOOL 11: create_external_share
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
async def create_external_share(
    name: str,
    file_ids: list[int],
    allow_download: bool = True,
    recipients: Optional[list[dict]] = None,
) -> dict:
    """Create an external share link for assets.

    Allows people outside the organization to view/download assets via a link.

    Args:
        name: Name/title for the share.
        file_ids: List of asset IDs to share.
        allow_download: Whether recipients can download files.
        recipients: Optional list of recipients [{"email": "...", "language": "en"}].

    Returns:
        Share details including the share URL.
    """
    form_data: dict = {
        "name": name,
        "fileIDs": json.dumps(file_ids),
        "allowDownload": json.dumps(allow_download),
    }
    if recipients:
        form_data["recipients"] = json.dumps(recipients)

    data = await _api_post("/api/v1/externalShares", form_data)

    return {
        "success": data.get("success", False),
        "share_id": data.get("id"),
        "share_url": data.get("url", ""),
        "name": name,
        "file_count": len(file_ids),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Health check endpoint
# ═══════════════════════════════════════════════════════════════════════════

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for deployment monitoring."""
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "ok",
        "server": "pixx.io MCP Server",
        "transport": TRANSPORT,
        "pixxio_configured": bool(PIXXIO_BASE_URL and PIXXIO_API_KEY),
    })


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info(f"Starting pixx.io MCP Server (transport={TRANSPORT})")
    logger.info(f"pixx.io instance: {PIXXIO_BASE_URL or 'NOT CONFIGURED'}")
    logger.info(f"API key: {'configured' if PIXXIO_API_KEY else 'NOT CONFIGURED'}")

    if TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        logger.info(f"HTTP server on {HOST}:{PORT}")
        logger.info(f"MCP endpoint: http://{HOST}:{PORT}/mcp")
        logger.info(f"Health check: http://{HOST}:{PORT}/health")
        mcp.run(transport="http", host=HOST, port=PORT, stateless_http=True)
