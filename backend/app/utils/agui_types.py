"""AG-UI Protocol Type Definitions

This module defines all the AG-UI protocol types and events according to the specification.
Reference: doc/AG-UI.txt
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class AGUIEventType(str, Enum):
    """AG-UI Event Types - 16 standard events"""
    
    # Core Events
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"
    
    # Message Events
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_DELTA = "TEXT_MESSAGE_DELTA"
    TEXT_MESSAGE_DONE = "TEXT_MESSAGE_DONE"
    
    # Tool Events
    TOOL_CALL_STARTED = "TOOL_CALL_STARTED"
    TOOL_CALL_FINISHED = "TOOL_CALL_FINISHED"
    TOOL_CALL_ERROR = "TOOL_CALL_ERROR"
    TOOL_CALL_REQUEST = "TOOL_CALL_REQUEST"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
    
    # State Events
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"
    
    # User Events
    USER_INPUT_REQUESTED = "USER_INPUT_REQUESTED"
    USER_INPUT_RECEIVED = "USER_INPUT_RECEIVED"
    
    # System Events
    SYSTEM_MESSAGE = "SYSTEM_MESSAGE"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class AGUIEvent(BaseModel):
    """Base AG-UI Event Structure"""
    
    type: AGUIEventType
    timestamp: float = Field(default_factory=lambda: __import__('time').time())
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None


class TextMessageContent(AGUIEvent):
    """TEXT_MESSAGE_CONTENT event"""
    
    type: AGUIEventType = AGUIEventType.TEXT_MESSAGE_CONTENT
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "content": "",
        "messageId": "",
        "role": "assistant"
    })


class TextMessageDelta(AGUIEvent):
    """TEXT_MESSAGE_DELTA event for streaming"""
    
    type: AGUIEventType = AGUIEventType.TEXT_MESSAGE_DELTA
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "delta": "",
        "messageId": ""
    })


class TextMessageDone(AGUIEvent):
    """TEXT_MESSAGE_DONE event"""
    
    type: AGUIEventType = AGUIEventType.TEXT_MESSAGE_DONE
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "messageId": ""
    })


class RunStarted(AGUIEvent):
    """RUN_STARTED event"""
    
    type: AGUIEventType = AGUIEventType.RUN_STARTED
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "runId": "",
        "agentId": "",
        "timestamp": 0
    })


class RunFinished(AGUIEvent):
    """RUN_FINISHED event"""
    
    type: AGUIEventType = AGUIEventType.RUN_FINISHED
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "runId": "",
        "result": {},
        "timestamp": 0
    })


class RunError(AGUIEvent):
    """RUN_ERROR event"""
    
    type: AGUIEventType = AGUIEventType.RUN_ERROR
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "runId": "",
        "error": "",
        "timestamp": 0
    })


class ToolCallStarted(AGUIEvent):
    """TOOL_CALL_STARTED event"""
    
    type: AGUIEventType = AGUIEventType.TOOL_CALL_STARTED
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "toolCallId": "",
        "toolName": "",
        "parameters": {}
    })


class ToolCallFinished(AGUIEvent):
    """TOOL_CALL_FINISHED event"""
    
    type: AGUIEventType = AGUIEventType.TOOL_CALL_FINISHED
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "toolCallId": "",
        "result": {}
    })


class ToolCallError(AGUIEvent):
    """TOOL_CALL_ERROR event"""
    
    type: AGUIEventType = AGUIEventType.TOOL_CALL_ERROR
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "toolCallId": "",
        "error": ""
    })


class StateSnapshot(AGUIEvent):
    """STATE_SNAPSHOT event"""
    
    type: AGUIEventType = AGUIEventType.STATE_SNAPSHOT
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "state": {}
    })


class StateDelta(AGUIEvent):
    """STATE_DELTA event"""
    
    type: AGUIEventType = AGUIEventType.STATE_DELTA
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "delta": {}
    })


class UserInputRequested(AGUIEvent):
    """USER_INPUT_REQUESTED event"""
    
    type: AGUIEventType = AGUIEventType.USER_INPUT_REQUESTED
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "prompt": "",
        "inputType": "text"
    })


class UserInputReceived(AGUIEvent):
    """USER_INPUT_RECEIVED event"""
    
    type: AGUIEventType = AGUIEventType.USER_INPUT_RECEIVED
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "input": "",
        "inputType": "text"
    })


class SystemMessage(AGUIEvent):
    """SYSTEM_MESSAGE event"""
    
    type: AGUIEventType = AGUIEventType.SYSTEM_MESSAGE
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "message": "",
        "level": "info"
    })


class SystemError(AGUIEvent):
    """SYSTEM_ERROR event"""
    
    type: AGUIEventType = AGUIEventType.SYSTEM_ERROR
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "error": "",
        "level": "error"
    })


# Event Factory
def create_event(event_type: AGUIEventType, **kwargs) -> AGUIEvent:
    """Factory function to create AG-UI events"""
    
    event_classes = {
        AGUIEventType.TEXT_MESSAGE_CONTENT: TextMessageContent,
        AGUIEventType.TEXT_MESSAGE_DELTA: TextMessageDelta,
        AGUIEventType.TEXT_MESSAGE_DONE: TextMessageDone,
        AGUIEventType.RUN_STARTED: RunStarted,
        AGUIEventType.RUN_FINISHED: RunFinished,
        AGUIEventType.RUN_ERROR: RunError,
        AGUIEventType.TOOL_CALL_STARTED: ToolCallStarted,
        AGUIEventType.TOOL_CALL_FINISHED: ToolCallFinished,
        AGUIEventType.TOOL_CALL_ERROR: ToolCallError,
        AGUIEventType.STATE_SNAPSHOT: StateSnapshot,
        AGUIEventType.STATE_DELTA: StateDelta,
        AGUIEventType.USER_INPUT_REQUESTED: UserInputRequested,
        AGUIEventType.USER_INPUT_RECEIVED: UserInputReceived,
        AGUIEventType.SYSTEM_MESSAGE: SystemMessage,
        AGUIEventType.SYSTEM_ERROR: SystemError,
    }
    
    event_class = event_classes.get(event_type, AGUIEvent)
    return event_class(type=event_type, data=kwargs.get('data', {}), metadata=kwargs.get('metadata'))
