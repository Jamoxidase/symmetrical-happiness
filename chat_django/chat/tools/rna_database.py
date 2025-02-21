import json
import sqlite3
import logging
import re
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum
from django.db.models import Q, F
from asgiref.sync import sync_to_async
from ..models import Sequence
import os

logger = logging.getLogger(__name__)

class SortOrder(Enum):
    ASC = "ASC"
    DESC = "DESC"

@dataclass
class RNAQueryParams:
    """Structure to hold RNA query parameters"""
    species: str = "human"
    search_terms: Dict[str, str] = None     # Column-value pairs for exact matching
    numeric_filters: Dict[str, Dict[str, float]] = None  # Column: {min/max values}
    overview_field: Optional[str] = None    # JSON field in overview to search
    overview_value: Optional[str] = None    # Value to match in overview field
    sort_by: Optional[str] = None
    sort_order: Optional[SortOrder] = None
    limit: Optional[int] = None

    def __post_init__(self):
        if self.search_terms is None:
            self.search_terms = {}
        if self.numeric_filters is None:
            self.numeric_filters = {}

class RNADatabaseTool:
    """Tool for reading from SQLite GTRNAdb and storing in PostgreSQL."""
    
    def __init__(self, user_id: str, chat_id: Optional[str] = None, message_id: Optional[str] = None):
        """Initialize the database tool.
        
        Args:
            user_id: ID of the current user
            chat_id: Optional chat ID for context
            message_id: Optional message ID for context
        """
        # Get path relative to this file
        current_dir = os.path.dirname(__file__)
        self.db_path = os.path.join(current_dir, "rna_database", "data", "human_yeast_mouse.db")
        logger.info(f"Current directory: {current_dir}")
        logger.info(f"Looking for database at: {self.db_path}")
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
            
        self.user_id = user_id
        self.chat_id = chat_id
        self.message_id = message_id
        
        # Set up valid fields and types
        self.valid_species = {"human", "yeast", "mouse"}
        self.species_display_names = {
            "human": "Human (Homo sapiens)",
            "yeast": "Yeast (Saccharomyces cerevisiae)",
            "mouse": "Mouse (Mus musculus)"
        }
        self.numerical_columns = {
            "General_tRNA_Model_Score",
            "Isotype_Model_Score"
        }
        self.json_columns = {
            "overview",
            "sequences",
            "variants",
            "images",
            "expression_profiles"
        }
        self.searchable_columns = {
            "GtRNAdb_Gene_Symbol",
            "tRNAscan_SE_ID",
            "Locus",
            "Anticodon",
            "Isotype_from_Anticodon",
            "General_tRNA_Model_Score",
            "Best_Isotype_Model",
            "Isotype_Model_Score",
            "Anticodon_and_Isotype_Model_Agreement",
            "Features"
        }
        
        # Set up logging
        self.log_dir = Path.cwd() / "logs" / "GtRNAdb"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.query_log = self.log_dir / f"query_log_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
        
    async def search_rna(self, query: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Search for tRNA sequences based on query.
        
        Args:
            query: Search query in format "GET_TRNA species:X Isotype_from_Anticodon:Y"
            
        Returns:
            Tuple of (species, list of results)
        """
        # Parse query parameters
        params = {}
        parts = query.split()
        for part in parts[1:]:  # Skip "GET_TRNA"
            if ':' in part:
                key, value = part.split(':', 1)
                # Remove quotes if present
                value = value.strip('"')
                params[key] = value
        
        try:
            # Get species from parameters or default to human
            species = params.get('species', 'human').lower()
            if species not in self.valid_species:
                logger.warning(f"Invalid species '{species}'. Defaulting to human.")
                species = 'human'
                
            # Build SQLite query with proper table
            # ALWAYS enforce a limit for safety
            MAX_RESULTS = 10
            sql = f"SELECT * FROM {species} WHERE 1=1"
            logger.info(f"Querying {self.species_display_names[species]} tRNA database")
            sql_params = []
            
            # Handle basic search parameters
            if 'Isotype_from_Anticodon' in params:
                sql += " AND Isotype_from_Anticodon = ?"
                sql_params.append(params['Isotype_from_Anticodon'])
                
            if 'Anticodon' in params:
                sql += " AND Anticodon = ?"
                sql_params.append(params['Anticodon'])
            
            # Handle numeric filters with min/max
            for score_type in ['General_tRNA_Model_Score', 'Isotype_Model_Score']:
                min_key = f"{score_type}_min"
                max_key = f"{score_type}_max"
                
                if min_key in params:
                    sql += f" AND {score_type} >= ?"
                    sql_params.append(float(params[min_key]))
                    
                if max_key in params:
                    sql += f" AND {score_type} <= ?"
                    sql_params.append(float(params[max_key]))
            
            # Handle JSON field search
            if 'json_field' in params:
                field_path = params['json_field']
                if 'json_value' in params:
                    # Search for specific value in JSON field
                    sql += " AND json_extract(overview, ?) LIKE ?"
                    sql_params.append(f"$.{field_path}")
                    sql_params.append(f"%{params['json_value']}%")
                else:
                    # Just check if the field exists and is not null/empty
                    sql += " AND json_extract(overview, ?) IS NOT NULL"
                    sql_params.append(f"$.{field_path}")
            
            # Handle sorting
            if 'sort_by' in params:
                sql += f" ORDER BY {params['sort_by']}"
                if 'order' in params and params['order'].lower() == 'desc':
                    sql += " DESC"
                else:
                    sql += " ASC"
            
            # Handle sorting and random sampling first
            if 'sample' in params and params['sample'].lower() == 'random':
                sql += " ORDER BY RANDOM()"
            elif 'sort_by' in params:
                sql += f" ORDER BY {params['sort_by']}"
                if 'order' in params and params['order'].lower() == 'desc':
                    sql += " DESC"
                else:
                    sql += " ASC"

            # ALWAYS enforce a limit - no exceptions
            requested_limit = 5  # default
            try:
                if 'limit' in params:
                    limit_str = params.get('limit', '5').strip('"\'')
                    requested_limit = int(limit_str)
            except (ValueError, TypeError):
                logger.warning(f"Invalid limit value: {params.get('limit')}. Using default of 5")
                requested_limit = 5

            # Never exceed MAX_RESULTS regardless of requested limit
            final_limit = min(requested_limit, MAX_RESULTS)
            sql += " LIMIT ?"
            sql_params.append(final_limit)
            logger.info(f"Enforcing limit of {final_limit} sequences (requested: {requested_limit}, max allowed: {MAX_RESULTS})")
            except (ValueError, TypeError):
                # If limit conversion fails, use default
                sql += " LIMIT 5"
                logger.warning(f"Invalid limit parameter: {params.get('limit', None)}. Using default limit of 5.")

            # Query SQLite database
            results = []
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, sql_params)
                rows = cursor.fetchall()
                
                for row in rows:
                    # Convert SQLite row to dict
                    row_dict = dict(row)
                    logger.info(f"Retrieved row: {row_dict}")
                    
                    # Handle fields
                    features = row_dict.get('Features', 'high-confidence')  # Not JSON, just a string
                    locus = row_dict.get('Locus', '')  # Not JSON, just a string
                    
                    # Handle actual JSON fields
                    sequences = {}
                    overview = {}
                    
                    # Parse JSON fields
                    sequences = {}
                    overview = {}
                    images = {}
                    
                    try:
                        if row_dict.get('sequences'):
                            sequences = json.loads(row_dict['sequences'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse sequences JSON: {row_dict.get('sequences')}")
                        
                    try:
                        if row_dict.get('overview'):
                            overview = json.loads(row_dict['overview'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse overview JSON: {row_dict.get('overview')}")
                        
                    try:
                        if row_dict.get('images'):
                            images = json.loads(row_dict['images'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse images JSON: {row_dict.get('images')}")
                    
                    # Convert model_agreement to proper boolean
                    model_agreement = str(row_dict.get('Anticodon_and_Isotype_Model_Agreement', '')).lower() == 'true'
                    # Create sequence in PostgreSQL
                    sequence = await sync_to_async(Sequence.objects.create)(
                        user_id=self.user_id,
                        chat_id=self.chat_id,
                        message_id=self.message_id,
                        gene_symbol=row_dict['GtRNAdb_Gene_Symbol'],
                        anticodon=row_dict['Anticodon'],
                        isotype=row_dict['Isotype_from_Anticodon'],
                        general_score=float(row_dict['General_tRNA_Model_Score']),
                        isotype_score=float(row_dict['Isotype_Model_Score']),
                        model_agreement=model_agreement,
                        features=features,
                        locus=locus,
                        sequences=sequences,
                        overview=overview,
                        images=images
                    )
            
                    # Add sequence to results
                    results.append({
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
                        'created_at': sequence.created_at.isoformat()
                    })
            
            return 'human', results
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return 'human', []