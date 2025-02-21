"""MCP-compliant RNA Database Server Implementation"""
import asyncio
from pathlib import Path
import sqlite3
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from mcp.server import Server
import mcp.types as types
from django.apps import apps

logger = logging.getLogger(__name__)

def get_sequence_model():
    """Get the Sequence model, falling back to mock for standalone testing"""
    try:
        return apps.get_model('chat', 'Sequence')
    except Exception:
        from .test_standalone import MockModel
        return MockModel

class RNADatabaseServer:
    """MCP-compliant RNA database server.
    
    Implements Model Context Protocol (MCP) 1.2.0 specification for accessing
    tRNA sequence data through standardized tools and resources.
    """
    
    def __init__(self):
        """Initialize the RNA Database MCP Server"""
        self.app = Server(
            "rna-database",
            capabilities={
                "tools": {
                    "search_rna": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "species": {
                                    "type": "string",
                                    "description": "Species to search: 'human' (H. sapiens), 'mouse' (M. musculus), or 'yeast' (S. cerevisiae)",
                                    "default": "human"
                                },
                                "isotype": {
                                    "type": "string",
                                    "description": "Filter by isotype (e.g. SeC, Ala)"
                                },
                                "anticodon": {
                                    "type": "string",
                                    "description": "Filter by anticodon"
                                },
                                "min_score": {
                                    "type": "number",
                                    "description": "Minimum general model score"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return (default: 5, max: 15)",
                                    "default": 5,
                                    "minimum": 1,
                                    "maximum": 15
                                }
                            }
                        }
                    },
                    "get_sequence": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "gene_symbol": {
                                    "type": "string",
                                    "description": "GtRNAdb Gene Symbol to look up"
                                }
                            },
                            "required": ["gene_symbol"]
                        }
                    }
                }
            }
        )
        self.db_path = str(Path(__file__).parent / "data/human_yeast_mouse.db")
        self._register_handlers()
        logger.info("RNA Database MCP Server initialized")

    def _register_handlers(self):
        """Register MCP protocol handlers"""
        # Verify database exists
        if not Path(self.db_path).exists():
            raise types.McpError(
                code="DATABASE_NOT_FOUND",
                message=f"Database not found at {self.db_path}"
            )
                    code="DATABASE_NOT_FOUND",
                    message=f"Database not found at {self.db_path}"
                )
            
            # Return capabilities
            return types.InitializeResult(
                capabilities={
                    "tools": {
                        "search_rna": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "species": {
                                        "type": "string",
                                        "description": "Species to search: 'human' (H. sapiens), 'mouse' (M. musculus), or 'yeast' (S. cerevisiae)",
                                        "default": "human"
                                    },
                                    "isotype": {
                                        "type": "string",
                                        "description": "Filter by isotype (e.g. SeC, Ala)"
                                    },
                                    "anticodon": {
                                        "type": "string",
                                        "description": "Filter by anticodon"
                                    },
                                    "min_score": {
                                        "type": "number",
                                        "description": "Minimum general model score"
                                    }
                                }
                            }
                        },
                        "get_sequence": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "gene_symbol": {
                                        "type": "string",
                                        "description": "GtRNAdb Gene Symbol to look up"
                                    }
                                },
                                "required": ["gene_symbol"]
                            }
                        }
                    }
                }
            )

        @self.app.list_tools()
        async def list_tools() -> List[types.Tool]:
            """Handle tool listing request"""
            logger.info("Handling tool listing request")
            return [
                types.Tool(
                    name="search_rna",
                    description="Search for tRNA sequences",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "species": {
                                "type": "string",
                                "description": "Species to search: 'human' (H. sapiens), 'mouse' (M. musculus), or 'yeast' (S. cerevisiae)",
                                "default": "human"
                            },
                            "isotype": {
                                "type": "string",
                                "description": "Filter by isotype (e.g. SeC, Ala)"
                            },
                            "anticodon": {
                                "type": "string",
                                "description": "Filter by anticodon"
                            },
                            "min_score": {
                                "type": "number",
                                "description": "Minimum general model score"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="get_sequence",
                    description="Get detailed sequence information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "gene_symbol": {
                                "type": "string",
                                "description": "GtRNAdb Gene Symbol to look up"
                            }
                        },
                        "required": ["gene_symbol"]
                    }
                )
            ]

        @self.app.call_tool()
        async def call_tool(
            name: str,
            arguments: Dict[str, Any]
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Handle tool execution request"""
            logger.info(f"Handling tool call: {name} with args {arguments}")
            
            try:
                if name == "search_rna":
                    return await self._handle_search_rna(arguments)
                elif name == "get_sequence":
                    return await self._handle_get_sequence(arguments)
                else:
                    raise types.McpError(
                        code="UNKNOWN_TOOL",
                        message=f"Unknown tool: {name}"
                    )
            except sqlite3.Error as e:
                raise types.McpError(
                    code="DATABASE_ERROR",
                    message=str(e)
                )
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                raise

    async def _handle_search_rna(
        self,
        arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle search_rna tool execution"""
        # Build query with enforced safety limit
        MAX_RESULTS = 10  # Absolute maximum for safety
        DEFAULT_LIMIT = 5  # Default number of results
        
        species = arguments.get('species', 'human').lower()
        if species not in {'human', 'yeast', 'mouse'}:
            species = 'human'
            
        # Get requested limit but ALWAYS enforce MAX_RESULTS
        try:
            requested_limit = int(arguments.get('limit', DEFAULT_LIMIT))
        except (ValueError, TypeError):
            requested_limit = DEFAULT_LIMIT
            logger.warning(f"Invalid limit value in arguments: {arguments.get('limit')}. Using default of {DEFAULT_LIMIT}")
        
        # Never exceed MAX_RESULTS regardless of what was requested
        final_limit = min(requested_limit, MAX_RESULTS)
        logger.info(f"Using limit of {final_limit} (requested: {requested_limit}, max allowed: {MAX_RESULTS})")
            
        sql = f"SELECT * FROM {species} WHERE 1=1"
        params = []
        
        if arguments.get('isotype'):
            sql += " AND Isotype_from_Anticodon = ?"
            params.append(arguments['isotype'])
            
        if arguments.get('anticodon'):
            sql += " AND Anticodon = ?"
            params.append(arguments['anticodon'])
            
        if arguments.get('min_score') is not None:
            sql += " AND General_tRNA_Model_Score >= ?"
            params.append(float(arguments['min_score']))

        # Execute query
        sequences = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # ALWAYS enforce the limit
            sql += " LIMIT ?"
            params.append(final_limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            logger.info(f"Retrieved {len(rows)} sequences (enforced limit: {final_limit})")

            # Process results
            for i, row in enumerate(rows):
                # Report progress
                if i % 10 == 0:  # Report every 10 sequences
                    self.app.request_context.session.send_notification(
                        "$/progress",
                        {
                            "message": f"Processing sequence {i+1}/{total_rows}",
                            "percentage": (i + 1) / total_rows
                        }
                    )
                    
                row_dict = dict(row)
                
                # Log available fields and image data
                logger.debug(f"Available fields: {list(row_dict.keys())}")
                if 'images' in row_dict:
                    logger.debug(f"Raw images data: {row_dict['images'][:100]}...")  # First 100 chars
                
                # Store in database if context provided
                if arguments.get('context'):
                    Sequence = get_sequence_model()
                    sequence = await Sequence.objects.acreate(
                        user_id=arguments['context'].get('user_id'),
                        chat_id=arguments['context'].get('chat_id'),
                        message_id=arguments['context'].get('message_id'),
                        gene_symbol=row_dict['GtRNAdb_Gene_Symbol'],
                        anticodon=row_dict['Anticodon'],
                        isotype=row_dict['Isotype_from_Anticodon'],
                        general_score=float(row_dict['General_tRNA_Model_Score']),
                        isotype_score=float(row_dict['Isotype_Model_Score']),
                        model_agreement=str(row_dict['Anticodon_and_Isotype_Model_Agreement']).lower() == 'true',
                        features=row_dict.get('Features', ''),
                        locus=row_dict.get('Locus', ''),
                        sequences=json.loads(row_dict.get('sequences', '{}')),
                        overview=json.loads(row_dict.get('overview', '{}')),
                        images=json.loads(row_dict.get('images', '{}'))
                    )
                    logger.debug(f"Stored sequence {sequence.id} in database")
                
                # Format sequence data
                sequences.append({
                    'gene_symbol': row_dict['GtRNAdb_Gene_Symbol'],
                    'anticodon': row_dict['Anticodon'],
                    'isotype': row_dict['Isotype_from_Anticodon'],
                    'general_score': float(row_dict['General_tRNA_Model_Score']),
                    'sequences': json.loads(row_dict.get('sequences', '{}')),
                    'images': json.loads(row_dict.get('images', '{}')),
                })

        return [types.TextContent(
            type="text",
            text=json.dumps(sequences, indent=2)
        )]

    async def _handle_get_sequence(
        self,
        arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle get_sequence tool execution"""
        gene_symbol = arguments['gene_symbol']
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {arguments.get('species', 'human').lower()} WHERE GtRNAdb_Gene_Symbol = ?",
                [gene_symbol]
            )
            row = cursor.fetchone()
            
            if not row:
                raise types.McpError(
                    code="SEQUENCE_NOT_FOUND",
                    message=f"No sequence found with gene symbol: {gene_symbol}"
                )

            row_dict = dict(row)
            
            # Store in database if context provided
            if arguments.get('context'):
                Sequence = get_sequence_model()
                sequence = await Sequence.objects.acreate(
                    user_id=arguments['context'].get('user_id'),
                    chat_id=arguments['context'].get('chat_id'),
                    message_id=arguments['context'].get('message_id'),
                    gene_symbol=row_dict['GtRNAdb_Gene_Symbol'],
                    anticodon=row_dict['Anticodon'],
                    isotype=row_dict['Isotype_from_Anticodon'],
                    general_score=float(row_dict['General_tRNA_Model_Score']),
                    isotype_score=float(row_dict['Isotype_Model_Score']),
                    model_agreement=str(row_dict['Anticodon_and_Isotype_Model_Agreement']).lower() == 'true',
                    features=row_dict.get('Features', ''),
                    locus=row_dict.get('Locus', ''),
                    sequences=json.loads(row_dict.get('sequences', '{}')),
                    overview=json.loads(row_dict.get('overview', '{}'))
                )
                logger.debug(f"Stored sequence {sequence.id} in database")

            # Format sequence data
            result = {
                'gene_symbol': row_dict['GtRNAdb_Gene_Symbol'],
                'anticodon': row_dict['Anticodon'],
                'isotype': row_dict['Isotype_from_Anticodon'],
                'general_score': float(row_dict['General_tRNA_Model_Score']),
                'isotype_score': float(row_dict['Isotype_Model_Score']),
                'model_agreement': str(row_dict['Anticodon_and_Isotype_Model_Agreement']).lower() == 'true',
                'features': row_dict.get('Features', ''),
                'locus': row_dict.get('Locus', ''),
                'sequences': json.loads(row_dict.get('sequences', '{}')),
                'overview': json.loads(row_dict.get('overview', '{}')),
                'images': json.loads(row_dict.get('images', '{}'))
            }

            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting RNA Database MCP Server")
        async with self.app.run() as session:
            await session.wait_until_exit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = RNADatabaseServer()
    asyncio.run(server.run())