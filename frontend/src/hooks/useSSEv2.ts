import { useState, useCallback, useRef, useEffect } from "react";
import type { Message } from "../services/api";
import { SseEventDispatcher } from "../services/sse";
import type {
  ThinkingBlock,
  PlanBlock,
  ToolCallBlock,
  FileNode,
  IntentResult,
  RenderBlock,
  SSEStatus,
  PreviewSource,
} from "../services/sse/types";

// ========== 类型定义（保持向后兼容）==========

/** 意图识别结果 */
export interface IntentResultV2 {
  intent: "chat" | "code_gen" | "code_edit" | "explain" | "debug" | "file_operation" | "unknown";
  confidence: number;
  tags?: string[];
  mode?: "frontend" | "backend" | "fullstack";
  complexity?: "simple" | "medium" | "complex";
  suggested_style?: string;
}

/** 计划步骤 */
export interface PlanStepV2 {
  step: number;
  description: string;
  status: "pending" | "in_progress" | "done";
}

/** 文件信息 */
export interface FileInfo {
  path: string;
  name: string;
  language?: string;
  size_bytes?: number;
}

/** 状态信息 */
export interface StatusInfo {
  status: "init" | "installing" | "install_done" | "generation_done" | "starting_dev" | "preview_ready";
  progress?: number;
  message?: string;
  url?: string;
}

/** 新渲染块 */
export interface RenderBlockV2 {
  id: string;
  type:
    | "reasoning"
    | "text"
    | "tool_call"
    | "generation"
    | "intent"
    | "thinking"
    | "plan"
    | "file_created"
    | "file_updated"
    | "file_deleted"
    | "status";
  content: string;
  status: "streaming" | "done" | "loading";
  // 类型特定字段
  intent?: IntentResultV2;
  plan_steps?: PlanStepV2[];
  file?: FileInfo;
  status_info?: StatusInfo;
  tool?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  version?: number;
}

/** PreviewSource 联合类型 */
export type PreviewSource =
  | { mode: 'html'; html: string }
  | { mode: 'url'; url: string }
  | { mode: 'none' };

/** useSSEv2 hook 返回值 */
export interface UseSSEv2Return {
  /** 消息列表 */
  messages: Message[];
  /** 当前流式响应的渲染块列表 */
  currentBlocks: RenderBlockV2[];
  /** 已完成的对话轮次 */
  completedTurns: { userMsg: Message; blocks: RenderBlockV2[] }[];
  /** 是否正在流式响应中 */
  isLoading: boolean;
  /** 预览源 */
  previewSource: PreviewSource;
  /** 文件树数据 */
  files: FileInfo[];
  /** 最新版本号 */
  latestVersion: number;
  /** 意图识别结果 */
  intentResult: IntentResult | null;
  /** 文件生成是否完成 */
  generationDone: boolean;
  /** 手动设置 previewSource */
  setPreviewSource: React.Dispatch<React.SetStateAction<PreviewSource>>;
  /** 发送消息 */
  sendMessage: (content: string) => void;
  /** 停止生成 */
  stopGeneration: () => void;
  /** 清空对话 */
  clearMessages: () => void;
}

// API 基础地址
const API_BASE = "http://localhost:9565/api";

/**
 * SSE v2 Hook - 使用三层架构（Dispatcher → Handlers → State Aggregation）
 *
 * 改造后只做状态聚合，事件处理逻辑委托给 SseEventDispatcher 和 handlers/
 * 新增事件类型只需在 handlers/ 目录添加新文件 + HANDLER_MAP 注册一行
 * 本文件不需要修改
 */

