import {
    createWebContainerProject,
    getWebContainerStatus,
    installWebContainerDependencies,
    startWebContainerServer,
    getWebContainerFiles,
    buildWebContainerProject,
    getWebContainerPreview,
    cleanupWebContainerProject,
    cleanupWebContainerSession,
    createReactProjectFromTemplate,
    getAvailableTemplates,
    WebContainerStatus,
    InstallResult,
    ServerResult,
    ProjectFiles,
    BuildResult
} from './api';

export interface WebContainerState {
    sessionId: string;
    version: number;
    status: 'idle' | 'creating' | 'installing' | 'starting' | 'running' | 'error';
    projectStatus?: WebContainerStatus;
    installResult?: InstallResult;
    serverResult?: ServerResult;
    error?: string;
}

export class WebContainerAPI {
    private currentState: WebContainerState | null = null;
    private listeners: Set<(state: WebContainerState) => void> = new Set();

    /** 订阅状态变化 */
    subscribe(listener: (state: WebContainerState) => void): () => void {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    }

    /** 通知状态变化 */
    private notifyStateChange() {
        if (this.currentState) {
            this.listeners.forEach(listener => listener(this.currentState!));
        }
    }

    /** 更新状态 */
    private updateState(updates: Partial<WebContainerState>) {
        if (this.currentState) {
            this.currentState = { ...this.currentState, ...updates };
            this.notifyStateChange();
        }
    }

    /** 初始化项目 */
    async initializeProject(sessionId: string, version: number): Promise<void> {
        this.currentState = {
            sessionId,
            version,
            status: 'creating'
        };
        this.notifyStateChange();

        try {
            // 1. 创建项目
            await createWebContainerProject(sessionId, version);
            this.updateState({ status: 'installing' });

            // 2. 安装依赖
            const installResult = await installWebContainerDependencies(sessionId, version);
            this.updateState({ installResult });

            if (installResult.status !== 'success') {
                throw new Error(installResult.error || '依赖安装失败');
            }

            this.updateState({ status: 'starting' });

            // 3. 启动服务器
            const serverResult = await startWebContainerServer(sessionId, version);
            this.updateState({ serverResult });

            if (serverResult.status !== 'success') {
                throw new Error(serverResult.error || '服务器启动失败');
            }

            // 4. 获取项目状态
            const projectStatus = await getWebContainerStatus(sessionId, version);
            this.updateState({
                status: 'running',
                projectStatus
            });

        } catch (error) {
            this.updateState({
                status: 'error',
                error: error instanceof Error ? error.message : '未知错误'
            });
        }
    }

    /** 获取项目状态 */
    async refreshStatus(): Promise<void> {
        if (!this.currentState) return;

        try {
            const status = await getWebContainerStatus(
                this.currentState.sessionId,
                this.currentState.version
            );
            this.updateState({ projectStatus: status });
        } catch (error) {
            this.updateState({
                error: error instanceof Error ? error.message : '获取状态失败'
            });
        }
    }

    /** 安装依赖 */
    async installDependencies(): Promise<void> {
        if (!this.currentState) return;

        this.updateState({ status: 'installing' });

        try {
            const result = await installWebContainerDependencies(
                this.currentState.sessionId,
                this.currentState.version
            );
            this.updateState({ installResult: result });

            if (result.status === 'success') {
                await this.refreshStatus();
            } else {
                throw new Error(result.error || '依赖安装失败');
            }
        } catch (error) {
            this.updateState({
                status: 'error',
                error: error instanceof Error ? error.message : '安装依赖失败'
            });
        }
    }

    /** 启动服务器 */
    async startServer(): Promise<void> {
        if (!this.currentState) return;

        this.updateState({ status: 'starting' });

        try {
            const result = await startWebContainerServer(
                this.currentState.sessionId,
                this.currentState.version
            );
            this.updateState({ serverResult: result });

            if (result.status === 'success') {
                this.updateState({ status: 'running' });
                await this.refreshStatus();
            } else {
                throw new Error(result.error || '服务器启动失败');
            }
        } catch (error) {
            this.updateState({
                status: 'error',
                error: error instanceof Error ? error.message : '启动服务器失败'
            });
        }
    }

    /** 构建项目 */
    async buildProject(): Promise<BuildResult> {
        if (!this.currentState) {
            throw new Error('项目未初始化');
        }

        try {
            const result = await buildWebContainerProject(
                this.currentState.sessionId,
                this.currentState.version
            );
            return result;
        } catch (error) {
            throw new Error(error instanceof Error ? error.message : '构建项目失败');
        }
    }

    /** 获取项目文件 */
    async getProjectFiles(): Promise<ProjectFiles> {
        if (!this.currentState) {
            throw new Error('项目未初始化');
        }

        try {
            return await getWebContainerFiles(
                this.currentState.sessionId,
                this.currentState.version
            );
        } catch (error) {
            throw new Error(error instanceof Error ? error.message : '获取文件失败');
        }
    }

