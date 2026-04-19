import { useState, useCallback, useEffect } from "react";
import {
    createSession,
    getVersions,
    getHtml,
    setBaseVersion,
    type PageVersion,
    type VersionsResponse,
} from "../services/api";

/** useSession hook 返回的状态和方法 */
export interface UseSessionReturn {
    /** 当前会话 ID */
    sessionId: string | null;
    /** 版本列表 */
    versions: PageVersion[];
    /** 当前基准版本号 */
    currentBase: number;
    /** 是否正在加载 */
    isLoading: boolean;
    /** 创建新会话 */
    newSession: () => Promise<void>;
    /** 加载版本列表 */
    loadVersions: () => Promise<void>;
    /** 切换基准版本 */
    switchBaseVersion: (version: number) => Promise<void>;
    /** 获取指定版本的 HTML */
    loadHtml: (version?: number) => Promise<{ html: string; version: number }>;
}

/**
 * 会话管理 Hook
 * 管理会话的创建、版本列表、基准版本切换等
 */
export function useSession(): UseSessionReturn {
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [versions, setVersions] = useState<PageVersion[]>([]);
    const [currentBase, setCurrentBase] = useState<number>(0);
    const [isLoading, setIsLoading] = useState(false);

    /** 创建新会话 */
    const newSession = useCallback(async () => {
        setIsLoading(true);
        try {
            const res = await createSession();
            setSessionId(res.session_id);
            // 新会话清空版本列表
            setVersions([]);
            setCurrentBase(0);
        } catch (error) {
            console.error("创建会话失败:", error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    /** 加载版本列表 */
    const loadVersions = useCallback(async () => {
        if (!sessionId) return;
        setIsLoading(true);
        try {
            const res: VersionsResponse = await getVersions(sessionId);
            setVersions(res.versions);
            setCurrentBase(res.current_base);
        } catch (error) {
            console.error("加载版本列表失败:", error);
        } finally {
            setIsLoading(false);
        }
    }, [sessionId]);

    /** 切换基准版本 */
    const switchBaseVersion = useCallback(
        async (version: number) => {
            if (!sessionId) return;
            setIsLoading(true);
            try {
                const res = await setBaseVersion(sessionId, version);
                setCurrentBase(res.current_base);
            } catch (error) {
                console.error("切换基准版本失败:", error);
            } finally {
                setIsLoading(false);
            }
        },
        [sessionId],
    );

    /** 获取指定版本的 HTML */
    const loadHtml = useCallback(
        async (version?: number) => {
            if (!sessionId) throw new Error("无活跃会话");
            return await getHtml(sessionId, version);
        },
        [sessionId],
    );

    // sessionId 变化时自动加载版本列表
    useEffect(() => {
        if (sessionId) {
            loadVersions();
        }
    }, [sessionId, loadVersions]);

    return {
        sessionId,
        versions,
        currentBase,
        isLoading,
        newSession,
        loadVersions,
        switchBaseVersion,
        loadHtml,
    };
}