export function useSSEv2(sessionId: string | null): UseSSEv2Return {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentBlocks, setCurrentBlocks] = useState<RenderBlockV2[]>([]);
  const [completedTurns, setCompletedTurns] = useState<
    { userMsg: Message; blocks: RenderBlockV2[] }[]
  >([]);

  const [isLoading, setIsLoading] = useState(false);
  const [previewSource, setPreviewSource] = useState<PreviewSource>({ mode: 'none' });
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [latestVersion, setLatestVersion] = useState(0);
  const [intentResult, setIntentResult] = useState<IntentResult | null>(null);
  const [generationDone, setGenerationDone] = useState(false);

  const dispatcherRef = useRef<SseEventDispatcher | null>(null);
  const blockIdRef = useRef(0);
  const blocksRef = useRef<RenderBlockV2[]>([]);
  const messagesRef = useRef<Message[]>([]);

  // 初始化 Dispatcher（只在 sessionId 变化时创建一次）
  useEffect(() => {
    if (!sessionId) return;

    const url = `${API_BASE}/sessions/${sessionId}/messages`;
    const dispatcher = new SseEventDispatcher(url);
    dispatcherRef.current = dispatcher;

    // ---- 订阅事件（状态聚合）----

    // 思维链完成时更新 blocks
    const unsubThinkingEnd = dispatcher.on('thinking_end', (data) => {
      const thinkingData = data as ThinkingBlock;
      const blocks = blocksRef.current;
      const target = blocks.find(b => b.id === thinkingData.id && b.type === 'thinking');
      if (target) {
        target.status = 'done';
        target.content = thinkingData.content;
        setCurrentBlocks([...blocks]);
      }
    });

    // 计划更新时更新 blocks
    const unsubPlanUpdate = dispatcher.on('plan_update', (data) => {
      const planData = data as PlanBlock;
      const blocks = blocksRef.current;

      // 转换为 V2 格式的 plan_steps
      const planSteps: PlanStepV2[] = planData.steps.map(s => ({
        step: s.id,
        description: s.label,
        status: s.status === 'pending' ? 'pending' : s.status === 'active' ? 'in_progress' : 'done',
      }));

      const existing = blocks.find(b => b.type === 'plan');
      if (existing) {
        existing.plan_steps = planSteps;
        existing.content = `计划更新：${planData.steps.length} 个步骤`;
        existing.status = planData.isComplete ? 'done' : 'streaming';
      } else {
        blocks.push({
          id: `plan_${Date.now()}`,
          type: 'plan',
          content: `计划：${planData.steps.length} 个步骤`,
          status: planData.isComplete ? 'done' : 'streaming',
          plan_steps: planSteps,
        });
      }

      setCurrentBlocks([...blocks]);
    });

    // 工具调用结束时更新 blocks
    const unsubToolEnd = dispatcher.on('tool_call:end', (data) => {
      const toolData = data as ToolCallBlock;
      const blocks = blocksRef.current;
      const target = blocks.find(b => b.id === toolData.id && b.type === 'tool_call');
      if (target) {
        target.status = toolData.status === 'error' ? 'loading' : 'done';
        if (toolData.error) {
          target.result = { error: toolData.error };
        }
        if (toolData.durationMs) {
          target.result = { durationMs: toolData.durationMs };
        }
        setCurrentBlocks([...blocks]);
      }
    });

    // 文件创建时更新文件列表和 blocks
    const unsubFileCreated = dispatcher.on('file_created', (data) => {
      const fileData = data as FileNode;
      const fileInfo: FileInfo = {
        path: fileData.path,
        name: fileData.name,
        language: fileData.language,
        size_bytes: fileData.size_bytes,
      };
      setFiles(prev => [...prev, fileInfo]);

      const blocks = blocksRef.current;
      blocks.push({
        id: `file_${Date.now()}`,
        type: 'file_created',
        content: `文件创建：${fileData.path}`,
        status: 'done',
        file: fileInfo,
      });
      setCurrentBlocks([...blocks]);
    });

    // 文件更新时更新 blocks
    const unsubFileUpdated = dispatcher.on('file_updated', (data) => {
      const fileData = data as FileNode;
      const fileInfo: FileInfo = {
        path: fileData.path,
        name: fileData.name,
        language: fileData.language,
      };
      const blocks = blocksRef.current;
      blocks.push({
        id: `file_${Date.now()}`,
        type: 'file_updated',
        content: `文件更新：${fileData.path}`,
        status: 'done',
        file: fileInfo,
      });
      setCurrentBlocks([...blocks]);
    });

    // 状态变更时更新 blocks
    const unsubStatusGenDone = dispatcher.on('status:generation_done', () => {
      setGenerationDone(true);
      const blocks = blocksRef.current;
      blocks.push({
        id: `status_gen_${Date.now()}`,
        type: 'status',
        content: '生成完成',
        status: 'done',
        status_info: { status: 'generation_done', message: '代码生成已完成' },
      });
      setCurrentBlocks([...blocks]);
    });

    // 预览就绪时通知
    const unsubStatusPreviewReady = dispatcher.on('status:preview_ready', () => {
      // preview_ready 只标记后端完成，前端 WebContainer 启动由 App.tsx 处理
    });

    // 意图识别完成时更新
    const unsubIntentResult = dispatcher.on('intent:result', (data) => {
      const intentData = data as IntentResult;
      setIntentResult(intentData);

      const blocks = blocksRef.current;
      blocks.push({
        id: `intent_${Date.now()}`,
        type: 'intent',
        content: `意图识别：${intentData.intent} (置信度: ${intentData.confidence})`,
        status: 'done',
        intent: intentData as unknown as IntentResultV2,
      });
      setCurrentBlocks([...blocks]);
    });

    // 风格选择完成时记录
    const unsubStyleSelected = dispatcher.on('style_selected', (data) => {
      console.log('Style selected:', data);
    });

    // 清理函数
    return () => {
      unsubThinkingEnd();
      unsubPlanUpdate();
      unsubToolEnd();
      unsubFileCreated();
      unsubFileUpdated();
      unsubStatusGenDone();
      unsubStatusPreviewReady();
      unsubIntentResult();
      unsubStyleSelected();
      dispatcher.disconnect();
      dispatcherRef.current = null;
    };
  }, [sessionId]);

  /** 生成块 ID */
  const nextBlockId = useCallback(() => {
    blockIdRef.current += 1;
    return `blk_v2_${blockIdRef.current}`;
  }, []);

  /** 发送消息并处理 SSE 流式响应 */
  const sendMessage = useCallback(
    (content: string) => {
      if (!sessionId || !dispatcherRef.current || isLoading) return;

      // 添加用户消息
      const userMessage: Message = {
        id: `local-${Date.now()}`,
        session_id: sessionId,
        role: "user",
        content,
        timestamp: new Date().toISOString(),
        tool_calls: [],
        html_version: null,
      };
      setMessages((prev) => [...prev, userMessage]);
      messagesRef.current = [...messagesRef.current, userMessage];

      setIsLoading(true);
      setCurrentBlocks([]);
      blocksRef.current = [];
      blockIdRef.current = 0;
      setGenerationDone(false);

      // 使用 Dispatcher 的 sendMessage 方法发送消息并接收 SSE 流
      dispatcherRef.current.sendMessage(content);
    },
    [sessionId, isLoading],
  );

  /** 停止当前生成 */
  const stopGeneration = useCallback(() => {
    dispatcherRef.current?.disconnect();
    setIsLoading(false);
    blocksRef.current = [];
    setCurrentBlocks([]);
  }, []);

  /** 清空对话 */
  const clearMessages = useCallback(() => {
    dispatcherRef.current?.disconnect();
    setIsLoading(false);
    setMessages([]);
    setCompletedTurns([]);
    messagesRef.current = [];
    setCurrentBlocks([]);
    blocksRef.current = [];
    setPreviewSource({ mode: 'none' });
    setFiles([]);
    setLatestVersion(0);
    setIntentResult(null);
    setGenerationDone(false);
  }, []);

  return {
    messages,
    currentBlocks,
    completedTurns,
    isLoading,
    previewSource,
    files,
    latestVersion,
    intentResult,
    generationDone,
    setPreviewSource,
    sendMessage,
    stopGeneration,
    clearMessages,
  };
}
