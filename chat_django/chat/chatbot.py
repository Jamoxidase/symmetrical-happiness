import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import json
import pickle
import traceback
from datetime import datetime
import logging
import openai 
import anthropic
import copy
from django.conf import settings
from django.db.models import Model
from asgiref.sync import sync_to_async
from dataclasses_json import dataclass_json
from .prompts import PLANNING_PROMPT, USER_FACING_PROMPT
from .models import Sequence, Chat, Message
from .tools.rna_database.mcp import RNADatabaseMCP, MCPRequest
from .tools.stdio_processor.mcp import StdioMCP
from .tools.crap.crap_mcp import CrapMCP

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ToolType(Enum):
    """Available tool types for chat processing."""
    GET_TRNA = "GET_TRNA"
    ALIGNER = "ALIGNER"
    TRNASCAN_SPRINZL = "tRNAscan-SE/SPRINZL"
    TERTIARY_STRUCT = "TERTIARY_STRUCT"
    CRAP = "CRAP"

@dataclass_json
@dataclass
class ChatMessage:
    """Represents a chat message in the conversation."""
    role: str
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content
        }

@dataclass_json
@dataclass
class ToolResult:
    """Result from executing a tool."""
    tool_type: ToolType
    data: Any
    raw_output: str
    sequence_ids: List[str] = field(default_factory=list)  # Store sequence IDs for reference

class PlanningAgent:
    """Agent responsible for planning the chat interaction flow."""
    
    def __init__(self, api_key: str):
        """Initialize planning agent.
        
        Args:
            api_key: Anthropic API key
        """
        self.client = openai.OpenAI(
            base_url=settings.LITELLM_BASE_URL,
            api_key=api_key
        )
        self.chat_history = []
    
    def get_next_step(self, user_input: str, accumulated_data: List[ToolResult] = None, last_plan_response: str = None, model: str = None) -> str:
        """Get the next step in the interaction plan.
        
        Args:
            user_input: The user's query
            accumulated_data: Data collected from previous steps
            last_plan_response: Response from the last planning step
            
        Returns:
            String indicating the next step to take
        """
        content_parts = [f"Original query: {user_input}"]
        
        # Add last chat pair for context if available
        if self.chat_history and len(self.chat_history) >= 2:
            last_pair = self.chat_history[-2:]  # Get last user/assistant pair
            history_context = [
                f"{msg.role}: {msg.content}" for msg in last_pair
                if isinstance(msg, ChatMessage) and msg.content.strip()
            ]
            if history_context:
                content_parts.append("Last chat exchange:\n" + "\n".join(history_context))
        
        
        complete_content = self._get_planning_system_prompt()

        if accumulated_data:
            # accumulated_data is now a list of summary strings
            data_str = "\n".join(accumulated_data) if accumulated_data else "No data collected yet"
            content_parts.append(f"Here is the data resulting from your previous actions - Good work, now youre on to the next step, or the plan is complete - depending on the data and goal. Data collected so far:\n{data_str}")
        
        if last_plan_response:
            content_parts.append(f"Last planning step:\n{last_plan_response}")
        
        complete_content += "\n\n".join(content_parts)
        
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "system", "content": complete_content}]
        )
        
        return response.choices[0].message.content
    
    def _get_planning_system_prompt(self) -> str:
        """Get the system prompt for the planning agent."""
        return PLANNING_PROMPT

