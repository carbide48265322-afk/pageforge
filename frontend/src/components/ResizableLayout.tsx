import { Panel, Group, Separator } from "react-resizable-panels";

/** ResizableLayout 组件的 props */
interface ResizableLayoutProps {
    /** 左侧面板内容（聊天区） */
    leftPanel: React.ReactNode;
    /** 右侧面板内容（预览区） */
    rightPanel: React.ReactNode;
    /** 右侧面板是否展开 */
    isRightOpen: boolean;
}

/**
 * 可拖拽分栏布局组件
 * 左侧聊天区 + 右侧预览区，中间拖拽调整宽度
 * 右侧面板关闭时左侧占满宽度
 */
export function ResizableLayout({
    leftPanel,
    rightPanel,
    isRightOpen,
}: ResizableLayoutProps) {
    return (
        <Group orientation="horizontal">
            {/* 左侧面板：聊天区 */}
            <Panel defaultSize={isRightOpen ? 50 : 100} minSize={30}>
                {leftPanel}
            </Panel>

            {/* 右侧面板：预览区（仅展开时显示） */}
            {isRightOpen && (
                <>
                    {/* 拖拽分割条 */}
                    <Separator className="w-1.5 bg-gray-200 hover:bg-blue-400
                        active:bg-blue-500 transition-colors cursor-col-resize
                        relative group">
                        {/* 拖拽手柄视觉提示 */}
                        <div className="absolute inset-y-0 -left-1 -right-1" />
                    </Separator>

                    <Panel defaultSize={50} minSize={25}>
                        {rightPanel}
                    </Panel>
                </>
            )}
        </Group>
    );
}