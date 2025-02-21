import json
import logging
import traceback
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
from django.conf import settings
from asgiref.sync import sync_to_async

from .chat_types import ChatRequest, ToolResult, ToolType
from .agents import PlanningAgent, UserFacingAgent
from .tools.rna_database.mcp import RNADatabaseMCP, MCPRequest
from .models import Message, Chat

logger = logging.getLogger(__name__)

class ChatProcessor:
    """Stateless chat processor for handling a single chat request"""
    
    def __init__(self, request: ChatRequest, api_key: str, base_url: str):
        """Initialize processor for a single request
        
        Args:
            request: ChatRequest containing all necessary request data
            api_key: API key for LLM service
            base_url: Base URL for LLM service
        """
        self.request = request
        self.api_key = api_key
        self.base_url = base_url
        
        logger.debug(f"Initializing ChatProcessor with model: {request.model_name}")
        logger.debug(f"Using API key: {api_key}")
        logger.debug(f"Using base URL: {base_url}")
        
        # Initialize agents for this request
        self.planning_agent = PlanningAgent(api_key, request.model_name, base_url)
        self.user_agent = UserFacingAgent(api_key, request.model_name, base_url)
        
        # Initialize tool for this request
        self.rna_tool = RNADatabaseMCP(
            self.request.user_id,
            self.request.chat_id,
            self.request.message_id
        )

    async def _execute_rna_tool(self, plan_response: str) -> AsyncGenerator[str, None]:
        """Execute RNA tool based on planning response and yield results"""
        # Parse parameters from GET_TRNA format
        params = {}
        parts = plan_response.split()
        for part in parts[1:]:
            if ':' in part:
                key, value = part.split(':', 1)
                value = value.strip('"')
                if key == 'Isotype_from_Anticodon':
                    params['isotype'] = value
                elif key == 'Anticodon':
                    params['anticodon'] = value
                elif key == 'General_tRNA_Model_Score_min':
                    params['min_score'] = float(value)
                elif key == 'species':
                    params['species'] = value
                elif key == 'limit':
                    params['limit'] = int(value)

        # Add request context
        params["context"] = {
            "user_id": self.request.user_id,
            "chat_id": self.request.chat_id,
            "message_id": self.request.message_id
        }

        # Create and execute MCP request
        mcp_request = MCPRequest(
            method="search_rna",
            params=params
        )

        # Notify start of tool execution
        yield json.dumps({
            'type': 'tool_start',
            'content': "Searching for tRNA sequences...",
            'timestamp': datetime.utcnow().isoformat()
        })

        result = await self.rna_tool.process_request(mcp_request)
        
        if result.status == "success" and "sequences" in result.data:
            sequences = result.data["sequences"]
            
            # Process sequences and yield both raw and filtered data
            filtered_sequences = []
            for sequence in sequences:
                # Yield raw sequence data for streaming
                yield json.dumps({
                    'type': 'sequence_data',
                    'data': sequence,
                    'timestamp': datetime.utcnow().isoformat()
                })

                # Add filtered data to our accumulated data
                filtered_sequences.append({
                    'gene_symbol': sequence.get('gene_symbol', ''),
                    'anticodon': sequence.get('anticodon', ''),
                    'isotype': sequence.get('isotype', ''),
                    'general_score': sequence.get('general_score', 0.0),
                    'sequences': {
                        'Genomic Sequence': sequence.get('sequences', {}).get('Genomic Sequence', ''),
                        'Secondary Structure': sequence.get('sequences', {}).get('Secondary Structure (nested bp)', ''),
                        'Mature tRNA': sequence.get('sequences', {}).get('Predicted Mature tRNA', '')
                    }
                })

            # Yield filtered data as a special message type
            yield json.dumps({
                'type': 'tool_result',
                'data': filtered_sequences,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            error_msg = result.error["message"] if result.error else "Unknown error"
            yield json.dumps({
                'type': 'error',
                'content': f"Error executing RNA tool: {error_msg}",
                'timestamp': datetime.utcnow().isoformat()
            })

    async def process_message(self) -> AsyncGenerator[str, None]:
        """Process the chat request and stream the response"""
        try:
            # Send initial start event with chat info
            chat = await sync_to_async(Chat.objects.get)(id=self.request.chat_id)
            yield json.dumps({
                'type': 'start',
                'chat': {
                    'id': str(chat.id),
                    'title': chat.title
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Planning phase
            accumulated_data = []
            last_plan_response = None
            
            # Execute planning loop
            for _ in range(getattr(settings, 'PLANNING_LOOP_MAX', 5)):
                plan_response = self.planning_agent.get_next_step(
                    self.request.message_content,
                    accumulated_data,
                    last_plan_response,
                    self.request.chat_history[-4:] if self.request.chat_history else None
                )
                
                if "PLAN_COMPLETE=True" in plan_response:
                    break
                
                # Handle tool execution
                if plan_response.startswith('GET_TRNA'):
                    async for result in self._execute_rna_tool(plan_response):
                        result_obj = json.loads(result)
                        # Forward all messages to client
                        yield result
                        # But only add tool results to accumulated data
                        if result_obj['type'] == 'tool_result':
                            accumulated_data.extend(result_obj['data'])
                
                last_plan_response = plan_response
            
            # Response phase - stream the response
            async for chunk in self.user_agent.stream_response(
                self.request.message_content,
                self.request.chat_history,
                accumulated_data
            ):
                yield chunk
            
            # Save assistant's response to database
            if accumulated_data:  # Only if we have tool results
                chat = await sync_to_async(Chat.objects.get)(id=self.request.chat_id)
                await sync_to_async(Message.objects.create)(
                    chat=chat,
                    content=json.dumps(accumulated_data),
                    role='assistant'
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.error(traceback.format_exc())
            yield json.dumps({
                'type': 'error',
                'content': f"Error: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            })