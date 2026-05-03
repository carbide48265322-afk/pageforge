from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional

from app.services.webcontainer_service import WebContainerService

router = APIRouter()
webcontainer_service = WebContainerService()


# ---------- 请求/响应模型 ----------

class CreateProjectRequest(BaseModel):
    """创建项目的请求"""
    session_id: str
    version: int


class CreateProjectResponse(BaseModel):
    """创建项目的响应"""
    project_path: str
    files: List[str]
    status: str


class ProjectStatusResponse(BaseModel):
    """项目状态响应"""
    status: str
    project_path: Optional[str] = None
    existing_files: List[str] = []
    missing_files: List[str] = []
    has_node_modules: bool = False
    dependencies: Dict[str, str] = {}
    dev_dependencies: Dict[str, str] = {}
    message: Optional[str] = None


class InstallDependenciesResponse(BaseModel):
    """安装依赖的响应"""
    status: str
    message: str
    error: Optional[str] = None
    stdout: Optional[str] = None


class StartDevServerResponse(BaseModel):
    """启动开发服务器的响应"""
    status: str
    message: str
    port: Optional[int] = None
    url: Optional[str] = None
    pid: Optional[int] = None
    error: Optional[str] = None
    stdout: Optional[str] = None


class ProjectFilesResponse(BaseModel):
    """项目文件响应"""
    project_path: str
    files: Dict[str, dict]


class CreateFromTemplateRequest(BaseModel):
    """从模板创建项目的请求"""
    session_id: str
    version: int
    template_name: str


class CreateFromTemplateResponse(BaseModel):
    """从模板创建项目的响应"""
    project_path: str
    files: List[str]
    status: str
    template: str


class CleanupResponse(BaseModel):
    """清理响应"""
    status: str
    message: str
    error: Optional[str] = None


# ---------- API 端点 ----------

@router.post("/projects", response_model=CreateProjectResponse)
async def create_project(session_id: str, version: int):
    """为指定会话和版本创建 WebContainer 项目"""
    try:
        result = webcontainer_service.create_project(session_id, version)
        return CreateProjectResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("/projects/{session_id}/{version}/status", response_model=ProjectStatusResponse)
async def get_project_status(session_id: str, version: int):
    """获取项目状态"""
    try:
        result = webcontainer_service.get_project_status(session_id, version)
        return ProjectStatusResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目状态失败: {str(e)}")


@router.post("/projects/{session_id}/{version}/install", response_model=InstallDependenciesResponse)
async def install_dependencies(session_id: str, version: int):
    """安装项目依赖"""
    try:
        result = webcontainer_service.install_dependencies(session_id, version)
        return InstallDependenciesResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"安装依赖失败: {str(e)}")


@router.post("/projects/{session_id}/{version}/start", response_model=StartDevServerResponse)
async def start_dev_server(session_id: str, version: int):
    """启动开发服务器"""
    try:
        result = webcontainer_service.start_dev_server(session_id, version)
        return StartDevServerResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动开发服务器失败: {str(e)}")


@router.get("/projects/{session_id}/{version}/files", response_model=ProjectFilesResponse)
async def get_project_files(session_id: str, version: int):
    """获取项目文件列表和内容"""
    try:
        result = webcontainer_service.get_project_files(session_id, version)
        return ProjectFilesResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目文件失败: {str(e)}")


@router.delete("/projects/{session_id}/{version}", response_model=CleanupResponse)
async def cleanup_project(session_id: str, version: int):
    """清理指定项目"""
    try:
        result = webcontainer_service.cleanup_project(session_id, version)
        return CleanupResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理项目失败: {str(e)}")


@router.delete("/projects/{session_id}", response_model=CleanupResponse)
async def cleanup_session_projects(session_id: str):
    """清理会话的所有项目"""
    try:
        result = webcontainer_service.cleanup_session(session_id)
        return CleanupResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理会话失败: {str(e)}")


@router.post("/projects/template", response_model=CreateFromTemplateResponse)
async def create_project_from_template(request: CreateFromTemplateRequest):
    """从模板创建 React 项目"""
    try:
        result = webcontainer_service.create_project_from_template(
            request.session_id,
            request.version,
            request.template_name
        )
        return CreateFromTemplateResponse(**result, template=request.template_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"从模板创建项目失败: {str(e)}")


@router.get("/templates")
async def get_available_templates():
    """获取可用模板列表"""
    templates = {
        "counter": {
            "name": "计数器",
            "description": "一个简单的计数器应用，支持本地存储",
            "features": ["React Hooks", "LocalStorage", "响应式设计"]
        },
        "todo": {
            "name": "待办事项",
            "description": "功能完整的待办事项管理应用",
            "features": ["任务管理", "过滤功能", "本地存储"]
        },
        "calculator": {
            "name": "计算器",
            "description": "支持基本四则运算的计算器",
            "features": ["数学运算", "键盘支持", "响应式界面"]
        },
        "weather": {
            "name": "天气查询",
            "description": "城市天气信息查询应用",
            "features": ["城市搜索", "天气数据", "图标显示"]
        },
        "chat": {
            "name": "聊天应用",
            "description": "实时聊天界面，支持AI助手",
            "features": ["实时消息", "AI回复", "用户设置"]
        },
        "blog": {
            "name": "博客系统",
            "description": "功能完整的博客管理系统",
            "features": ["文章管理", "搜索过滤", "分类标签"]
        },
        "charts": {
            "name": "数据图表",
            "description": "数据可视化图表展示应用",
            "features": ["多种图表", "实时数据", "动画效果"]
        }
    }
    return templates


@router.get("/projects/{session_id}/{version}/preview")
async def get_preview_info(session_id: str, version: int):
    """获取预览信息"""
    try:
        status = webcontainer_service.get_project_status(session_id, version)

        preview_info = {
            "session_id": session_id,
            "version": version,
            "status": status.status,
            "project_ready": status.has_node_modules if hasattr(status, 'has_node_modules') else False,
            "files_count": len(status.existing_files) if hasattr(status, 'existing_files') else 0
        }

        return preview_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预览信息失败: {str(e)}")


@router.post("/projects/{session_id}/{version}/build")
async def build_project(session_id: str, version: int):
    """构建项目"""
    try:
        import subprocess
        from pathlib import Path

        project_dir = webcontainer_service._get_project_dir(session_id, version)

        if not project_dir.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        # 检查 node_modules 是否存在
        if not (project_dir / 'node_modules').exists():
            raise HTTPException(status_code=400, detail="请先安装依赖")

        # 执行构建命令
        result = subprocess.run(
            ['npm', 'run', 'build'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            return {
                "status": "error",
                "message": "构建失败",
                "error": result.stderr,
                "stdout": result.stdout
            }

        # 读取构建结果
        dist_dir = project_dir / 'dist'
        if dist_dir.exists():
            build_files = []
            for file_path in dist_dir.rglob('*'):
                if file_path.is_file():
                    build_files.append(str(file_path.relative_to(dist_dir)))

            return {
                "status": "success",
                "message": "构建成功",
                "build_files": build_files,
                "stdout": result.stdout
            }
        else:
            return {
                "status": "error",
                "message": "构建完成但未找到 dist 目录"
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "构建超时"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建项目失败: {str(e)}")