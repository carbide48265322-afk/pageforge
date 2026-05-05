import { Panel, Group, Separator } from "react-resizable-panels";

interface ResizableLayoutProps {
    leftPanel: React.ReactNode;
    rightPanel: React.ReactNode;
}

export function ResizableLayout({
    leftPanel,
    rightPanel,
}: ResizableLayoutProps) {
    return (
        <div className="flex h-full bg-gray-50 select-none outline-none">
            <Group orientation="horizontal" className="flex-1 select-none outline-none">
                <Panel defaultSize={50} minSize={30}>
                    <div className="h-full">
                        {leftPanel}
                    </div>
                </Panel>

                <Separator className="w-3 bg-transparent cursor-col-resize relative group z-36 select-none outline-none" style={{ width: '12px' }}>
                    <div className="absolute z-0 inset-y-0 left-1/2 w-5" />
                    <div className="absolute z-[1] left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                        style={{ width: '2px', height: '420px' }}>
                        <div className="absolute inset-0"
                            style={{ background: 'linear-gradient(to bottom, transparent 0%, #7669FF 50%, transparent 100%)' }} />
                    </div>
                    <div className="absolute z-[2] opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                        style={{ width: '4px', height: '62px', borderRadius: '999px', background: '#6455FF', left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }} />
                </Separator>

                <Panel defaultSize={50} minSize={25}>
                    <div className="h-full bg-gray-50 rounded-xl shadow-lg overflow-hidden">
                        {rightPanel}
                    </div>
                </Panel>
            </Group>
        </div>
    );
}
