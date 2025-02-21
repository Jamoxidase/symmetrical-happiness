from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class ToolType(Enum):
    """Available tool types for chat processing."""
    GET_TRNA = "GET_TRNA"
    ALIGNER = "ALIGNER"
    TRNASCAN_SPRINZL = "tRNAscan-SE/SPRINZL"
    TERTIARY_STRUCT = "TERTIARY_STRUCT"

@dataclass
class ChatRequest:
    """Single request data structure containing all necessary data for processing"""
    user_id: str
    chat_id: str
    message_id: str
    message_content: str
    model_name: str
    chat_history: List[Dict[str, Any]]  # Recent messages from DB

@dataclass
class ChatMessage:
    """Single chat message structure"""
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "content": self.content
        }

@dataclass
class ToolResult:
    """Result from executing a tool"""
    tool_type: ToolType
    data: Any
    raw_output: str
    sequence_ids: List[str] = None  # Store sequence IDs for reference

    def __post_init__(self):
        if self.sequence_ids is None:
            self.sequence_ids = []