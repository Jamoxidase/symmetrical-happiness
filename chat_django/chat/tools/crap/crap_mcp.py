import base64
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ..rna_database.mcp import MCPRequest, MCPResponse
from .genome_browser import GenomeBrowser, GenomicRegion

logger = logging.getLogger(__name__)

@dataclass
class CrapMCP:
    """MCP interface for CRAP tool."""
    
    user_id: str
    chat_id: Optional[str]
    message_id: Optional[str]
    
    def __init__(self, user_id: str, chat_id: Optional[str] = None, message_id: Optional[str] = None):
        self.user_id = user_id
        self.chat_id = chat_id
        self.message_id = message_id
        self.browser = GenomeBrowser()
    
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process a CRAP request.
        
        Args:
            request: MCPRequest containing sequence and region data
            
        Returns:
            MCPResponse with sequence, annotated sequence, and image data
        """
            
        try:
            # Extract parameters
            params = request.params
            
            # Create region object
            region = GenomicRegion(
                genome=params.get("genome", "hg19"),
                chrom=params.get("chrom"),
                start=params.get("start"),
                end=params.get("end"),
                tracks=params.get("tracks", [])
            )
            
            # Get response from browser
            response = self.browser.view_region(region)
            
            # Process image
            image_data = None
            image_media_type = None
            filename, image_bytes = response.capture_browser_screenshot()
            if image_bytes:
                image_data = base64.b64encode(image_bytes).decode("utf-8")
                image_media_type = "image/png"  # Explicitly using allowed type
                logger.debug(f"Image media type: {image_media_type}")
                logger.debug("Image structure:")
                image_structure = {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_media_type,
                        "data": image_data[:100] + "..." # Truncate for logging
                    }
                }
                logger.debug(f"Image structure: {json.dumps(image_structure, indent=2)}")
            
            # Prepare response data
            data = {
                "sequence": response.sequence[:2000],
                "annotated_sequence": response.annotated_sequence[:2000],
                "features": [f.__dict__ for f in response.features[:50]],
                "tracks": response.tracks,
                "browser_link": response.generate_browser_link(),
                "image": {
                    "data": image_data,
                    "media_type": image_media_type
                } if image_data else None
            }
            
            return MCPResponse(
                status="success",
                data=data,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error processing CRAP request: {str(e)}")
            return MCPResponse(
                status="error",
                data=None,
                error={"message": str(e)}
            )