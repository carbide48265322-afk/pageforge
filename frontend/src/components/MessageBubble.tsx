import type { Message } from "../services/api";

interface MessageBubbleProps {
    message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
    const isUser = message.role === "user";

    return (
        <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
            <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${isUser
                    ? "bg-gray-700 text-white"
                    : "bg-white text-gray-800 border border-gray-200 shadow-sm"
                }`}
            >
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                </div>

                {!isUser && message.tool_calls.length > 0 && (
                    <div className="mt-3 border-t border-gray-100 pt-3 space-y-1.5">
                        {message.tool_calls.map((call, idx) => (
                            <div
                                key={idx}
                                className="text-xs text-gray-500 flex items-center gap-1.5"
                            >
                                <span className="font-mono bg-gray-50 px-2 py-1 rounded">
                                    {call.tool}
                                </span>
                                {call.result !== undefined && (
                                    <span className="text-emerald-500">✓</span>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
