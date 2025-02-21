"""RNA Database MCP Server Implementation"""
from pathlib import Path
import sqlite3
import json
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from django.apps import apps

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    """Standard error codes for RNA Database MCP Server"""
    DATABASE_NOT_FOUND = "DATABASE_NOT_FOUND"
    DATABASE_ERROR = "DATABASE_ERROR"
    INVALID_QUERY = "INVALID_QUERY"
    SEQUENCE_NOT_FOUND = "SEQUENCE_NOT_FOUND"

def get_sequence_model():
    """Get the Sequence model, falling back to mock for standalone testing"""
    try:
        return apps.get_model('chat', 'Sequence')
    except Exception:
        from .test_standalone import MockModel
        return MockModel

class RNADatabaseServer:
    """MCP-compliant RNA database server"""
    
    def __init__(self):
        self.app = FastMCP("rna-database")
        self.db_path = str(Path(__file__).parent / "data/human_yeast_mouse.db")
        self._init_database()
        self._register_tools()

    def _init_database(self):
        """Initialize and verify database"""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

    def _register_tools(self):
        """Register available tools with the MCP server"""
        
        @self.app.tool()
        async def search_rna(
            species: str = "human",
            isotype: Optional[str] = None,
            anticodon: Optional[str] = None,
            min_general_score: Optional[float] = None,
            max_general_score: Optional[float] = None,
            min_isotype_score: Optional[float] = None,
            max_isotype_score: Optional[float] = None,
            json_field: Optional[str] = None,
            json_value: Optional[str] = None,
            sort_by: Optional[str] = None,
            order: Optional[str] = "asc",
            limit: Optional[int] = 10,
            sample: Optional[str] = None,
            context: Optional[Dict[str, str]] = None
        ) -> List[Dict[str, Any]]:
            """Search for tRNA sequences matching criteria.
            
            Args:
                species: Species to search ("human", "mouse", "yeast")
                isotype: Filter by isotype (e.g., "Ala", "Gly")
                anticodon: Filter by anticodon
                min_general_score: Minimum General_tRNA_Model_Score
                max_general_score: Maximum General_tRNA_Model_Score
                min_isotype_score: Minimum Isotype_Model_Score
                max_isotype_score: Maximum Isotype_Model_Score
                json_field: JSON field to search in overview data
                json_value: Value to match in json_field
                sort_by: Column to sort by
                order: Sort order ("asc" or "desc")
                limit: Maximum number of results to return
                sample: If "random", returns random sample
                context: Context for sequence storage
            """
            # Build query
            sql = f"SELECT * FROM {species} WHERE 1=1"
            params = []
            
            # Basic filters
            if isotype:
                sql += " AND Isotype_from_Anticodon = ?"
                params.append(isotype)
                
            if anticodon:
                sql += " AND Anticodon = ?"
                params.append(anticodon)
            
            # Score filters
            if min_general_score is not None:
                sql += " AND General_tRNA_Model_Score >= ?"
                params.append(float(min_general_score))
                
            if max_general_score is not None:
                sql += " AND General_tRNA_Model_Score <= ?"
                params.append(float(max_general_score))
                
            if min_isotype_score is not None:
                sql += " AND Isotype_Model_Score >= ?"
                params.append(float(min_isotype_score))
                
            if max_isotype_score is not None:
                sql += " AND Isotype_Model_Score <= ?"
                params.append(float(max_isotype_score))
            
            # JSON field search
            if json_field and json_value:
                sql += " AND json_extract(overview, ?) LIKE ?"
                params.append(f"$.{json_field}")
                params.append(f"%{json_value}%")
            
            # Sorting
            if sort_by:
                sql += f" ORDER BY {sort_by}"
                if order and order.lower() == "desc":
                    sql += " DESC"
                else:
                    sql += " ASC"
            
            # Random sampling
            if sample and sample.lower() == "random":
                sql += " ORDER BY RANDOM()"
            
            # Limit results
            if limit is not None:
                sql += " LIMIT ?"
                params.append(int(limit))

            # Execute query
            sequences = []
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()

                    # Process results
                    for row in rows:
                        row_dict = dict(row)
                        
                        # Store in database if context provided
                        if context:
                            Sequence = get_sequence_model()
                            sequence = await Sequence.objects.acreate(
                                user_id=context.get('user_id'),
                                chat_id=context.get('chat_id'),
                                message_id=context.get('message_id'),
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
                        
                        # Format sequence data
                        sequences.append({
                            'gene_symbol': row_dict['GtRNAdb_Gene_Symbol'],
                            'anticodon': row_dict['Anticodon'],
                            'isotype': row_dict['Isotype_from_Anticodon'],
                            'general_score': float(row_dict['General_tRNA_Model_Score']),
                            'sequences': json.loads(row_dict.get('sequences', '{}')),
                            'images': json.loads(row_dict.get('images', '{}'))
                        })

                return sequences

            except Exception as e:
                logger.error(f"Database error in search_rna: {e}")
                raise

        @self.app.tool()
        async def get_sequence(
            gene_symbol: str,
            species: str = "human",
            context: Optional[Dict[str, str]] = None
        ) -> Dict[str, Any]:
            """Get detailed information for a specific sequence."""
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(
                        f"SELECT * FROM {species} WHERE GtRNAdb_Gene_Symbol = ?",
                        [gene_symbol]
                    )
                    row = cursor.fetchone()
                    
                    if not row:
                        raise ValueError(f"No sequence found with gene symbol: {gene_symbol}")

                    row_dict = dict(row)
                    
                    # Store in database if context provided
                    if context:
                        Sequence = get_sequence_model()
                        sequence = await Sequence.objects.acreate(
                            user_id=context.get('user_id'),
                            chat_id=context.get('chat_id'),
                            message_id=context.get('message_id'),
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

                    # Return formatted sequence data
                    return {
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

            except Exception as e:
                logger.error(f"Database error in get_sequence: {e}")
                raise

    def run(self):
        """Run the MCP server"""
        self.app.run(transport='stdio')
