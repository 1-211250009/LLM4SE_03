"""AG-UI Protocol Utility Functions

This module provides utility functions for working with AG-UI protocol.
"""

import uuid
import time
from typing import Dict, Any, Optional, List
from .agui_types import AGUIEvent, AGUIEventType, create_event


def generate_run_id() -> str:
    """Generate a unique run ID for AG-UI events"""
    return f"run_{uuid.uuid4().hex[:8]}"


def generate_message_id() -> str:
    """Generate a unique message ID"""
    return f"msg_{uuid.uuid4().hex[:8]}"


def create_text_message_event(content: str, message_id: str = None, role: str = "assistant") -> AGUIEvent:
    """Create a TEXT_MESSAGE_CONTENT event"""
    if not message_id:
        message_id = generate_message_id()
    
    return create_event(
        AGUIEventType.TEXT_MESSAGE_CONTENT,
        data={
            "content": content,
            "messageId": message_id,
            "role": role
        }
    )


def create_text_delta_event(delta: str, message_id: str) -> AGUIEvent:
    """Create a TEXT_MESSAGE_DELTA event"""
    return create_event(
        AGUIEventType.TEXT_MESSAGE_DELTA,
        data={
            "delta": delta,
            "messageId": message_id
        }
    )


def create_text_done_event(message_id: str) -> AGUIEvent:
    """Create a TEXT_MESSAGE_DONE event"""
    return create_event(
        AGUIEventType.TEXT_MESSAGE_DONE,
        data={
            "messageId": message_id
        }
    )


def create_run_started_event(run_id: str, agent_id: str = "default") -> AGUIEvent:
    """Create a RUN_STARTED event"""
    return create_event(
        AGUIEventType.RUN_STARTED,
        data={
            "runId": run_id,
            "agentId": agent_id,
            "timestamp": time.time()
        }
    )


def create_run_finished_event(run_id: str, result: Dict[str, Any] = None) -> AGUIEvent:
    """Create a RUN_FINISHED event"""
    return create_event(
        AGUIEventType.RUN_FINISHED,
        data={
            "runId": run_id,
            "result": result or {},
            "timestamp": time.time()
        }
    )


def create_run_error_event(run_id: str, error: str) -> AGUIEvent:
    """Create a RUN_ERROR event"""
    return create_event(
        AGUIEventType.RUN_ERROR,
        data={
            "runId": run_id,
            "error": error,
            "timestamp": time.time()
        }
    )


def create_system_message_event(message: str, level: str = "info") -> AGUIEvent:
    """Create a SYSTEM_MESSAGE event"""
    return create_event(
        AGUIEventType.SYSTEM_MESSAGE,
        data={
            "message": message,
            "level": level
        }
    )


def create_system_error_event(error: str) -> AGUIEvent:
    """Create a SYSTEM_ERROR event"""
    return create_event(
        AGUIEventType.SYSTEM_ERROR,
        data={
            "error": error,
            "level": "error"
        }
    )


def validate_agui_event(event_data: Dict[str, Any]) -> bool:
    """Validate AG-UI event structure"""
    required_fields = ["type", "timestamp", "data"]
    
    for field in required_fields:
        if field not in event_data:
            return False
    
    # Check if event type is valid
    try:
        AGUIEventType(event_data["type"])
    except ValueError:
        return False
    
    return True


def parse_agui_event(event_data: Dict[str, Any]) -> Optional[AGUIEvent]:
    """Parse AG-UI event from dictionary"""
    if not validate_agui_event(event_data):
        return None
    
    try:
        return AGUIEvent.model_validate(event_data)
    except Exception:
        return None


def get_event_sequence() -> List[AGUIEventType]:
    """Get the standard AG-UI event sequence"""
    return [
        AGUIEventType.RUN_STARTED,
        AGUIEventType.TEXT_MESSAGE_CONTENT,
        AGUIEventType.TEXT_MESSAGE_DELTA,
        AGUIEventType.TEXT_MESSAGE_DONE,
        AGUIEventType.RUN_FINISHED
    ]


def is_core_event(event_type: AGUIEventType) -> bool:
    """Check if event is a core AG-UI event"""
    core_events = {
        AGUIEventType.RUN_STARTED,
        AGUIEventType.RUN_FINISHED,
        AGUIEventType.RUN_ERROR
    }
    return event_type in core_events


def is_message_event(event_type: AGUIEventType) -> bool:
    """Check if event is a message event"""
    message_events = {
        AGUIEventType.TEXT_MESSAGE_CONTENT,
        AGUIEventType.TEXT_MESSAGE_DELTA,
        AGUIEventType.TEXT_MESSAGE_DONE
    }
    return event_type in message_events


def is_tool_event(event_type: AGUIEventType) -> bool:
    """Check if event is a tool event"""
    tool_events = {
        AGUIEventType.TOOL_CALL_STARTED,
        AGUIEventType.TOOL_CALL_FINISHED,
        AGUIEventType.TOOL_CALL_ERROR
    }
    return event_type in tool_events


def is_state_event(event_type: AGUIEventType) -> bool:
    """Check if event is a state event"""
    state_events = {
        AGUIEventType.STATE_SNAPSHOT,
        AGUIEventType.STATE_DELTA
    }
    return event_type in state_events
