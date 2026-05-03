from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.template_service import template_service

router = APIRouter()

# 请求/响应模型
class ApplyTemplateRequest(BaseModel):
    """应用模板请求"""
    template_id: str

class ApplyTemplateResponse(BaseModel):
    """应用模板响应"""
    success: bool
    template_id: str
    template_name: str
    version: int

# API端点
@router.get("/templates")
async def get_templates(category: Optional[str] = None):
    """获取模板列表

    Args:
        category: 模板类别筛选 (ecommerce, dashboard, visualization, etc.)
    """
    return template_service.get_template_list(category)

@router.get("/templates/categories")
async def get_template_categories():
    """获取模板类别"""
    return template_service.get_categories()

@router.get("/templates/{template_id}")
async def get_template_detail(template_id: str):
    """获取模板详情"""
    return template_service.get_template_detail(template_id)

@router.post("/sessions/{session_id}/templates", response_model=ApplyTemplateResponse)
async def apply_template(session_id: str, request: ApplyTemplateRequest):
    """应用模板到指定会话"""
    result = template_service.apply_template(session_id, request.template_id)
    return ApplyTemplateResponse(**result)

@router.get("/sessions/{session_id}/templates/preview/{template_id}")
async def preview_template(session_id: str, template_id: str):
    """预览模板效果（不保存）"""
    template_detail = template_service.get_template_detail(template_id)

    # 生成预览用的HTML内容
    preview_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{template_detail['name']} - 预览</title>
    <style>
        :root {{
{chr(10).join(f'            {key}: {value};' for key, value in template_detail['css_variables'].items())}
        }}

        body {{
            font-family: {template_detail['typography']['body_font']};
            font-size: {template_detail['typography']['base_size']};
            color: var(--color-text-primary);
            background-color: var(--color-background);
            margin: 0;
            padding: 20px;
        }}

        .preview-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .color-palette {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}

        .color-swatch {{
            width: 60px;
            height: 60px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}

        .component-demo {{
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }}

        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: {template_detail['components']['button_radius']};
            cursor: pointer;
            margin: 5px;
        }}

        .btn-primary {{
            background-color: var(--color-primary);
            color: white;
        }}

        .btn-secondary {{
            background-color: var(--color-secondary);
            color: white;
        }}

        .card {{
            padding: 20px;
            border-radius: {template_detail['components']['card_radius']};
            background-color: var(--color-surface);
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <h1>{template_detail['name']}</h1>
        <p>{template_detail['description']}</p>

        <h2>颜色调色板</h2>
        <div class="color-palette">
            <div class="color-swatch" style="background-color: {template_detail['color_scheme']['primary']};">主色</div>
            <div class="color-swatch" style="background-color: {template_detail['color_scheme']['secondary']};">次色</div>
            <div class="color-swatch" style="background-color: {template_detail['color_scheme']['accent']};">强调色</div>
            <div class="color-swatch" style="background-color: {template_detail['color_scheme']['success']};">成功</div>
            <div class="color-swatch" style="background-color: {template_detail['color_scheme']['warning']};">警告</div>
            <div class="color-swatch" style="background-color: {template_detail['color_scheme']['error']};">错误</div>
        </div>

        <h2>组件示例</h2>
        <div class="component-demo">
            <h3>按钮组件</h3>
            <button class="btn btn-primary">主要按钮</button>
            <button class="btn btn-secondary">次要按钮</button>
        </div>

        <div class="card">
            <h3>卡片组件</h3>
            <p>这是一个使用当前模板样式的卡片组件示例。</p>
        </div>

        <h2>排版示例</h2>
        <h1>一级标题</h1>
        <h2>二级标题</h2>
        <h3>三级标题</h3>
        <p>正文文本示例，展示当前的字体和颜色设置。</p>
        <code>代码字体示例</code>
    </div>
</body>
</html>
"""

    return {"preview_html": preview_html}