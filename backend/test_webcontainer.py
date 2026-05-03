import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.services.webcontainer_service import WebContainerService

client = TestClient(app)

def test_webcontainer_service_parse_html():
    """测试 HTML 解析功能"""
    service = WebContainerService()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { background: red; }
            .test { color: blue; }
        </style>
    </head>
    <body>
        <h1>Test Page</h1>
        <script>
            console.log('Hello World');
            function test() { return 42; }
        </script>
    </body>
    </html>
    """

    files = service._parse_html_to_project(html)

    # 检查文件数量
    assert len(files) == 4

    # 检查文件存在性
    assert 'index.html' in files
    assert 'src/style.css' in files
    assert 'src/main.js' in files
    assert 'package.json' in files

    # 检查 HTML 内容
    assert 'Test Page' in files['index.html']
    assert 'src/style.css' in files['index.html']
    assert 'src/main.js' in files['index.html']

    # 检查 CSS 内容
    assert 'background: red' in files['src/style.css']
    assert 'color: blue' in files['src/style.css']

    # 检查 JS 内容
    assert "console.log('Hello World')" in files['src/main.js']
    assert 'function test()' in files['src/main.js']

    # 检查 package.json
    import json
    package_data = json.loads(files['package.json'])
    assert package_data['name'] == 'generated-project'
    assert 'vite' in package_data['devDependencies']

def test_webcontainer_service_create_project():
    """测试项目创建功能"""
    service = WebContainerService()

    # 创建临时会话和版本
    session_id = 'test_session'
    version = 1

    # 模拟 HTML
    html = '<h1>Test</h1>'

    # 创建项目
    result = service.create_project(session_id, version)

    assert result['status'] == 'created'
    assert 'project_path' in result
    assert len(result['files']) == 4

    # 检查项目目录是否存在
    project_dir = Path(result['project_path'])
    assert project_dir.exists()

    # 检查文件是否存在
    for file in result['files']:
        file_path = project_dir / file
        assert file_path.exists()

def test_webcontainer_service_get_project_status():
    """测试项目状态获取"""
    service = WebContainerService()

    session_id = 'test_session_status'
    version = 1

    # 创建项目
    service.create_project(session_id, version)

    # 获取状态
    status = service.get_project_status(session_id, version)

    assert status['status'] == 'created'
    assert status['project_path']
    assert len(status['existing_files']) == 4
    assert len(status['missing_files']) == 0
    assert status['has_node_modules'] == False

def test_webcontainer_api_create_project():
    """测试创建项目 API"""
    response = client.post(
        "/api/webcontainer/projects",
        params={"session_id": "test_api", "version": 1}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert "project_path" in data
    assert len(data["files"]) == 4

def test_webcontainer_api_get_status():
    """测试获取项目状态 API"""
    # 先创建项目
    client.post(
        "/api/webcontainer/projects",
        params={"session_id": "test_status_api", "version": 1}
    )

    # 获取状态
    response = client.get(
        "/api/webcontainer/projects/test_status_api/1/status"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert len(data["existing_files"]) == 4

def test_webcontainer_api_get_files():
    """测试获取项目文件 API"""
    # 先创建项目
    client.post(
        "/api/webcontainer/projects",
        params={"session_id": "test_files_api", "version": 1}
    )

    # 获取文件
    response = client.get(
        "/api/webcontainer/projects/test_files_api/1/files"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["project_path"]
    assert len(data["files"]) == 4

    # 检查文件内容
    files = data["files"]
    assert "index.html" in files
    assert "package.json" in files
    assert "src/style.css" in files
    assert "src/main.js" in files

def test_webcontainer_api_cleanup():
    """测试清理项目 API"""
    # 先创建项目
    client.post(
        "/api/webcontainer/projects",
        params={"session_id": "test_cleanup_api", "version": 1}
    )

    # 清理项目
    response = client.delete(
        "/api/webcontainer/projects/test_cleanup_api/1"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_webcontainer_api_cleanup_session():
    """测试清理会话 API"""
    # 先创建项目
    client.post(
        "/api/webcontainer/projects",
        params={"session_id": "test_session_cleanup", "version": 1}
    )

    # 清理会话
    response = client.delete(
        "/api/webcontainer/projects/test_session_cleanup"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

def test_webcontainer_api_preview_info():
    """测试预览信息 API"""
    # 先创建项目
    client.post(
        "/api/webcontainer/projects",
        params={"session_id": "test_preview_api", "version": 1}
    )

    # 获取预览信息
    response = client.get(
        "/api/webcontainer/projects/test_preview_api/1/preview"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_preview_api"
    assert data["version"] == 1
    assert data["status"] == "created"
    assert data["files_count"] == 4

def test_webcontainer_service_cleanup_session():
    """测试会话清理功能"""
    service = WebContainerService()

    session_id = 'test_session_cleanup_service'

    # 创建多个版本
    service.create_project(session_id, 1)
    service.create_project(session_id, 2)

    # 清理会话
    result = service.cleanup_session(session_id)

    assert result['status'] == 'success'
    assert result['message'] == '会话清理完成'

def test_webcontainer_service_error_handling():
    """测试错误处理"""
    service = WebContainerService()

    # 测试不存在的项目
    status = service.get_project_status('nonexistent', 999)
    assert status['status'] == 'not_found'

    # 测试清理不存在的项目
    result = service.cleanup_project('nonexistent', 999)
    assert result['status'] == 'not_found'

def test_webcontainer_html_without_styles_or_scripts():
    """测试没有样式和脚本的 HTML"""
    service = WebContainerService()

    html = '<h1>Simple HTML</h1>'
    files = service._parse_html_to_project(html)

    # 应该仍然创建所有必要的文件
    assert len(files) == 4
    assert 'Simple HTML' in files['index.html']
    assert files['src/style.css'] == '/* No styles */'
    assert files['src/main.js'] == '// No scripts'

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])