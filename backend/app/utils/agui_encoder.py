"""AG-UI Protocol Event Encoder for SSE (Server-Sent Events)

This module provides encoding functionality for AG-UI events to SSE format.
"""

import json
from typing import Any, Dict, Optional
from .agui_types import AGUIEvent, AGUIEventType


class AGUIEventEncoder:
    """Encoder for AG-UI events to SSE format"""
    
    @staticmethod
    def encode_event(event: AGUIEvent) -> str:
        """
        Encode AG-UI event to SSE format
        
        Args:
            event: AG-UI event object
            
        Returns:
            SSE formatted string
        """
        # Convert event to dict
        event_dict = event.model_dump()
        
        # 确保必要字段不为None
        event_type = event_dict.get("type", "UNKNOWN")
        if event_type is None:
            event_type = "UNKNOWN"
            
        timestamp = event_dict.get("timestamp", 0.0)
        if timestamp is None:
            timestamp = 0.0
            
        data = event_dict.get("data", {})
        if data is None:
            data = {}
        
        # Create SSE data
        sse_data = {
            "type": event_type,
            "timestamp": timestamp,
            "data": data,
            "metadata": event_dict.get("metadata")
        }
        
        # Encode as JSON
        json_data = json.dumps(sse_data, ensure_ascii=False)
        
        # Format as SSE
        sse_lines = [
            f"event: {event_type}",
            f"data: {json_data}",
            ""  # Empty line to end the event
        ]
        
        return "\n".join(sse_lines)
    
    @staticmethod
    def encode_text_stream(chunk: str, message_id: str = None) -> str:
        """
        Encode text chunk for streaming
        
        Args:
            chunk: Text chunk to stream
            message_id: Optional message ID
            
        Returns:
            SSE formatted string for TEXT_MESSAGE_DELTA
        """
        from .agui_types import create_event
        
        event = create_event(
            AGUIEventType.TEXT_MESSAGE_DELTA,
            data={
                "delta": chunk,
                "messageId": message_id or ""
            }
        )
        
        return AGUIEventEncoder.encode_event(event)
    
    @staticmethod
    def encode_run_started(run_id: str, agent_id: str = "default") -> str:
        """Encode RUN_STARTED event"""
        from .agui_types import create_event
        
        event = create_event(
            AGUIEventType.RUN_STARTED,
            data={
                "runId": run_id,
                "agentId": agent_id,
                "timestamp": __import__('time').time()
            }
        )
        
        return AGUIEventEncoder.encode_event(event)
    
    @staticmethod
    def encode_run_finished(run_id: str, result: Dict[str, Any] = None) -> str:
        """Encode RUN_FINISHED event"""
        from .agui_types import create_event
        
        event = create_event(
            AGUIEventType.RUN_FINISHED,
            data={
                "runId": run_id,
                "result": result or {},
                "timestamp": __import__('time').time()
            }
        )
        
        return AGUIEventEncoder.encode_event(event)
    
    @staticmethod
    def encode_run_error(run_id: str, error: str) -> str:
        """Encode RUN_ERROR event"""
        from .agui_types import create_event
        
        event = create_event(
            AGUIEventType.RUN_ERROR,
            data={
                "runId": run_id,
                "error": error,
                "timestamp": __import__('time').time()
            }
        )
        
        return AGUIEventEncoder.encode_event(event)
    
    @staticmethod
    def encode_system_message(message: str, level: str = "info") -> str:
        """Encode SYSTEM_MESSAGE event"""
        from .agui_types import create_event
        
        event = create_event(
            AGUIEventType.SYSTEM_MESSAGE,
            data={
                "message": message,
                "level": level
            }
        )
        
        return AGUIEventEncoder.encode_event(event)
    
    @staticmethod
    def encode_system_error(error: str) -> str:
        """Encode SYSTEM_ERROR event"""
        from .agui_types import create_event
        
        event = create_event(
            AGUIEventType.SYSTEM_ERROR,
            data={
                "error": error,
                "level": "error"
            }
        )
        
        return AGUIEventEncoder.encode_event(event)


class AGUIStreamGenerator:
    """Generator for AG-UI event streams"""
    
    def __init__(self, run_id: str, agent_id: str = "default"):
        self.run_id = run_id
        self.agent_id = agent_id
        self.encoder = AGUIEventEncoder()
    
    def start_run(self):
        """Generate RUN_STARTED event"""
        yield self.encoder.encode_run_started(self.run_id, self.agent_id)
    
    def stream_text(self, text: str, message_id: str = None):
        """Stream text content in chunks"""
        if not message_id:
            message_id = f"msg_{self.run_id}_{__import__('time').time()}"
        
        # Split text into chunks for streaming effect
        chunk_size = 10  # Characters per chunk
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            yield self.encoder.encode_text_stream(chunk, message_id)
            
            # Small delay for streaming effect
            import time
            time.sleep(0.05)
    
    def finish_run(self, result: Dict[str, Any] = None):
        """Generate RUN_FINISHED event"""
        yield self.encoder.encode_run_finished(self.run_id, result)
    
    def error_run(self, error: str):
        """Generate RUN_ERROR event"""
        yield self.encoder.encode_run_error(self.run_id, error)