class UserFacingAgent:
    """Agent responsible for generating user-facing responses."""
    
    def __init__(self, api_key: str, max_history: int = 15):
        """Initialize user-facing agent.
        
        Args:
            api_key: Anthropic API key
            max_history: Maximum number of messages to keep in history
        """
        self.client = openai.OpenAI(
            base_url=settings.LITELLM_BASE_URL,
            api_key=api_key
        )
        self.max_history = max_history
        self.chat_history: List[ChatMessage] = []
        self.data = "Here is the data we retrieved for you to incorperate into your response: " # For transient tool data.. maybe move to message idk
    
    async def _update_chat_history(self, role: str, response: str):
        """Update chat history with new messages and sync with database.
        
        This method updates both the in-memory chat history and the database records.
        The messages variable is defined in process_message() and contains the full
        conversation history used for generating responses.

        Args:
            user_input: User's message
            response: Assistant's response
        """
        # Add to in-memory history
        self.chat_history.append(ChatMessage(role=role, content=response))
        
        # If this agent belongs to a ChatProcessor, update its history
        if hasattr(self, '_processor'):
            # Sync with database if we have chat context
            if self._processor.chat_id:
                try:
                    # Get chat instance
                    chat = await sync_to_async(Chat.objects.get)(id=self._processor.chat_id)
                    #HERE
                    # Create only the assistant message in database
                    # User message is already created in the view
                    await sync_to_async(Message.objects.create)(
                        chat=chat,
                        content=response,
                        role=role
                    )
                except Exception as e:
                    logger.error(f"Error syncing {role} response {response} to database: {str(e)}")
                    logger.error(traceback.format_exc())
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get chat history in dictionary format."""
        prompt_with_data = self._get_user_facing_system_prompt()
        messages = messages = [msg.to_dict() if not isinstance(msg, dict) else msg for msg in self.chat_history]
        messages.insert(0, {"role": "system", "content": prompt_with_data})
        return messages
    
    def _get_user_facing_system_prompt(self) -> str:
        """Get the system prompt for the user-facing agent."""
        return str(USER_FACING_PROMPT) + str(self.data)

@dataclass_json
@dataclass
class ChatProcessor:
    """Handles chat message processing and response generation."""
    
    user_id: str
    chat_id: Optional[str] = None
    message_id: Optional[str] = None
    max_history: int = 10
    accumulated_data: List[Dict] = field(default_factory=list)
    data_summary: str = ""
    _chat_history: List[ChatMessage] = field(default_factory=list)
    _next_message_image: Optional[Dict] = None
    
    def __post_init__(self):
        """Initialize non-serializable components after deserialization."""
        # Get settings with fallbacks
        self.api_key = getattr(settings, 'LITELLM_API_KEY', None)
        self.base_url = getattr(settings, 'LITELLM_BASE_URL', None)
        self.model_name = getattr(settings, 'DEFAULT_LLM_MODEL', None)
        
        # Log settings for debugging
        logger.debug(f"Initializing ChatProcessor with base_url={self.base_url}, model={self.model_name}")
        
        if not all([self.api_key, self.base_url, self.model_name]):
            raise ValueError("Missing required LLM settings. Check API_KEY, BASE_URL, and LLM_MODEL_NAME in settings.")
        
        # Initialize agents
        self.planning_agent = PlanningAgent(self.api_key)
        self.user_facing_agent = UserFacingAgent(self.api_key, self.max_history)
        
        # Link agents back to this processor for settings and history sync
        self.planning_agent._processor = self
        self.user_facing_agent._processor = self
        
        # Verify agent initialization
        logger.debug(f"Planning agent base_url: {getattr(self.planning_agent.client, 'base_url', None)}")
        logger.debug(f"User agent base_url: {getattr(self.user_facing_agent.client, 'base_url', None)}")
        
        # Separate histories for planning and chat
        self.planning_history = []  # For current planning loop
        self.last_chat_pair = None  # Last user/assistant exchange
    
    async def process_message(self, message: str) -> AsyncGenerator[str, None]:
        """Process a user message and generate a streaming response.
        
        Args:
            message: The user's input message
            
        Yields:
            Chunks of the response as they are generated
        """
        try:
            logger.debug("Starting process_message")
            
            # Get recent chat history if we have chat context
            if self.chat_id:
                from .db_access import ChatHistoryAccess
                logger.debug(f"Fetching chat history for chat {self.chat_id}")
                
                # Get last 6 messages (3 pairs) for user-facing agent
                history = await ChatHistoryAccess.get_recent_chat_history(
                    self.user_id,
                    self.chat_id,
                    message_limit=6  # 3 pairs
                )
                logger.debug(f"Got {len(history)} messages from history")
                
                self._chat_history = [
                    ChatMessage(role=msg['role'], content=msg['content'])
                    for msg in history
                ]
                

                logger.debug("Chat history messages:")
                for msg in self._chat_history:
                    logger.debug(f"- {msg.role}: {msg.content[:100]}...")
                
                self.user_facing_agent.chat_history = self._chat_history 
                logger.debug("Set user-facing agent chat history")
                
                # Get last pair for planning agent if available
                if len(history) >= 2:
                    last_pair = history[-2:]
                    self.planning_agent.chat_history = [
                        ChatMessage(role=msg['role'], content=msg['content'])
                        for msg in last_pair
                    ] # We are not actually giving it any chat history?
                    logger.debug(f"Initialized planning agent with last chat pair")
            
            # Initialize MCP tool handlers
            rna_tool = RNADatabaseMCP(self.user_id, self.chat_id, self.message_id)
            stdio_tool = StdioMCP(self.user_id, self.chat_id, self.message_id)
            crap_tool = CrapMCP(self.user_id, self.chat_id, self.message_id)
            
            last_plan_response = None
            loop_count = 0
            max_loops = getattr(settings, 'PLANNING_LOOP_MAX', 5)
            
            while loop_count < max_loops:
                logger.debug(f"Planning loop iteration {loop_count}/{max_loops}")
                
                # Get the model from the message
                message_obj = await sync_to_async(Message.objects.get)(id=self.message_id)
                model = message_obj.model or self.model_name  # Use message model or fallback to default
                
                # Get next step from planning agent
                plan_response = self.planning_agent.get_next_step(
                    message,
                    [self.data_summary] if self.data_summary else [],
                    last_plan_response, # Single message history, last response
                    model=model  # Pass the model to the planning agent
                )
                logger.debug(f"Plan response: {plan_response}")
                
                if loop_count >= max_loops - 1 or "PLAN_COMPLETE=True" in plan_response:
                    logger.debug("Plan complete, starting chat response")
                    
                    
                    # Add current message
                    if self._next_message_image:
                        # Add image message to user facing messages as user, this will not sync UNTIL we use agent.update history, fine for now...
                        self.user_facing_agent.chat_history.append({
                            "role": self._next_message_image[0],
                            "content": [
                                self._next_message_image[1],
                            ]
                        })
                        logger.debug(f"Added current message with image: {message[:100]}...")
                        # Clear the image for next message
                        self._next_message_image = None
                    
                    # Log complete LLM call
                    logger.debug("=== COMPLETE LLM CALL PROTOTYPE ===")
                    
                    
                    # Stream response from user-facing agent
                    logger.debug(f"Starting user-facing response using model: {model}")
                    yield json.dumps({
                        'type': 'start_response',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    self.user_facing_agent.data = self.accumulated_data

                    full_response = [] # Collect the full response
                    with self.user_facing_agent.client.chat.completions.create(
                        model=model,
                        max_tokens=1000,
                        temperature=0.7,
                        messages=self.user_facing_agent.get_chat_history(),
                        stream=True
                    ) as stream:
                        logger.debug("Starting stream")
                        for chunk in stream:
                            if chunk.choices[0].delta.content is not None:
                                text = chunk.choices[0].delta.content
                                now = datetime.utcnow()
                                logger.debug(f"Got chunk from OpenAI at {now.isoformat()}: {text[:50]}...")
                                full_response.append(text)
                                yield json.dumps({
                                    'type': 'token',
                                    'content': text,
                                    'timestamp': now.isoformat()
                                })
                        
                        # Join full response and update chat history
                        complete_response = ''.join(full_response)
                        await self.user_facing_agent._update_chat_history("assistant", complete_response)
                        
                        # Signal end of response
                        yield json.dumps({
                            'type': 'end',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        break

                
                # Parse and execute tool commands if present
                if plan_response:
                    if plan_response.startswith('GET_TRNA'):
                        logger.debug("Executing GET_TRNA")
                        # Parse parameters from GET_TRNA format
                        params = {}
                        parts = plan_response.split()
                        for part in parts[1:]:
                            if ':' in part:
                                key, value = part.split(':', 1)
                                value = value.strip('"')
                                # Core parameters
                                if key == 'Isotype_from_Anticodon':
                                    params['isotype'] = value
                                elif key == 'Anticodon':
                                    params['anticodon'] = value
                                elif key == 'species':
                                    params['species'] = value
                                elif key == 'json_field':
                                    # Remove any quotes and preserve exact field name
                                    params['json_field'] = value
                                elif key == 'json_value':
                                    # Remove any quotes from the value
                                    params['json_value'] = value
                                
                                # Score parameters
                                elif key == 'General_tRNA_Model_Score_min':
                                    params['min_general_score'] = float(value)
                                elif key == 'General_tRNA_Model_Score_max':
                                    params['max_general_score'] = float(value)
                                elif key == 'Isotype_Model_Score_min':
                                    params['min_isotype_score'] = float(value)
                                elif key == 'Isotype_Model_Score_max':
                                    params['max_isotype_score'] = float(value)
                                
                                
                                # Sorting and limiting
                                elif key == 'sort_by':
                                    params['sort_by'] = value
                                elif key == 'order':
                                    params['order'] = value.lower()  # normalize to lowercase
                                elif key == 'limit':
                                    params['limit'] = int(value)
                                elif key == 'sample':
                                    params['sample'] = value.lower()  # normalize to lowercase

                        
                        # Create MCP request with context in params
                        params["context"] = {
                            "user_id": self.user_id,
                            "chat_id": self.chat_id,
                            "message_id": self.message_id
                        }
                        mcp_request = MCPRequest(
                            method="search_rna",
                            params=params
                        )

                        # Execute through MCP interface and stream progress
                        logger.debug("Making MCP request")
                        yield json.dumps({
                            'type': 'tool_start',
                            'content': f"Searching for tRNA sequences...",
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        
                        result = await rna_tool.process_request(mcp_request)
                        
                        if result.status == "success" and "sequences" in result.data:
                            
                            sequences = result.data["sequences"]
                            logger.info(f"Got {len(sequences)} sequences")
                            if sequences:
                                logger.info(f"First sequence data: {json.dumps(sequences[0], indent=2)}")
                            
                            # Initialize accumulated_data as empty list
                            
                            
                            # Send sequence data through SSE and store for user-facing agent
                            for sequence in sequences:
                                # Send to frontend
                                sequence_event = {
                                    'type': 'sequence_data',
                                    'data': sequence
                                }
                                yield json.dumps(sequence_event)
                                
                                # Store for user-facing agent with safe field access
                                filtered_data = {
                                    'gene_symbol': sequence.get('gene_symbol', ''),
                                    'anticodon': sequence.get('anticodon', ''),
                                    'isotype': sequence.get('isotype', ''),
                                    'general_score': sequence.get('general_score', 0.0),
                                    'isotype_score': sequence.get('isotype_score', 0.0),
                                    'model_agreement': sequence.get('model_agreement', False),
                                    'features': sequence.get('features', ''),
                                    'locus': sequence.get('locus', ''),
                                    'sequences': {}
                                }
                                
                                # Safely get nested sequence data
                                if 'sequences' in sequence:
                                    seq_data = sequence['sequences']
                                    filtered_data['sequences'] = {
                                        'Genomic Sequence': seq_data.get('Genomic Sequence', ''),
                                        'Secondary Structure': seq_data.get('Secondary Structure (nested bp)', ''),
                                        'Mature tRNA': seq_data.get('Predicted Mature tRNA', '')
                                    }
                                
                                no_filtering=True
                                if no_filtering:
                                    filtered_data = sequence

                                self.accumulated_data.append(filtered_data)
                            
                            # Create summary for planning agent
                            summary = [f"Retrieved {len(sequences)} sequences:"]
                            for seq in sequences:
                                summary.append(f"- {seq['gene_symbol']} ({seq['isotype']})")
                            
                            # Add to accumulated data summary
                            self.data_summary = "FETCHED DATA FOR \n".join(summary)
                        else:
                            # Handle error case
                            error_msg = result.error["message"] if result.error else "Unknown error"
                            yield json.dumps({'type': 'error', 'message': error_msg})
                    
                    elif plan_response.startswith('CRAP'):
                        logger.debug("Executing CRAP")
                        # Parse parameters from CRAP format
                        params = {}
                        parts = plan_response.split()
                        for part in parts[1:]:
                            if ':' in part:
                                key, value = part.split(':', 1)
                                value = value.strip('"')
                                params[key] = value

                        # Add tool tyle param for transparency
                        yield json.dumps({
                                'type': 'tool_progress',
                                'content': f"Found {len(result.data['sequences'])} sequences",
                                'timestamp': datetime.utcnow().isoformat()
                            })
                        
                        # Create MCP request with context in params
                        params["context"] = {
                            "user_id": self.user_id,
                            "chat_id": self.chat_id,
                            "message_id": self.message_id
                        }
                        mcp_request = MCPRequest(
                            method="view_region",
                            params=params
                        )
                        
                        # Execute through MCP interface and stream progress
                        logger.debug("Making CRAP MCP request")
                        yield json.dumps({
                            'type': 'tool_start',
                            'content': f"Surfing the genome browser...",
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        
                        result = await crap_tool.process_request(mcp_request)
                        
                        if result.status == "success":
                            yield json.dumps({
                                'type': 'tool_progress',
                                'content': f"Retrieved genomic data",
                                'timestamp': datetime.utcnow().isoformat()
                            })
                            
                            # Store sequence and annotated sequence for user-facing agent
                            filtered_data = {
                                'sequence': result.data['sequence'],
                                'annotated_sequence': result.data['annotated_sequence'],
                                'features': result.data['features'],
                                'tracks': result.data['tracks'],
                                'browser_link': result.data['browser_link']
                            }
                            self.accumulated_data.append(filtered_data)
                            
                            # Create summary for planning agent
                            summary = [
                                f"Retrieved genomic data:",
                                f"- Sequence length: {len(result.data['sequence'])}",
                                f"- Features: {len(result.data['features'])}",
                                f"- Tracks: {', '.join(result.data['tracks'])}"
                            ]
                            self.data_summary = "\n".join(summary)
                            
                            # If image is available, add it as a separate user message
                            if result.data.get('image') and result.data['image'].get('data'):
                                # Create image content exactly matching required structure
                                """OUTDATED DOCSTRING- THIS IS ANTHROPIC SDK FORMAT image_content = {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",  # Explicitly set
                                            "data": result.data['image']['data']
                                        }
                                    }"""
                                
                                image_content = {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{result.data['image']['data']}"
                                    }
                                }
                                # yield json.dumps(image_content)

                                self._next_message_image = ("user", image_content)
                        else:
                            # Handle error case
                            error_msg = result.error["message"] if result.error else "Unknown error"
                            yield json.dumps({'type': 'error', 'message': error_msg})
                    
                    """elif tool_name == "STDIO":
                        # Extract command from plan response
                        command = plan_response.split("COMMAND=")[1].split("\n")[0].strip()
                        
                        # Create MCP request
                        mcp_request = MCPRequest(
                            command=command,
                            parameters="{}"
                        )
                        
                        # Execute stdio command
                        result = await stdio_tool.process_request(mcp_request)
                        if result:
                            self.data_summary = f"Executed command: {command}"
                            self.accumulated_data.append(result)"""
                
                last_plan_response = plan_response
                loop_count += 1
            
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}")
            logger.error(traceback.format_exc())
            yield json.dumps({
                'type': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })

class ChatManager:
    """Creates new chat processors for message processing."""

    def get_processor(self, user_id: str) -> ChatProcessor:
        """Create a new chat processor for a user.

        Args:
            user_id: Unique identifier for the user

        Returns:
            New ChatProcessor instance
        """
        logger.debug(f"Creating new chat processor for user {user_id}")
        return ChatProcessor(user_id)
