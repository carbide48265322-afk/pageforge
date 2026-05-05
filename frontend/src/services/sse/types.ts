/**
 * SSE 事件类型定义
 * 对应后端推送的所有 SSE 事件
 */

// ========== 基础类型 ==========

export interface SSEEvent {
  event: string;
  data: unknown;
}

// ========== Thinking 相关 ==========

export interface ThinkingBlock {
  type: 'thinking';
  id: string;
  status: 'streaming' | 'complete';
  content: string;           // thinking_delta 累积的内容
  summary?: string;          // thinking_end 时填入的摘要
  startedAt: number;         // thinking_start 时间戳
  completedAt?: number;      // thinking_end 时间戳
}

// ========== Plan 相关 ==========

export interface PlanStep {
  id: number;
  label: string;            // 步骤名称，如"生成项目结构"
  status: 'pending' | 'active' | 'done';  // 当前状态
}

export interface PlanBlock {
  type: 'plan';
  id: string;
  steps: PlanStep[];
  currentStep: number;      // 当前执行到的步骤索引（0-based）
  isComplete: boolean;       // plan_done 后为 true
}

// ========== Tool Call 相关 ==========

export interface ToolCallBlock {
  type: 'tool_call';
  id: string;
  name: string;               // 工具名，如 "react-vite-scaffold"
  input?: Record<string, unknown>;  // 输入参数（可选，可能很大）
  status: 'running' | 'success' | 'error';
  durationMs?: number;         // tool_call:end 时填入
  error?: string;              // status === 'error' 时填入
  startedAt: number;
  endedAt?: number;
}

// ========== File 相关 ==========

export interface FileNode {
  type: 'file' | 'folder';
  name: string;
  path: string;
  children?: FileNode[];
  language?: string;
  size_bytes?: number;
}

// ========== Status 相关 ==========

export type WebContainerPhase = 'idle' | 'booting' | 'installing' | 'ready' | 'running' | 'error';

export interface StatusEvent {
  phase?: WebContainerPhase;
  message?: string;
  [key: string]: unknown;
}

// ========== Intent 相关 ==========

export interface IntentResult {
  intent: 'chat' | 'code_gen' | 'code_edit' | 'explain' | 'debug' | 'file_operation' | 'unknown';
  confidence: number;
  tags?: string[];
  mode?: 'frontend' | 'backend' | 'fullstack' | null;
  complexity?: 'simple' | 'medium' | 'complex' | null;
  suggested_style?: string;
}

// ========== Style 相关 ==========

export interface StyleConfig {
  style: string;
  primary_color?: string;
  description?: string;
  [key: string]: unknown;
}

// ========== RenderBlock（用于 useSSEv2 状态聚合）==========

export type RenderBlock = ThinkingBlock | PlanBlock | ToolCallBlock | TextBlock;

export interface SSEStatus {
  status: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';
  error?: string;
}

// ========== Text 相关 ==========

export interface TextBlock {
  type: 'text';
  id: string;
  content: string;
  status: 'streaming' | 'complete';
  startedAt: number;
  completedAt?: number;
}

// ========== Command Output 相关 ==========

export interface CommandOutput {
  type: 'command_output';
  id: string;
  output: string;
  timestamp: number;
}

// ========== Preview 相关 ==========

export interface PreviewSource {
  mode: 'none' | 'url' | 'srcdoc';
  url?: string;
  srcdoc?: string;
}
