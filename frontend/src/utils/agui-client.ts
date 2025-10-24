/**
 * AG-UI Protocol Client
 * 
 * This module provides AG-UI protocol client functionality for the frontend.
 * It handles SSE event streams and AG-UI event processing.
 */


export interface AGUIEvent {
  type: string;
  timestamp: number;
  data: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface AGUIClientOptions {
  baseUrl: string;
  token?: string;
  onEvent?: (event: AGUIEvent) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export class AGUIClient {
  private baseUrl: string;
  private token?: string;
  private eventSource?: EventSource;
  private onEvent?: (event: AGUIEvent) => void;
  private onError?: (error: Error) => void;
  private onComplete?: () => void;

  constructor(options: AGUIClientOptions) {
    this.baseUrl = options.baseUrl;
    this.token = options.token;
    this.onEvent = options.onEvent;
    this.onError = options.onError;
    this.onComplete = options.onComplete;
  }

  /**
   * Start streaming chat with AG-UI protocol
   */
  async startStreamChat(
    message: string,
    systemPrompt?: string,
    history?: Array<{ role: string; content: string }>,
    runId?: string
  ): Promise<void> {
    try {
      // Close existing connection
      this.close();

      // Prepare request data
      const requestData = {
        message,
        system_prompt: systemPrompt,
        history: history || [],
        run_id: runId
      };

      // Use fetch API for POST request with streaming
      await this.sendPostRequest(`${this.baseUrl}/api/v1/chat/stream`, requestData);

    } catch (error) {
      console.error('Failed to start AG-UI stream:', error);
      this.onError?.(error as Error);
    }
  }

  /**
   * Send POST request to start streaming
   */
  private async sendPostRequest(url: string, data: any): Promise<void> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      // Check if response is streaming
      if (!response.body) {
        throw new Error('No response body available');
      }

      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            this.onComplete?.();
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.trim() === '') continue;
            
            if (line.startsWith('event: ')) {
              // Handle event type (currently not used)
              continue;
            }
            
            if (line.startsWith('data: ')) {
              const eventData = line.slice(6).trim();
              
              if (eventData === '[DONE]') {
                this.onComplete?.();
                return;
              }

              try {
                const aguiEvent: AGUIEvent = JSON.parse(eventData);
                this.onEvent?.(aguiEvent);
              } catch (parseError) {
                console.error('Failed to parse AG-UI event:', parseError, 'Data:', eventData);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

    } catch (error) {
      console.error('Failed to send POST request:', error);
      this.onError?.(error as Error);
    }
  }

  /**
   * Close the connection
   */
  close(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = undefined;
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.eventSource?.readyState === EventSource.OPEN;
  }
}

/**
 * AG-UI Event Handler
 */
export class AGUIEventHandler {
  private onTextContent?: (content: string, messageId: string) => void;
  private onTextDelta?: (delta: string, messageId: string) => void;
  private onRunStarted?: (runId: string, agentId: string) => void;
  private onRunFinished?: (runId: string, result: any) => void;
  private onRunError?: (runId: string, error: string) => void;
  private onSystemMessage?: (message: string, level: string) => void;
  private onToolCallResult?: (callId: string, result: any) => void;
  private onToolCallRequest?: (callId: string, toolName: string, parameters: any) => void;

  constructor() {}

  setOnTextContent(handler: (content: string, messageId: string) => void) {
    this.onTextContent = handler;
  }

  setOnTextDelta(handler: (delta: string, messageId: string) => void) {
    this.onTextDelta = handler;
  }

  setOnRunStarted(handler: (runId: string, agentId: string) => void) {
    this.onRunStarted = handler;
  }

  setOnRunFinished(handler: (runId: string, result: any) => void) {
    this.onRunFinished = handler;
  }

  setOnRunError(handler: (runId: string, error: string) => void) {
    this.onRunError = handler;
  }

  setOnSystemMessage(handler: (message: string, level: string) => void) {
    this.onSystemMessage = handler;
  }

  setOnToolCallResult(handler: (callId: string, result: any) => void) {
    this.onToolCallResult = handler;
  }

  setOnToolCallRequest(handler: (callId: string, toolName: string, parameters: any) => void) {
    this.onToolCallRequest = handler;
  }

  handleEvent(event: AGUIEvent): void {
    switch (event.type) {
      case 'TEXT_MESSAGE_CONTENT':
        this.onTextContent?.(event.data.content, event.data.messageId);
        break;
      
      case 'TEXT_MESSAGE_DELTA':
        this.onTextDelta?.(event.data.delta, event.data.messageId);
        break;
      
      case 'RUN_STARTED':
        this.onRunStarted?.(event.data.runId, event.data.agentId);
        break;
      
      case 'RUN_FINISHED':
        this.onRunFinished?.(event.data.runId, event.data.result);
        break;
      
      case 'RUN_ERROR':
        this.onRunError?.(event.data.runId, event.data.error);
        break;
      
      case 'SYSTEM_MESSAGE':
        this.onSystemMessage?.(event.data.message, event.data.level);
        break;
      
      case 'TOOL_CALL_REQUEST':
        this.onToolCallRequest?.(event.data.callId, event.data.toolName, event.data.parameters);
        break;
      
      case 'TOOL_CALL_RESULT':
        this.onToolCallResult?.(event.data.callId, event.data.result);
        break;
      
      default:
        console.log('Unhandled AG-UI event:', event.type);
    }
  }

}
