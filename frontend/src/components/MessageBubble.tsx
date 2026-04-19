import type { Message } from "../services/api";

/** MessageBubble 组件的 props */
interface MessageBubbleProps {
    /** 消息数据 */
    message: Message;
}

/**
 * 消息气泡组件
 * 根据 role 区分用户和 assistant 的样式
 * assistant 消息支持展示工具调用记录
 */
export function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === "user";

    return (
        <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
            <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${isUser
                        ? "bg-blue-600 text-white rounded-br-sm"
                        : "bg-gray-100 text-gray-900 rounded-bl-sm"
                    }`}
            >
                {/* 消息内容（支持换行） */}
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                </div>

                {/* 工具调用记录（仅 assistant 消息展示） */}
                {!isUser && message.tool_calls.length > 0 && (
                    <div className="mt-2 border-t border-gray-200 pt-2">
                        {message.tool_calls.map((call, idx) => (
                            <div
                                key={idx}
                                className="text-xs text-gray-500 flex items-center gap-1"
                            >
                                <span className="font-mono bg-gray-200 px-1 rounded">
                                    {call.tool}
                                </span>
                                {call.result !== undefined && (
                                    <span>✓</span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}