    /** 获取预览信息 */
    async getPreviewInfo(): Promise<any> {
        if (!this.currentState) {
            throw new Error('项目未初始化');
        }

        try {
            return await getWebContainerPreview(
                this.currentState.sessionId,
                this.currentState.version
            );
        } catch (error) {
            throw new Error(error instanceof Error ? error.message : '获取预览信息失败');
        }
    }

    /** 清理项目 */
    async cleanup(): Promise<void> {
        if (!this.currentState) return;

        try {
            await cleanupWebContainerProject(
                this.currentState.sessionId,
                this.currentState.version
            );
            this.currentState = null;
            this.notifyStateChange();
        } catch (error) {
            console.error('清理项目失败:', error);
        }
    }

    /** 清理会话 */
    async cleanupSession(): Promise<void> {
        if (!this.currentState) return;

        try {
            await cleanupWebContainerSession(this.currentState.sessionId);
            this.currentState = null;
            this.notifyStateChange();
        } catch (error) {
            console.error('清理会话失败:', error);
        }
    }

    /** 从模板初始化 React 项目 */
    async initializeFromTemplate(sessionId: string, version: number, templateName: string): Promise<void> {
        this.currentState = {
            sessionId,
            version,
            status: 'creating'
        };
        this.notifyStateChange();

        try {
            // 1. 从模板创建项目
            await createReactProjectFromTemplate(sessionId, version, templateName);
            this.updateState({ status: 'installing' });

            // 2. 安装依赖
            const installResult = await installWebContainerDependencies(sessionId, version);
            this.updateState({ installResult });

            if (installResult.status !== 'success') {
                throw new Error(installResult.error || '依赖安装失败');
            }

            this.updateState({ status: 'starting' });

            // 3. 启动服务器
            const serverResult = await startWebContainerServer(sessionId, version);
            this.updateState({ serverResult });

            if (serverResult.status !== 'success') {
                throw new Error(serverResult.error || '服务器启动失败');
            }

            // 4. 获取项目状态
            const projectStatus = await getWebContainerStatus(sessionId, version);
            this.updateState({
                status: 'running',
                projectStatus
            });

        } catch (error) {
            this.updateState({
                status: 'error',
                error: error instanceof Error ? error.message : '未知错误'
            });
        }
    }

    /** 获取可用模板列表 */
    async getTemplates(): Promise<any> {
        try {
            return await getAvailableTemplates();
        } catch (error) {
            throw new Error(error instanceof Error ? error.message : '获取模板列表失败');
        }
    }

    /** 获取当前状态 */
    getCurrentState(): WebContainerState | null {
        return this.currentState;
    }

    /** 检查项目是否就绪 */
    isReady(): boolean {
        return this.currentState?.status === 'running' &&
               this.currentState.projectStatus?.has_node_modules === true;
    }

    /** 获取服务器 URL */
    getServerUrl(): string | null {
        return this.currentState?.serverResult?.url || null;
    }

    /** 获取服务器端口 */
    getServerPort(): number | null {
        return this.currentState?.serverResult?.port || null;
    }
}

// 创建全局实例
export const webContainerAPI = new WebContainerAPI();

// React Hook 封装
import { useEffect, useState } from 'react';

export function useWebContainer() {
    const [state, setState] = useState<WebContainerState | null>(null);

    useEffect(() => {
        const unsubscribe = webContainerAPI.subscribe(setState);
        setState(webContainerAPI.getCurrentState());
        return unsubscribe;
    }, []);

    return {
        state,
        isReady: webContainerAPI.isReady(),
        serverUrl: webContainerAPI.getServerUrl(),
        serverPort: webContainerAPI.getServerPort(),
        initializeProject: webContainerAPI.initializeProject.bind(webContainerAPI),
        refreshStatus: webContainerAPI.refreshStatus.bind(webContainerAPI),
        installDependencies: webContainerAPI.installDependencies.bind(webContainerAPI),
        startServer: webContainerAPI.startServer.bind(webContainerAPI),
        buildProject: webContainerAPI.buildProject.bind(webContainerAPI),
        getProjectFiles: webContainerAPI.getProjectFiles.bind(webContainerAPI),
        getPreviewInfo: webContainerAPI.getPreviewInfo.bind(webContainerAPI),
        cleanup: webContainerAPI.cleanup.bind(webContainerAPI),
        cleanupSession: webContainerAPI.cleanupSession.bind(webContainerAPI),
        initializeFromTemplate: webContainerAPI.initializeFromTemplate.bind(webContainerAPI),
        getTemplates: webContainerAPI.getTemplates.bind(webContainerAPI)
    };
}