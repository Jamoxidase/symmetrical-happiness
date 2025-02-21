from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import json
import sqlite3
from pathlib import Path
import logging
# Lazy load models to prevent circular imports
from django.apps import apps

def get_sequence_model():
    try:
        return apps.get_model('chat', 'Sequence')
    except Exception:
        # For standalone testing
        from .test_standalone import MockModel
        return MockModel

logger = logging.getLogger(__name__)

@dataclass
class MCPRequest:
    """MCP-style request format"""
    method: str
    params: Dict[str, Any]

@dataclass
class MCPResponse:
    """MCP-style response format"""
    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

class RNADatabaseMCP:
    """MCP-style RNA database tool that maintains Django chat module compatibility.
    
    This tool requires a complete chat context (user_id, chat_id, and message_id) to ensure
    all data can be properly associated with specific messages in the chat history."""
    
    def __init__(self, user_id: str, chat_id: str, message_id: str):
        """Initialize with chat context and database path
        
        Args:
            user_id: ID of current user
            chat_id: Chat session ID
            message_id: Message ID for data association
        """
        self.user_id = user_id
        self.chat_id = chat_id
        self.message_id = message_id
        
        # Use default database path
        self.db_path = str(Path(__file__).parent / "data/human_yeast_mouse.db")
        self.capabilities = {
            "search": {
                "species": ["human", "yeast", "mouse"],
                "fields": ["isotype", "anticodon", "score"]
            },
            "data_types": {
                "sequences": "List[Dict]",
                "metadata": "Dict"
            }
        }
        self.valid_species = {"human", "yeast", "mouse"}
        self.species_display_names = {
            "human": "Human (Homo sapiens)",
            "yeast": "Yeast (Saccharomyces cerevisiae)",
            "mouse": "Mouse (Mus musculus)"
        }
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database connection"""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

    async def search_rna(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Original interface required by chat module
        
        Args:
            query: GET_TRNA format query string
            
        Returns:
            Tuple of (species, list of results)
        """
        # Parse GET_TRNA format into MCP request
        params = {}
        parts = query.split()
        for part in parts[1:]:
            if ':' in part:
                key, value = part.split(':', 1)
                value = value.strip('"')
                # Core parameters
                if key == 'search_term':
                    params['search_term'] = value
                elif key == 'Isotype_from_Anticodon':
                    params['isotype'] = value
                elif key == 'Anticodon':
                    params['anticodon'] = value
                elif key == 'species':
                    params['species'] = value
                
                # Score parameters
                elif key == 'General_tRNA_Model_Score_min':
                    params['min_general_score'] = float(value)
                elif key == 'General_tRNA_Model_Score_max':
                    params['max_general_score'] = float(value)
                elif key == 'Isotype_Model_Score_min':
                    params['min_isotype_score'] = float(value)
                elif key == 'Isotype_Model_Score_max':
                    params['max_isotype_score'] = float(value)
                
                # JSON field search
                elif key == 'json_field':
                    params['json_field'] = value
                elif key == 'json_value':
                    params['json_value'] = value
                
                # Sorting and limiting
                elif key == 'sort_by':
                    params['sort_by'] = value
                elif key == 'order':
                    params['order'] = value.lower()  # normalize to lowercase
                elif key == 'limit':
                    params['limit'] = int(value)
                elif key == 'sample':
                    params['sample'] = value.lower()  # normalize to lowercase

        # Add context from instance variables
        params["context"] = {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "message_id": self.message_id
        }

        # Create MCP request
        request = MCPRequest(
            method="search_rna",
            params=params
        )
        
        # Process through MCP interface
        response = await self.process_request(request)
        
        if response.status == "success" and "sequences" in response.data:
            species = params.get('species', 'human').lower()
            if species not in self.valid_species:
                species = 'human'
            return species, response.data["sequences"]
        else:
            return "human", []  # Default to human on error

    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process an MCP-style request
        
        Args:
            request: The MCP request containing method, params, and context
            
        Returns:
            MCPResponse with results or error
        """
        # Always use instance variables as base context
        context = {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "message_id": self.message_id
        }
        # Add any additional context from request
        context.update(request.params.get("context", {}))
        # Process the request
        try:
            if request.method == "get_capabilities":
                return MCPResponse(
                    status="success",
                    data={"capabilities": self.capabilities}
                )

            elif request.method == "search_rna":
                return await self._handle_search(request.params, context)

            elif request.method == "get_sequence":
                return await self._handle_get_sequence(request.params, context)

            else:
                return MCPResponse(
                    status="error",
                    error={
                        "code": "INVALID_METHOD",
                        "message": f"Unknown method: {request.method}"
                    }
                )

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return MCPResponse(
                status="error",
                error={
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            )

    async def _handle_search(self, params: Dict[str, Any], context: Dict[str, Any]) -> MCPResponse:
        """Handle RNA search requests"""
        try:
            # Get species from parameters
            species = params.get('species', 'human').lower()
            if species not in self.valid_species:
                logger.warning(f"Invalid species '{species}'. Defaulting to human.")
                species = 'human'
            
            # Build query
            sql = f"SELECT * FROM {species} WHERE 1=1"
            sql_params = []
            
            logger.info(f"Querying {self.species_display_names[species]} tRNA database")
            
            # Basic filters
            if 'search_term' in params:
                # Search in both isotype and gene symbol
                sql += " AND (Isotype_from_Anticodon LIKE ? OR GtRNAdb_Gene_Symbol LIKE ?)"
                search_pattern = f"%{params['search_term']}%"
                sql_params.extend([search_pattern, search_pattern])
            
            if 'isotype' in params:
                sql += " AND Isotype_from_Anticodon = ?"
                sql_params.append(params['isotype'])
                
            if 'anticodon' in params:
                sql += " AND Anticodon = ?"
                sql_params.append(params['anticodon'])
            
            # Score filters - handle as TEXT fields with numeric comparison
            if 'min_general_score' in params:
                sql += " AND CAST(General_tRNA_Model_Score AS FLOAT) >= ?"
                sql_params.append(float(params['min_general_score']))
                
            if 'max_general_score' in params:
                sql += " AND CAST(General_tRNA_Model_Score AS FLOAT) <= ?"
                sql_params.append(float(params['max_general_score']))
                
            if 'min_isotype_score' in params:
                sql += " AND CAST(Isotype_Model_Score AS FLOAT) >= ?"
                sql_params.append(float(params['min_isotype_score']))
                
            if 'max_isotype_score' in params:
                sql += " AND CAST(Isotype_Model_Score AS FLOAT) <= ?"
                sql_params.append(float(params['max_isotype_score']))
            
            # JSON field search in overview TEXT field
            if 'json_field' in params and 'json_value' in params:
                # Since overview is TEXT containing JSON, we need to parse it
                
                if params['json_field'] == "Known Modifications (Modomics)":
                    # First ensure overview is valid JSON
                    sql += " AND json_valid(overview)"
                    # Extract the Known Modifications field and do exact string matching
                    sql += " AND json_extract(overview, '%Known Modifications (Modomics)%) = ?"
                    sql_params.append(params['json_value'])
            
            # Sorting
            if 'sort_by' in params:
                sql += f" ORDER BY {params['sort_by']}"
                if params.get('order', '').lower() == 'desc':
                    sql += " DESC"
                else:
                    sql += " ASC"
            
            # Random sampling
            if params.get('sample', '').lower() == 'random':
                sql += " ORDER BY RANDOM()"
            
            # Limit results
            if 'limit' in params:
                sql += " LIMIT ?"
                sql_params.append(int(params['limit']))
            else:
                sql += " LIMIT 10"  # Default limit

            # Query SQLite
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, sql_params)
                rows = cursor.fetchall()

            # Process results and store in PostgreSQL
            sequences = []
            for row in rows:
                # Convert SQLite row to dict
                row_dict = dict(row)
                
                # Store in PostgreSQL
                Sequence = get_sequence_model()
                sequence = await Sequence.objects.acreate(
                    user_id=context['user_id'],
                    chat_id=context['chat_id'],
                    message_id=context['message_id'],
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
                
                sequences.append({
                    'id': str(sequence.id),
                    'gene_symbol': sequence.gene_symbol,
                    'anticodon': sequence.anticodon,
                    'isotype': sequence.isotype,
                    'general_score': sequence.general_score,
                    'isotype_score': sequence.isotype_score,
                    'model_agreement': sequence.model_agreement,
                    'features': sequence.features,
                    'locus': sequence.locus,
                    'sequences': sequence.sequences,
                    'overview': sequence.overview,
                    'images': sequence.images,
                })

            return MCPResponse(
                status="success",
                data={
                    "sequences": sequences,
                    "metadata": {
                        "count": len(sequences),
                        "query": params
                    }
                }
            )

        except Exception as e:
            logger.error(f"Search error: {e}")
            return MCPResponse(
                status="error",
                error={
                    "code": "SEARCH_ERROR",
                    "message": str(e)
                }
            )

    async def _handle_get_sequence(self, params: Dict[str, Any], context: Dict[str, Any]) -> MCPResponse:
        """Handle sequence detail requests"""
        try:
            gene_symbol = params.get('gene_symbol')
            if not gene_symbol:
                return MCPResponse(
                    status="error",
                    error={
                        "code": "MISSING_PARAM",
                        "message": "gene_symbol parameter is required"
                    }
                )

            # Query SQLite for full details
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Get species from parameters
                species = params.get('species', 'human').lower()
                if species not in self.valid_species:
                    logger.warning(f"Invalid species '{species}'. Defaulting to human.")
                    species = 'human'
                
                logger.info(f"Querying {self.species_display_names[species]} tRNA database")
                cursor.execute(
                    f"SELECT * FROM {species} WHERE GtRNAdb_Gene_Symbol = ?",
                    [gene_symbol]
                )
                row = cursor.fetchone()
                
                if not row:
                    return MCPResponse(
                        status="error",
                        error={
                            "code": "NOT_FOUND",
                            "message": f"No sequence found with gene symbol: {gene_symbol}"
                        }
                    )

                row_dict = dict(row)
                
                # Store in PostgreSQL
                Sequence = get_sequence_model()
                sequence = await Sequence.objects.acreate(
                    user_id=context['user_id'],
                    chat_id=context['chat_id'],
                    message_id=context['message_id'],
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

                return MCPResponse(
                    status="success",
                    data={
                        "sequence": {
                            'id': str(sequence.id),
                            'gene_symbol': sequence.gene_symbol,
                            'anticodon': sequence.anticodon,
                            'isotype': sequence.isotype,
                            'general_score': sequence.general_score,
                            'isotype_score': sequence.isotype_score,
                            'model_agreement': sequence.model_agreement,
                            'features': sequence.features,
                            'locus': sequence.locus,
                            'sequences': sequence.sequences,
                            'overview': sequence.overview
                        }
                    }
                )

        except Exception as e:
            logger.error(f"Get sequence error: {e}")
            return MCPResponse(
                status="error",
                error={
                    "code": "GET_SEQUENCE_ERROR",
                    "message": str(e)
                }
            )