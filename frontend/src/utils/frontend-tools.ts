/**
 * 前端工具系统 - 已移除
 * 
 * 工具API应该在后端实现，调用外部服务
 * 前端只负责显示和用户交互
 */

// 空的工具系统，等待后端实现
export interface ToolResult {
  success: boolean;
  data?: any;
  error?: string;
  messageId: string;
}

// 占位符，实际工具调用由后端处理
export class FrontendToolRegistry {
  static async executeTool(name: string, params: Record<string, any>): Promise<ToolResult> {
    console.warn(`前端工具调用已禁用: ${name}`, params);
    return {
      success: false,
      error: '前端工具系统已禁用，工具调用应由后端处理',
      messageId: `tool_error_${Date.now()}`
    };
  }
}